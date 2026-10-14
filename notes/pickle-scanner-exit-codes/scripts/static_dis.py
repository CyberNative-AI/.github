"""Static, no-loader check: decompress each PoC and list opcodes + GLOBAL/STACK_GLOBAL strings + literals. Never unpickles."""
import sys, io, json, tarfile, gzip, bz2, lzma, zlib, pickletools
from pathlib import Path
def dec(b):
    for n,f in [("gzip",gzip.decompress),("bz2",bz2.decompress),("lzma/xz",lzma.decompress),("zlib",zlib.decompress)]:
        try: return n,f(b)
        except Exception: pass
    try:
        import lz4.frame
        return "lz4.frame",lz4.frame.decompress(b)
    except Exception: pass
    return "raw",b
out={}
for p in sorted(Path(sys.argv[1]).iterdir()):
    b=p.read_bytes(); streams={}
    if p.suffix==".tar":
        t=tarfile.open(p); streams={m.name:("tar-member",t.extractfile(m).read()) for m in t.getmembers() if m.isfile()}
    else: streams={p.name:dec(b)}
    r={}
    for k,(how,s) in streams.items():
        ops=[]
        try:
            for op,arg,pos in pickletools.genops(s): ops.append((op.name,arg if not isinstance(arg,(bytes,bytearray)) else arg.hex()))
        except Exception as e: ops.append(("ERR",repr(e)))
        r[k]={"decoder":how,"len":len(s),"ops":[(n,str(a)[:80]) for n,a in ops]}
    out[p.name]=r
json.dump(out,open(sys.argv[2],"w"),indent=1)
for n,r in out.items():
    for k,v in r.items(): print(n,k,v["decoder"],v["len"],[(o,a) for o,a in v["ops"] if o in("GLOBAL","STACK_GLOBAL","UNICODE","SHORT_BINUNICODE","BINUNICODE","STRING","SHORT_BINSTRING","INT","BININT1","ERR","EXT1","EXT2","EXT4")])
