# 40M rows, two columns: a random int64 key and a float. ~620 MB of Parquet.
import sys
import numpy as np
import polars as pl

n = 40_000_000
rng = np.random.default_rng(0)
pl.DataFrame({"k": rng.integers(0, 2**62, n), "v": rng.random(n)}).write_parquet(
    sys.argv[1], row_group_size=1_000_000
)
