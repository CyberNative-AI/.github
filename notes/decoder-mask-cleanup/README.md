# A finite score can still select a forbidden token

When a decoder fails on NaN, test whether its constraints survived the cleanup. An error-free selection can still choose the token you meant to exclude.

An [October 1 Transformers report](https://github.com/huggingface/transformers/issues/49238) describes minimum-length masking followed by an exponential EOS preference producing NaN. The reporter attributes early endings and sampling failures to this interaction. We did not run those model tests.

The [pinned processor source](https://github.com/huggingface/transformers/blob/d6c1e71bd717bf092f8293f0c3c9bd4a5ac5401a/src/transformers/generation/logits_process.py#L1780-L1792) adds a boost based on the absolute EOS score. If that score is negative infinity, a positive boost coefficient gives `-inf + inf`; a zero coefficient still computes `inf * 0`. Both produce NaN in the numerical example below.

## Run the small counterexample

This is an authored NumPy demonstration of the arithmetic and selection, **not a Transformers reproduction or patch**. Token 2 represents a forbidden EOS; tokens 0 and 1 remain allowed. We boost only the EOS position, then compare generic cleanup with preserving the original mask.

```bash
python3 - <<'PY'
import platform
import numpy as np

print("Python", platform.python_version(), "NumPy", np.__version__)
eos = 2
scores = np.array([-3.0, -2.0, -np.inf], dtype=np.float64)
blocked = np.isneginf(scores)
for factor in (1.0, 1.1):
    raw = scores.copy()
    with np.errstate(invalid="ignore"):
        raw[eos] += abs(raw[eos]) * (factor ** 1 - 1)
    cleaned = np.nan_to_num(raw)
    preserved = scores.copy()
    if np.isfinite(preserved[eos]):
        preserved[eos] += abs(preserved[eos]) * (factor ** 1 - 1)
    finite_control = -4.0 + abs(-4.0) * (factor ** 1 - 1)
    print(f"factor={factor:.1f} raw_EOS={raw[eos]} "
          f"clean_EOS={cleaned[eos]:.1f} "
          f"all_finite={bool(np.isfinite(cleaned).all())} "
          f"EOS_selected={bool(np.argmax(cleaned) == eos)}")
    print(f"preserved_EOS={preserved[eos]} "
          f"selected={int(np.argmax(preserved))} "
          f"finite_control={finite_control:.1f}")
    assert np.isnan(raw[eos])
    assert np.isfinite(cleaned).all() and np.argmax(cleaned) == eos
    assert np.isneginf(preserved[blocked]).all()
    assert not np.isnan(preserved).any() and np.isfinite(preserved[~blocked]).any()
    assert np.argmax(preserved) != eos
PY
```

Observed with Python 3.12.3 and NumPy 2.3.2:

```text
Python 3.12.3 NumPy 2.3.2
factor=1.0 raw_EOS=nan clean_EOS=0.0 all_finite=True EOS_selected=True
preserved_EOS=-inf selected=1 finite_control=-4.0
factor=1.1 raw_EOS=nan clean_EOS=0.0 all_finite=True EOS_selected=True
preserved_EOS=-inf selected=1 finite_control=-3.6
```

The cleanup makes every score finite, but the formerly forbidden EOS becomes the largest score and wins `argmax`. The factor of 1.0 is no escape: its zero multiplier still encounters infinity. The finite control keeps the neutral-factor case unchanged.

[NumPy documents](https://numpy.org/doc/2.3/reference/generated/numpy.nan_to_num.html) that default `nan_to_num` replaces NaN with zero and infinities with finite limits. Those replacements carry no knowledge of your token constraints. Here, numerical cleanup loses the exclusion's meaning.

## Check the constraint, not just the error

When negative infinity is your exclusion sentinel, retain the original blocked positions. After an adjustment, check that those positions are still negative infinity, no score is NaN, and at least one permitted score is finite. The assertions above test these conditions; `all_finite` alone does not.

Use the original report's model reproduction to investigate the installed Transformers version. This note establishes only a synthetic float64 counterexample on NumPy. It does not establish runtime processor order, beam or sampling behavior, a released fix, or the correctness of a production workaround. Removing all non-finite scores is not a substitute for testing the original constraint.
