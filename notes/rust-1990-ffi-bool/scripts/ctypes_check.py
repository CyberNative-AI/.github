# Usage: python3 scripts/ctypes_check.py path/to/libflagcheck.so
import ctypes, sys
lib = ctypes.CDLL(sys.argv[1])
calls = [("is_flag_set", ctypes.c_uint8, 0x10), ("is_odd", ctypes.c_uint32, 16), ("is_even", ctypes.c_uint32, 3)]
print("restype = c_bool")
for name, argtype, arg in calls:
    f = getattr(lib, name); f.restype = ctypes.c_bool; f.argtypes = [argtype]
    r = f(arg); print(f"  {name}({arg:#x}) -> {r!r}  {'WRONG' if r else 'ok'}")
print("restype = c_uint8, then test bit 0")
for name, argtype, arg in calls + [("is_odd", ctypes.c_uint32, 17)]:
    f = getattr(lib, name); f.restype = ctypes.c_uint8; f.argtypes = [argtype]
    r = f(arg); print(f"  {name}({arg:#x}) -> raw {r:#04x}, bool(raw & 1) = {bool(r & 1)}")
