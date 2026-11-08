# World size 2 on one GPU (torch >= 2.9 skips the all-gather at world size 1): fake process group + a loopback
# all-gather that writes rank 0's bytes into rank 1's slot. Every weight has byte-identical halves, so these are the
# bytes a real 2-GPU all-gather delivers. Usage: python issue_repro.py bfloat16|uint8|uint8-sharded
# uint8-sharded = uint8 storage with the #3987 exclusion removed (Params4bit dropped from ignored_params), i.e. the
# proposed change, emulated by wrapping fully_shard; no accelerate file is modified.
import os, sys, torch, torch.distributed as dist
from torch.testing._internal.distributed.fake_pg import FakeStore
from torch.distributed.fsdp import FSDPModule
from torch.distributed.fsdp._fully_shard._fsdp_collectives import AllGather, DefaultAllocMixin
from torch.distributed.tensor import DTensor
import bitsandbytes as bnb
from transformers import AutoModelForCausalLM, BitsAndBytesConfig, LlamaConfig, LlamaForCausalLM
from peft import LoraConfig, get_peft_model
from accelerate import Accelerator, FullyShardedDataParallelPlugin

os.environ.update(RANK="0", LOCAL_RANK="0", WORLD_SIZE="2", LOCAL_WORLD_SIZE="2", MASTER_ADDR="127.0.0.1",
                  MASTER_PORT="29500", ACCELERATE_USE_FSDP="true", FSDP_VERSION="2")
dist.init_process_group("fake", store=FakeStore(), rank=0, world_size=2)
torch.cuda.set_device(0)
mode = sys.argv[1]
if mode == "uint8-sharded":
    import torch.distributed.fsdp as fsdp_pkg
    real_fully_shard = fsdp_pkg.fully_shard

    def fully_shard(module, **kw):  # accelerate imports fully_shard at call time
        ig = {p for p in (kw.get("ignored_params") or ()) if type(p).__name__ != "Params4bit"}
        kw["ignored_params"] = ig or None
        return real_fully_shard(module, **kw)

    fsdp_pkg.fully_shard = fully_shard


class Loopback(DefaultAllocMixin, AllGather):
    def __call__(self, output_tensor, input_tensor, group, async_op=False):
        output_tensor.view(torch.uint8).view(2, -1)[1].copy_(input_tensor.view(torch.uint8).view(-1))


def dup_halves(params):
    with torch.no_grad():
        for p in params:
            if p.dim() == 2:
                p[p.shape[0] // 2:] = p[: p.shape[0] // 2].clone()


torch.manual_seed(0)
cfg = LlamaConfig(vocab_size=256, hidden_size=512, intermediate_size=1024, num_hidden_layers=2,
                  num_attention_heads=8, num_key_value_heads=8, tie_word_embeddings=False)
tiny = LlamaForCausalLM(cfg).to(torch.bfloat16)
dup_halves(tiny.parameters())
tiny.save_pretrained("/tmp/tiny-llama")
q = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
                       bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_quant_storage=getattr(torch, mode.split("-")[0]))
model = AutoModelForCausalLM.from_pretrained("/tmp/tiny-llama", quantization_config=q, dtype=torch.bfloat16,
                                             device_map={"": 0})
model = get_peft_model(model, LoraConfig(r=16, lora_alpha=32, lora_dropout=0.0, target_modules="all-linear"))
dup_halves(p for n, p in model.named_parameters() if "lora_A" in n)

acc = Accelerator(mixed_precision="bf16", fsdp_plugin=FullyShardedDataParallelPlugin(
    fsdp_version=2, auto_wrap_policy="transformer_based_wrap", transformer_cls_names_to_wrap=["LlamaDecoderLayer"]))
ids = torch.randint(0, 256, (2, 32), device="cuda")
lin = {n: m for n, m in model.named_modules() if isinstance(m, bnb.nn.Linear4bit)}
before = {n: m.weight.data.clone() for n, m in lin.items()}
with torch.no_grad(), acc.autocast():
    y_ref = model(input_ids=ids).logits.float()

opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
model, opt = acc.prepare(model, opt)  # FSDP2 prepare needs the optimizer too
for unit in model.modules():
    if isinstance(unit, FSDPModule):
        unit.set_custom_all_gather(Loopback())
seen = {}


def capture(name):  # the packed bytes each Linear4bit sees after the all-gather
    def hook(mod, args):
        seen[name] = mod.weight.detach().clone()
    return hook


for n, m in lin.items():
    m.register_forward_pre_hook(capture(n))
with torch.no_grad(), acc.autocast():
    y = model(input_ids=ids).logits.float()

changed = sum(int((seen[n].flatten().view(torch.uint8) != before[n].flatten().view(torch.uint8)).sum()) for n in lin)
sharded = sum(isinstance(m.weight, DTensor) for m in lin.values())
print(f"{mode} storage: {sharded}/{len(lin)} Linear4bit sharded, {changed} packed bytes changed, "
      f"logits max |diff| vs before prepare = {(y - y_ref).abs().max().item():.4f}")
dist.destroy_process_group()
