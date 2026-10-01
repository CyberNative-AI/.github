"""Internal native-pandas recipe probe, never a production data transformer.

Deterministic arithmetic fixtures; no files, customer data, network or writes.
Run with pandas 3.0.6 and NumPy 2.3.2. See README.md for limits and sources.
"""

import json
import platform
import time

import numpy as np
import pandas as pd


def exact_text(frame):
    """Only this fixture's exact integer/text keys are supported."""
    keys = frame[["group", "key"]]
    if keys.isna().any().any():
        raise ValueError("missing key: resolve at source before joining")
    if any(pd.api.types.is_float_dtype(keys[col]) for col in keys):
        raise ValueError("float key: reload an exact source; casting cannot restore bits")
    result = frame.copy()
    result["key"] = result["key"].astype("string")
    return result


def checked_join(left, right):
    """Native join plus this probe's explicit all-left-rows-must-match contract."""
    left, right = exact_text(left), exact_text(right)
    result = left.merge(right, on=["group", "key"], how="left",
                        validate="one_to_one", indicator=True)
    if len(result) != len(left) or not result["_merge"].eq("both").all():
        raise ValueError("unmatched or expanded rows: inspect exact keys before output")
    return result


def main():
    started = time.perf_counter()
    keys = [2**60 + offset for offset in (1, 2, 3)]
    left = pd.DataFrame({"group": [7] * 3,
                         "key": np.array(keys, dtype="int64"),
                         "left_value": [10, 20, 30]})
    right = pd.DataFrame({"group": [7] * 3,
                          "key": np.array(keys, dtype="uint64"),
                          "right_value": [100, 200, 300]})
    baseline = left.merge(right, on=["group", "key"], how="left",
                          validate="one_to_one", indicator=True)
    baseline_pairs = list(zip(baseline.left_value, baseline.right_value))
    expected_pairs = [(10, 100), (20, 200), (30, 300)]
    baseline_correct = len(baseline) == 3 and baseline_pairs == expected_pairs

    # Range is known for this fixture. Never cast arbitrary uint64 to int64.
    signed_right = right.copy()
    signed_right["key"] = signed_right["key"].astype("int64")
    signed = left.merge(signed_right, on=["group", "key"], how="left",
                        validate="one_to_one", indicator=True)
    assert list(zip(signed.left_value, signed.right_value)) == expected_pairs
    assert signed.key.tolist() == keys

    text = checked_join(left, right)
    assert list(zip(text.left_value, text.right_value)) == expected_pairs
    assert text.key.tolist() == [str(k) for k in keys]
    assert checked_join(left, right).equals(text)

    results = [{"case": "mixed_integer_baseline", "rows": len(baseline),
                "validation_raised": False, "correct": baseline_correct,
                "pairs": baseline_pairs},
               {"case": "common_signed_integer", "rows": len(signed),
                "correct": True, "pairs": expected_pairs},
               {"case": "exact_text", "rows": len(text), "correct": True,
                "keys": text.key.tolist(), "pairs": expected_pairs}]

    bad_inputs = []
    duplicate = pd.concat([right, right.iloc[[0]]], ignore_index=True)
    bad_inputs.append(("duplicate_right", left, duplicate, pd.errors.MergeError))
    missing = right.iloc[:2].copy()
    bad_inputs.append(("unmatched_left", left, missing, ValueError))
    null = right.copy()
    null["key"] = null["key"].astype("UInt64")
    null.loc[0, "key"] = pd.NA
    bad_inputs.append(("null_key", left, null, ValueError))
    rounded = left.copy()
    rounded["key"] = rounded["key"].astype("float64")
    bad_inputs.append(("already_float_key", rounded, right, ValueError))
    padded_left = pd.DataFrame({"group": [7], "key": ["001"], "left_value": [10]})
    unpadded_right = pd.DataFrame({"group": [7], "key": ["1"], "right_value": [100]})
    bad_inputs.append(("leading_zero_difference", padded_left, unpadded_right, ValueError))
    for name, bad_left, bad_right, error in bad_inputs:
        try:
            checked_join(bad_left, bad_right)
        except error as exc:
            results.append({"case": name, "rejected": True,
                            "error_type": type(exc).__name__, "reason": str(exc)})
        else:
            raise AssertionError(f"{name} was not rejected")

    # Exact text also supports keys outside signed-int64 range in this fixture.
    large_left = pd.DataFrame({"group": [7], "key": [str(2**63 + 1)], "left_value": [10]})
    large_right = pd.DataFrame({"group": [7],
                               "key": np.array([2**63 + 1], dtype="uint64"),
                               "right_value": [100]})
    large = checked_join(large_left, large_right)
    assert large.key.tolist() == [str(2**63 + 1)]
    assert large.right_value.tolist() == [100]
    results.append({"case": "above_signed_int64", "rows": len(large), "correct": True})

    print(json.dumps({"kind": "internal_arithmetic_fixture_probe",
                      "python": platform.python_version(),
                      "pandas": pd.__version__, "numpy": np.__version__,
                      "elapsed_seconds": round(time.perf_counter() - started, 6),
                      "cases": results,
                      "limits": "No customer run, production write, upstream fix or demand evidence."},
                     indent=2))


if __name__ == "__main__":
    main()
