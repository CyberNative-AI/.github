"""One documented use of a package, run under the current lazy-imports mode.

    python -X lazy_imports=all check.py CASE      # or normal
    LAZY_EAGER=httpcore python -X lazy_imports=all check.py httpx

Prints one line: "OK <result>" or "EXC <type>: <message> || ROOT <type>: <message>".
LAZY_EAGER (comma-separated names) installs a filter that keeps an import eager when the
importing module or the imported module is one of those names or below them.
"""
import os
import sys
import tempfile

EAGER = [n for n in os.environ.get("LAZY_EAGER", "").split(",") if n]

if EAGER:
    def _under(mod):
        return bool(mod) and any(mod == p or mod.startswith(p + ".") for p in EAGER)

    def _lazy_ok(importer, name, fromlist):
        return not (_under(importer) or _under(name))

    sys.set_lazy_imports_filter(_lazy_ok)


def run(case):
    if case == "sympy":
        import sympy
        return sympy.integrate(sympy.Symbol("x") ** 2)
    if case == "mpmath":
        import mpmath
        mpmath.mp.dps = 30
        return mpmath.pi
    if case == "httpx":
        import httpx
        try:
            httpx.Client().get("http://127.0.0.1:9/")
        except httpx.ConnectError:
            return "ConnectError (expected: nothing listens on port 9)"
    if case == "openai":
        import openai
        return type(openai.OpenAI(api_key="sk-test")).__name__
    if case == "anthropic":
        import anthropic
        return type(anthropic.Anthropic(api_key="sk-test")).__name__
    if case == "truststore":
        import truststore
        truststore.inject_into_ssl()
        return "injected"
    if case == "sqlalchemy":
        from sqlalchemy import Column, Integer, MetaData, Table, create_engine
        md = MetaData()
        Table("t", md, Column("id", Integer, primary_key=True))
        md.create_all(create_engine("sqlite://"))
        return "created"
    if case == "alembic":
        from alembic.migration import MigrationContext
        from sqlalchemy import create_engine
        return MigrationContext.configure(create_engine("sqlite://").connect()).get_current_revision()
    if case == "pandas":
        import pandas as pd
        return pd.DataFrame({"a": [1, 2]}).sum().to_dict()
    if case == "matplotlib":
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots()
        ax.plot([1, 2, 3])
        ax.legend(["a"])
        fig.savefig(os.path.join(tempfile.mkdtemp(), "x.png"))
        return "saved"
    if case == "otel":
        from opentelemetry.sdk.metrics import MeterProvider
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader
        reader = InMemoryMetricReader()
        MeterProvider(metric_readers=[reader]).get_meter("x").create_counter("c").add(1)
        return reader.get_metrics_data() is not None
    if case == "protobuf":
        from google.rpc import status_pb2
        return repr(status_pb2.Status(code=3, message="x"))
    if case == "rapidfuzz":
        from rapidfuzz.distance import Editop
        return Editop("replace", 0, 0)
    if case == "uvicorn":
        from uvicorn.supervisors import ChangeReload
        return "ChangeReload = " + ChangeReload.__name__
    raise SystemExit("unknown case " + case)


try:
    line = "OK " + str(run(sys.argv[1]))
except Exception as e:
    root = e
    while root.__cause__ or root.__context__:
        root = root.__cause__ or root.__context__
    line = f"EXC {type(e).__name__}: {str(e)[:120]} || ROOT {type(root).__name__}: {str(root)[:120]}"
print(line.replace("\n", " "), flush=True)
os._exit(0)  # skip interpreter teardown: some clients print __del__ errors after a failed init
