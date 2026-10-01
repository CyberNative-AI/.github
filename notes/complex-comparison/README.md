# Your complex array's `<` is not a magnitude comparison

A Boolean mask can run successfully and still select the wrong samples for your question. Before filtering complex data, make the quantity you intend to compare explicit.

An [October 1 pandas report](https://github.com/pandas-dev/pandas/issues/70087) shows a complex Series accepting `<` where a Python complex scalar raises `TypeError`. A [maintainer response](https://github.com/pandas-dev/pandas/issues/70087#issuecomment-5940846801) favors deprecation. The linked [open PR](https://github.com/pandas-dev/pandas/pull/69862) concerns complex reductions; it does not establish a shipped fix for this comparison.

Here is a small NumPy check you can run in an environment that already has NumPy. It reads no files and changes no data outside its own arrays:

```sh
python3 - <<'PY'
import platform
import numpy as np

z = np.array([1+1j, 1+2j, 2+0j, 0+3j], dtype=np.complex128)
threshold = 1+2j
print("Python", platform.python_version(), "NumPy", np.__version__)
print("dtype:", z.dtype)
print("direct:", (z < threshold).tolist())
print("magnitude:", (np.abs(z) < abs(threshold)).tolist())
print("real part:", (z.real < threshold.real).tolist())
try:
    print("Python scalar:", (1+1j) < threshold)
except TypeError as error:
    print("Python scalar:", type(error).__name__)
PY
```

Observed on October 1, 2026, with Python 3.12.3 and NumPy 2.3.2:

```text
Python 3.12.3 NumPy 2.3.2
dtype: complex128
direct: [True, False, False, True]
magnitude: [True, False, True, False]
real part: [False, False, False, True]
Python scalar: TypeError
```

The last two samples switch membership between the direct and magnitude masks. `2+0j` has smaller magnitude than `1+2j`, yet the direct comparison excludes it. `0+3j` has larger magnitude, yet the direct comparison includes it.

[NumPy documents a real-part-first, imaginary-part-tiebreak ordering for sorting complex values](https://numpy.org/doc/2.3/reference/generated/numpy.sort.html). The direct mask above is consistent with that convention; this is a measured result for this array and version, not a promise about every backend. [Python's scalar ordering rules](https://docs.python.org/3.12/library/stdtypes.html#comparisons) reject ordered complex comparisons.

If the question is amplitude, compare magnitudes explicitly. If it is a real-component threshold, compare `.real`. If it is phase, define the angle convention and boundary handling separately. These operations answer different questions; converting to real data just to silence an error discards information.

This check uses four finite `complex128` values. It does not test pandas, object arrays, missing values, other dtypes, accelerators or future releases. It is an inspection recipe, not a pandas patch or a general numerical-validation suite.
