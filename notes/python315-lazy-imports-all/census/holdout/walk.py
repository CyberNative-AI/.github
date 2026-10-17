"""Import the named top-level modules, then force-reify every module attribute.

Run as: python -X lazy_imports=<mode> -W ignore walk.py NAME [NAME...]
Prints one JSON object on stdout. Never imports anything from cwd (run with -I-like cwd).
"""
import importlib
import json
import sys
import time
import traceback
import warnings

warnings.simplefilter("ignore")
WALK_SECONDS = 60.0


def origin(exc):
    frames = traceback.extract_tb(exc.__traceback__)
    deepest = frames[-1].filename if frames else ""
    sp = ""
    for fr in frames:
        if "site-packages" in fr.filename or "/ctl/" in fr.filename:
            sp = fr.filename
    return {"deepest": deepest, "deepest_site_packages": sp}


def describe(exc):
    d = {"type": type(exc).__name__, "msg": str(exc)[:300]}
    d.update(origin(exc))
    return d


def install_deny_filter():
    """Arm F: keep imports eager when the importer or the imported module is under a denied prefix."""
    import os
    prefixes = [x for x in os.environ.get("LAZY_DENY", "").split(",") if x]
    pb2 = False
    if os.environ.get("LAZY_DENY_FILE"):  # amendment 01 (experiment B): ecosystem denylist
        spec = json.load(open(os.environ["LAZY_DENY_FILE"], encoding="utf-8"))
        prefixes += spec["prefixes"]
        pb2 = bool(spec.get("pb2_pattern"))
    if not prefixes:
        return None

    def under(mod):
        return bool(mod) and any(mod == p or mod.startswith(p + ".") for p in prefixes)

    def is_pb2(mod):
        return pb2 and bool(mod) and mod.rsplit(".", 1)[-1].endswith(("_pb2", "_pb2_grpc"))

    def allow(importer, name, fromlist):
        return not (under(importer) or under(name) or is_pb2(importer) or is_pb2(name))

    sys.set_lazy_imports_filter(allow)
    return prefixes


def main():
    names = sys.argv[1:]
    deny = install_deny_filter()
    try:
        mode = sys.get_lazy_imports()
    except Exception as e:  # pragma: no cover
        mode = "unavailable:" + type(e).__name__
    base = set(sys.modules)
    out = {"mode": str(mode), "version": sys.version.split()[0], "imports": {}, "walk_errors": [],
           "walk_complete": None, "walked": 0, "deny": deny}
    for n in names:
        try:
            importlib.import_module(n)
            out["imports"][n] = {"ok": True}
        except BaseException as e:  # noqa: BLE001 - record everything, incl. SystemExit
            out["imports"][n] = {"ok": False, **describe(e)}
    walked = set()
    deadline = time.monotonic() + WALK_SECONDS
    complete = True
    changed = True
    while changed:
        changed = False
        for modname, mod in sorted(list(sys.modules.items()), key=lambda kv: kv[0]):
            if modname in base or modname in walked:
                continue
            if time.monotonic() > deadline:
                complete = False
                changed = False
                break
            walked.add(modname)
            changed = True
            if mod is None:
                continue
            try:
                keys = sorted(k for k in list(mod.__dict__.keys()) if isinstance(k, str))
            except BaseException:  # noqa: BLE001
                continue
            for k in keys:
                try:
                    getattr(mod, k)
                except BaseException as e:  # noqa: BLE001
                    out["walk_errors"].append({"module": modname, "attr": k, **describe(e)})
    out["walk_complete"] = complete
    out["walked"] = len(walked)
    out["modules_after"] = sorted(m for m in sys.modules if m not in base)
    sys.stdout.write(json.dumps(out, sort_keys=True) + "\n")
    sys.stdout.flush()


main()
