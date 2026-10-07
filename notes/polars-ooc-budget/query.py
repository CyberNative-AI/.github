# The measured query: a lazy sort written straight to Parquet.
import sys
import time
import polars as pl

t = time.time()
pl.scan_parquet(sys.argv[1]).sort("k").sink_parquet(sys.argv[2])
print(f"completed in {time.time() - t:.1f} s")
