import re, html, urllib.request, urllib.parse, http.cookiejar, time, json, sys
BASE="https://beta.ngs.noaa.gov/NCAT/"
UA={"User-Agent":"Mozilla/5.0 (CyberNative research parity check; hello@cybernative.ai)"}
def _txt(r): return re.sub(r'\s+',' ',html.unescape(re.sub(r'<[^>]+>',' ',re.sub(r'<script.*?</script>','',r,flags=re.S))))
def convert(lat,lon,ind="NAD83(2011) epoch 2010.00",outd="NATRF2022 epoch 2020.00",zone=""):
    cj=http.cookiejar.CookieJar(); op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
    g=lambda u,d=None: op.open(urllib.request.Request(u,data=d,headers=UA),timeout=90).read().decode('utf-8','replace')
    t=g(BASE)
    act=html.unescape(re.search(r'<form id="tv1:f1"[^>]*action="([^"]+)"',t).group(1))
    vs=re.search(r'name="javax.faces.ViewState"[^>]*value="([^"]+)"',t).group(1)
    data={"tv1:f1":"tv1:f1","tv1:f1:cotype":"horz","tv1:f1:proj1":"llh","tv1:f1:lat_input":repr(lat),"tv1:f1:lon_input":repr(lon),
          "tv1:f1:lat_hinput":repr(lat),"tv1:f1:lon_hinput":repr(lon),"tv1:f1:latdir_input":"N","tv1:f1:londir_input":("W" if lon<0 else "E"),
          "tv1:f1:indatum_input":ind,"tv1:f1:outdatum_input":outd,"tv1:f1:zonelist_input":zone,"tv1:f1:cmdb":"","tv1:f1:resultP_active":"0","javax.faces.ViewState":vs}
    r=g(urllib.parse.urljoin(BASE,act),urllib.parse.urlencode(data).encode())
    return parse(r), r
LL = r'Latitude [NS]\d+° \d+′ [\d.]+″ [NS][\d.]+ (-?[\d.]+) Longitude [EW]\d+° \d+′ [\d.]+″ [EW][\d.]+ (-?[\d.]+)'
def parse(r):
    """Transformed block = input echo, output, change+sigma; Converted block repeats the output plus SPC.
    parse_ok False => ERROR (not NA). NA only when the output shows explicit N/A coordinates."""
    x=_txt(r); i=x.find('Transformed Coordinate'); j=x.find('Converted Coordinate')
    d={"parse_ok": False}
    if i < 0 or j < 0 or j < i:
        return d
    tb=x[i:j]; cb=x[j:]
    pairs=re.findall(LL,tb)
    if pairs:
        d['in_lat'],d['in_lon']=float(pairs[0][0]),float(pairs[0][1])
    if len(pairs)>=2:
        d['out_lat'],d['out_lon']=float(pairs[1][0]),float(pairs[1][1])
        c=re.search(LL,cb)
        d['converted_matches']=bool(c) and float(c.group(1))==d['out_lat'] and float(c.group(2))==d['out_lon']
        d['parse_ok']=True
    elif pairs and re.search(r'Input Epoch [\d.]+ Latitude N/A',tb):
        d['explicit_na']=True; d['parse_ok']=True
    s=re.search(r'Latitude (-?[\d.]+)″ ±([\d.]+)″ \((-?[\d.]+) m ±([\d.]+) m\) \* Longitude (-?[\d.]+)″ ±([\d.]+)″ \((-?[\d.]+) m ±([\d.]+) m\)',tb)
    if s: d.update(dlat_m=float(s.group(3)),siglat_m=float(s.group(4)),dlon_m=float(s.group(7)),siglon_m=float(s.group(8)))
    z=re.search(r'Epoch [\d.]+ Zone (.*?) Northing (-?[\d.]+|N/A) m (\S+) ift (\S+) usft Easting (-?[\d.]+|N/A) m',cb)
    if z: d.update(spc_zone=z.group(1),spc_n=z.group(2),spc_e=z.group(5))
    e=re.search(r'Output Epoch ([\d.]+)',tb); d['out_epoch']=e.group(1) if e else None
    return d
if __name__=="__main__":
    print(json.dumps(convert(float(sys.argv[1]),float(sys.argv[2]))[0]))
