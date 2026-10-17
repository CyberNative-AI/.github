"""Run DeepSeek's own encoding tests against DeepSeek-V4.1 chat templates.

    python -m pip install "transformers==5.20.1" "pytest==9.*"
    python run.py

Downloads pinned files from huggingface.co into ./work, then for each template and
encoder revision runs DeepSeek's test_encoding.py with prompts rendered by the template
(see template_encoding.py). Prints passed/failed counts and failing test names.
"""
import os
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"
HF = "https://huggingface.co/deepseek-ai"
FLASH = "DeepSeek-V4.1-Flash"
FLASH_1017 = "DeepSeek-V4.1-Flash-1017"
MERGE_REV = "2cba9e42aa026125f3ed06c6d98c1db82f7ca027"     # "Adding chat template (#68)", 2026-10-01
OCT16_REV = "314113f8a7dadb388215396ba5fbee2c610a04d6"     # encoding fix, 2026-10-16
REV_1017 = "1bae0e1088993b9b82de08f59de5be5a34e42170"      # V4.1-Flash-1017, 2026-10-17
ENC_FILES = ["encoding/encoding.py", "encoding/test_encoding.py"] + [
    f"encoding/tests/test_{k}_{i}.{'json' if k == 'input' else 'txt'}"
    for i in range(1, 6) for k in ("input", "output")]
EXAMPLES = ["inference/examples/example.txt", "inference/examples/example_harmony.json"]


def fetch(repo, rev, path, dest):
    dest.parent.mkdir(parents=True, exist_ok=True)
    if not dest.exists():
        urllib.request.urlretrieve(f"{HF}/{repo}/resolve/{rev}/{path}", dest)
    return dest


def snapshot(name, repo, rev, files):
    root = WORK / name
    for f in files:
        fetch(repo, rev, f, root / f)
    return root


def run_suite(enc_root, template, dict_args):
    suite = WORK / "suite"
    shutil.rmtree(suite, ignore_errors=True)
    shutil.copytree(enc_root / "encoding", suite / "encoding")
    shutil.copytree(enc_root / "inference", suite / "inference")
    enc_dir = suite / "encoding"
    (enc_dir / "encoding.py").rename(enc_dir / "_ref_encoding.py")
    shutil.copy(HERE / "template_encoding.py", enc_dir / "encoding.py")
    env = dict(os.environ, DS_TOKENIZER=str(WORK / "tokenizer"), DS_TEMPLATE=str(template),
               DS_DICT_ARGS="1" if dict_args else "0", TRANSFORMERS_VERBOSITY="error")
    out = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                          "test_encoding.py"], cwd=enc_dir, env=env,
                         capture_output=True, text=True).stdout
    lines = out.strip().splitlines()
    return [l for l in lines if l.startswith("FAILED")], lines[-1] if lines else "no output"


def main():
    tok = WORK / "tokenizer"
    for f in ("tokenizer.json", "tokenizer_config.json"):
        fetch(FLASH_1017, REV_1017, f, tok / f)
    templates = {
        "PR #68 template": fetch(FLASH, MERGE_REV, "chat_template.jinja", WORK / "pr68" / "chat_template.jinja"),
        "synced template": HERE / "chat_template.jinja",
    }
    encoders = {
        "encoder @2cba9e42 (10-01)": snapshot("enc-merge", FLASH, MERGE_REV, ENC_FILES + EXAMPLES),
        "encoder @314113f8 (10-16)": snapshot("enc-oct16", FLASH, OCT16_REV, ENC_FILES + EXAMPLES),
        "1017 encoder @1bae0e10": snapshot("enc-1017", FLASH_1017, REV_1017, ENC_FILES + EXAMPLES),
    }
    same = (encoders["encoder @314113f8 (10-16)"] / "encoding/encoding.py").read_bytes() == \
           (encoders["1017 encoder @1bae0e10"] / "encoding/encoding.py").read_bytes()
    print(f"1017 encoding.py identical to V4.1-Flash @314113f8: {same}")
    for tname, tpath in templates.items():
        for ename, eroot in encoders.items():
            for dict_args in (True, False):
                failed, summary = run_suite(eroot, tpath, dict_args)
                args = "dict args  " if dict_args else "string args"
                print(f"{tname:16s} | {ename:26s} | {args} | {summary}")
                for f in failed:
                    print(f"    {f}")


if __name__ == "__main__":
    main()
