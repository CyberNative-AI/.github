import json,struct,sys,urllib.request,urllib.error,time
B="https://ecmwf-forecasts.s3.eu-central-1.amazonaws.com/"
def get(url,rng=None):
    r=urllib.request.Request(url, headers={"Range":f"bytes={rng[0]}-{rng[1]}"} if rng else {})
    import time
    for k in range(6):
        try: return urllib.request.urlopen(r,timeout=60).read()
        except urllib.error.HTTPError as e:
            if e.code!=503: raise
            time.sleep(3*(k+1))
    raise SystemExit("503 x6")
def sec5(msg):
    i=16
    while i<len(msg)-4:
        L=struct.unpack('>I',msg[i:i+4])[0]; n=msg[i+4]
        if n==5:
            s=msg[i:i+L]; npts=struct.unpack('>I',s[5:9])[0]; tmpl=struct.unpack('>H',s[9:11])[0]
            R=struct.unpack('>f',s[11:15])[0]
            def sg(b): v=struct.unpack('>H',b)[0]; return -(v&0x7fff) if v&0x8000 else v
            E=sg(s[15:17]); D=sg(s[17:19]); nb=s[19]
            return dict(tmpl=tmpl,R=R,E=E,D=D,nbits=nb,npts=npts)
        i+=L
def run(date,param,steps):
    out=[]
    for st in steps:
        stem=f"{date}/00z/ifs/0p25/oper/{date}000000-{st}h-oper-fc"
        idx=[json.loads(l) for l in get(B+stem+".index").decode().splitlines() if l.strip()]
        m=[x for x in idx if x.get("param")==param]
        if not m: out.append((st,None)); continue
        x=m[0]; msg=get(B+stem+".grib2",(x["_offset"],x["_offset"]+x["_length"]-1))
        s=sec5(msg); s["step_size_mm" if param in("tp","sf") else "step_size"]=(2.0**s["E"])*10**(-s["D"])*(1000 if param in("tp","sf") else 1)
        out.append((st,s)); time.sleep(1)
    return out
date,param=sys.argv[1],sys.argv[2]; steps=[int(a) for a in sys.argv[3].split(",")]
for st,s in run(date,param,steps): print(date,param,st,s)
