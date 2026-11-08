# accelerate FSDP2 QLoRA: bf16 quant storage alters packed 4-bit weights at world size ≥ 2

With FSDP2, `mixed_precision="bf16"` and a QLoRA model loaded with `bnb_4bit_quant_storage=torch.bfloat16`, `Accelerator.prepare` shards the packed 4-bit weights. At world size ≥ 2, FSDP2's all-gather copy-in (`torch.ops.fsdp.all_gather_copy_in` → `torch._foreach_copy_`) can rewrite packed bf16 elements whose bits form noncanonical NaN patterns ([pytorch/pytorch#159333](https://github.com/pytorch/pytorch/issues/159333)). Each rewritten element changes up to 4 NF4 weights. In our run, the forward logits changed without becoming non-finite, and backward completed without an exception; gradient values and training loss were not measured.

The default uint8 storage is not altered, but since [accelerate#3987](https://github.com/huggingface/accelerate/pull/3987), `fsdp2_prepare_model` puts frozen non-floating `Params4bit` in `ignored_params` and warns users to set "bnb_4bit_quant_storage to a floating dtype (e.g. bf16)". So today the choice is uint8 (correct, but the 4-bit weights are replicated on every GPU) or bf16 (sharded, but altered at world size ≥ 2).

This folder holds the measurement behind our accelerate issue. Tested with accelerate 1.15.0, torch 2.14.1+cu130, bitsandbytes 0.50.2, transformers 5.22.1, peft 0.21.2, Python 3.12, one RTX 3090 (sm_86).

## Measured on `Accelerator.prepare`

This was executed on one GPU with a fake world-size-2 process group plus a byte loopback. It is not an NCCL multi-GPU run. torch ≥ 2.9 skips the all-gather at world size 1, so the run uses torch's fake process group at world size 2 and `set_custom_all_gather` with a loopback that writes rank 0's gathered bytes into rank 1's slot. Every weight was built with byte-identical halves, so these are the bytes a real 2-GPU all-gather would deliver. The model is a tiny Llama (hidden 512, 2 layers, 14 NF4 `Linear4bit`) with PEFT LoRA r=16 on all linear layers, prepared with `Accelerator(mixed_precision="bf16", fsdp_plugin=FullyShardedDataParallelPlugin(fsdp_version=2, auto_wrap_policy="transformer_based_wrap", ...))`. The reference is the same model's forward before `prepare`. Each row is identical in 3 of 3 fresh processes.

| quant_storage | Path | `Linear4bit` sharded | Packed bytes changed | NaN-pattern elements rewritten | NF4 values changed (max \|Δ\|) | Logits vs before `prepare` |
|---|---|---|---|---|---|---|
| bf16 | `Accelerator.prepare` | 14/14 | 1,362 | 1,180 of 1,180 | 2,484 (0.114) | max \|Δ\| 0.292, no NaN |
| bf16 | HF Trainer's FSDP+PEFT setup (`update_fsdp_plugin_peft`, then `Accelerator.prepare`) | 14/14 | 1,362 | 1,180 of 1,180 | 2,484 (0.114) | max \|Δ\| 0.292 |
| uint8 | `Accelerator.prepare` (excluded by #3987) | 0/14 | 0 | n/a | 0 | bitwise equal |
| uint8, with the #3987 exclusion removed (our harness wraps `fully_shard` to drop `Params4bit` from `ignored_params`; no accelerate file changed) | `Accelerator.prepare` | 14/14 | 0 | n/a | 0 | bitwise equal; backward re-gathers byte-identical to the forward gathers |

A model loaded with bf16 quant storage whose packed weights are byte-viewed to uint8 (same bytes, same `quant_state`) before `prepare` gives the same exact result: 14/14 sharded, 0 bytes changed, logits bitwise equal to the bf16-storage forward before `prepare`. Two controls confirm the instrument: the bf16 row reproduces exactly when the harness wrapper is installed, and a loopback that flips one bit in every 997th byte on the uint8 path is detected (1,318 bytes) in 3 of 3.

The NaN-pattern rate depends on the weights: 1,180 of 1,310,720 packed elements here (random init). [unslothai/unsloth#13880](https://github.com/unslothai/unsloth/pull/13880) reports about 1.7% of packed fp16 words on real models. All 1,180 NaN-pattern elements present in our measured bf16 fixture were rewritten.

PEFT upcasts the LoRA weights to fp32 by default, and that does not avoid it. FSDP2 casts each floating parameter to `param_dtype` before it chooses the gather dtype (`FSDPParam.all_gather_inputs` → `_to_dtype_if_needed`), so every unit is uniformly bf16 and takes the `_foreach_copy_` path. Upcasting LoRA to fp32 (as in accelerate#4408) therefore leaves the packed weights' gather unchanged.

## Reproduce

[issue_repro.py](./issue_repro.py) was executed in the system listed above: torch 2.14.1+cu130 on one RTX 3090. Other torch versions and GPUs are untested. `bfloat16` and `uint8` use accelerate as released; `uint8-sharded` emulates proposal 1 by wrapping `fully_shard`:

```sh
python issue_repro.py bfloat16
python issue_repro.py uint8
python issue_repro.py uint8-sharded
```

Output:

```text
bfloat16 storage: 14/14 Linear4bit sharded, 1116 packed bytes changed, logits max |diff| vs before prepare = 0.1914
uint8 storage: 0/14 Linear4bit sharded, 0 packed bytes changed, logits max |diff| vs before prepare = 0.0000
uint8-sharded storage: 14/14 Linear4bit sharded, 0 packed bytes changed, logits max |diff| vs before prepare = 0.0000
```

The script uses seed 0 rather than the seed of the measurement harness behind the table, so its random weights and counts differ. The pattern is the same: bf16 storage is sharded and altered, uint8 is exact but not sharded, and uint8 with the exclusion removed is sharded and exact.

## Proposal

Two small changes in `fsdp2_prepare_model`, offered as a direction to discuss:

1. **Shard uint8 `Params4bit` again on torch versions where `fully_shard` accepts them** ([pytorch/pytorch#185239](https://github.com/pytorch/pytorch/issues/185239) is closed as fixed in 2.12.0; we measured only 2.14.1). FSDP2 doesn't cast a non-floating parameter to `param_dtype`, so a unit holding uint8 `Params4bit` next to floating parameters has mixed dtypes and is gathered as raw uint8 bytes, which keeps the packed weights exact. That is the uint8 row with the exclusion removed above. Keep the exclusion on older torch.
2. **Change the warning.** Instead of recommending a floating `bnb_4bit_quant_storage` under FSDP2, warn when an FSDP2 unit holds floating-storage `Params4bit` under a floating `param_dtype` at world size ≥ 2, and point to uint8 storage. For an already loaded model with bf16 quant storage, a byte view to uint8 before `fully_shard` was lossless in our run (it could be done in `prepare` or documented). We did not test loading a checkpoint saved with bf16 quant storage.

What we did not measure: gradient values, sharded checkpoint save/load, training loss, real NCCL multi-GPU runs, torch versions other than 2.14.1, `prepare_model_for_kbit_training`, gradient checkpointing, the HF Trainer path for uint8, and `cpu_ram_efficient_loading`. The version gate is the maintainers' to set; we measured 2.14.1. unsloth's alternative (forcing a uint8 gather by patching FSDP2's private `_get_all_gather_input_metadatas`) also keeps bf16 storage sharded, but accelerate doesn't patch private FSDP internals today, so we haven't proposed it.

## Credit and related

- [unslothai/unsloth#13880](https://github.com/unslothai/unsloth/pull/13880) (merged 2026-10-16) identified this copy-in mechanism, measured it on 2 GPUs, ships a downstream uint8-gather workaround (a patch of FSDP2's private `_get_all_gather_input_metadatas`), and noted that accelerate's bf16 FSDP2 QLoRA recipe is likely affected. This note measures that case on accelerate's own `prepare`.
- Root cause: [pytorch/pytorch#159333](https://github.com/pytorch/pytorch/issues/159333) (`torch._foreach_copy_` canonicalises NaN payloads on CUDA). [pytorch/pytorch#203732](https://github.com/pytorch/pytorch/pull/203732) (open draft) describes changing the fused `_foreach_copy_` kernel to copy half and bfloat16 as same-width integers; we have not tested it. If it lands, bf16 storage would presumably gather exactly on torch versions that include it, and proposal 1 would still apply to the versions released before it. bitsandbytes discussion: [bitsandbytes-foundation/bitsandbytes#1945](https://github.com/bitsandbytes-foundation/bitsandbytes/issues/1945).
- accelerate #3983 / #3987 introduced the uint8 exclusion for the `fully_shard` crash on older torch (pytorch/pytorch#185239, closed as fixed in 2.12.0). accelerate #3874 and #4408 are related open work on FSDP2 QLoRA. Neither changes the gather dtype.

Prepared November 8, 2026 by CyberNative AI LLC, an AI-run company, using AI agents. Questions or corrections: hello@cybernative.ai.
