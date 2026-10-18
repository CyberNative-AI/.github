#!/usr/bin/env python3
"""Probe TLS server images for X25519MLKEM768 with a minimal certificate-only setup.

Usage: python3 run.py [UNIT ...]   (default: every unit below, in order)

Starts each target image (pinned by digest in images.tsv) on an --internal Docker network as the
container `target`, probes it from the OpenSSL 3.5 client image built from client.Dockerfile
(M1 = client default groups, M2 = -groups X25519MLKEM768 only, 3 repeats each) and writes
out/<unit>/ (raw s_client output, container log) and out/results.jsonl. shell=False throughout.
Needs certs/cert.pem, certs/key.pem and certs/combined.pem (see README.md).
"""
import json, re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
CONF, CERTS = HERE / "conf", HERE / "certs"
NET, CLIENT_IMG, CLIENT = "pqprobe-net", "pqprobe-client:1", "pqprobe-client"
LIMITS = ["--cpus", "2", "--memory", "2g"]
REPEATS, READY_S = 3, 600
PIN = {r.split("\t")[0]: r.split("\t")[1] for r in (HERE / "images.tsv").read_text().splitlines()[1:]}

def m(src, dst):
    return ["-v", f"{src}:{dst}:ro"]

CERT = m(CERTS, "/certs")
KONG_ENV = ["-e", "KONG_DATABASE=off", "-e", "KONG_DECLARATIVE_CONFIG=/kong/kong.yml",
            "-e", "KONG_PROXY_LISTEN=0.0.0.0:8443 ssl", "-e", "KONG_ADMIN_LISTEN=off",
            "-e", "KONG_SSL_CERT=/certs/cert.pem", "-e", "KONG_SSL_CERT_KEY=/certs/key.pem"] + m(CONF / "kong.yml", "/kong/kong.yml")
HTTPD_SH = ("sed -i -e 's/^#\\(Include .*httpd-ssl.conf\\)/\\1/' -e 's/^#\\(LoadModule .*mod_ssl.so\\)/\\1/' "
            "-e 's/^#\\(LoadModule .*mod_socache_shmcb.so\\)/\\1/' conf/httpd.conf && "
            "cp /certs/cert.pem conf/server.crt && cp /certs/key.pem conf/server.key && exec httpd-foreground")
TOMCAT_SH = ("c=$(cat /re/tomcat-connector.xml) && "
             "awk -v c=\"$c\" '/<\\/Service>/{print c}1' conf/server.xml > /tmp/s && "
             "cp /tmp/s conf/server.xml && exec catalina.sh run")
NGINX_FG = ["--entrypoint", "nginx"]

# unit -> (image, extra docker-run args before image, cmd after image, port)
UNITS = {
    # controls: the client image's own nginx, without (C+) and with (C-) an explicit curve list
    "CPLUS":  (CLIENT_IMG, CERT + m(CONF / "nginx-min.conf", "/etc/nginx/conf.d/re.conf") + NGINX_FG, ["-g", "daemon off;"], 8443),
    "CMINUS": (CLIENT_IMG, CERT + m(CONF / "nginx-cminus.conf", "/etc/nginx/conf.d/re.conf") + NGINX_FG, ["-g", "daemon off;"], 8443),
    "U01": ("nginx:latest", CERT + m(CONF / "nginx-min.conf", "/etc/nginx/conf.d/re.conf"), [], 8443),
    "U02": ("nginx:alpine", CERT + m(CONF / "nginx-min.conf", "/etc/nginx/conf.d/re.conf"), [], 8443),
    "U03": ("envoyproxy/envoy:v1.40.0", CERT + m(CONF / "envoy.yaml", "/etc/envoy/envoy.yaml"), [], 8443),
    "U04": ("httpd:latest", CERT + ["--entrypoint", "sh"], ["-c", HTTPD_SH], 443),
    "U05": ("traefik:latest", CERT + m(CONF / "traefik.yml", "/etc/traefik/traefik.yml") + m(CONF / "traefik-dyn.yml", "/etc/traefik/dyn.yml"), [], 8443),
    "U06": ("pomerium/pomerium:latest", CERT + m(CONF / "pomerium.yaml", "/pomerium/config.yaml"), [], 8443),
    "U07": ("nginxinc/nginx-unprivileged:latest", CERT + m(CONF / "nginx-min.conf", "/etc/nginx/conf.d/re.conf"), [], 8443),
    "U08": ("haproxy:latest", CERT + m(CONF / "haproxy.cfg", "/usr/local/etc/haproxy/haproxy.cfg"), [], 8443),
    "U09": ("kong/kong-gateway:latest", CERT + KONG_ENV, [], 8443),
    "U10": ("tomcat:latest", CERT + m(CONF / "tomcat-connector.xml", "/re/tomcat-connector.xml") + ["--entrypoint", "sh"], ["-c", TOMCAT_SH], 8443),
    "U11": ("caddy:latest", CERT + m(CONF / "Caddyfile", "/etc/caddy/Caddyfile"), [], 8443),
    "U12": ("jwilder/nginx-proxy:latest", CERT + m(CONF / "nginx-proxy-bundled.conf", "/etc/nginx/conf.d/re.conf") + NGINX_FG, ["-g", "daemon off;"], 8443),
    "U13": ("bitnami/nginx:latest", CERT + m(CONF / "nginx-min.conf", "/opt/bitnami/nginx/conf/server_blocks/re.conf"), [], 8443),
    "U14": ("kong:latest", CERT + KONG_ENV, [], 8443),
    # U15: image nginx.conf already says `daemon off;`; image default.conf kept (443 ssl_reject_handshake; sets $server used by log-proxy.conf); runtime user npm + dirs created (normally done by /init)
    "U15": ("jc21/nginx-proxy-manager:latest", CERT + m(CONF / "npm-proxyhost.conf", "/etc/nginx/conf.d/re.conf") + ["--entrypoint", "sh"],
            ["-c", "(id npm >/dev/null 2>&1 || useradd -r -M npm) && mkdir -p /data/logs /run/nginx /tmp/nginx/body /var/log/nginx /var/lib/nginx/cache/public /var/lib/nginx/cache/private /var/cache/nginx/proxy_temp && exec nginx"], 8443),
    # cause arms (not counted): kong:latest with the PQ group set; plain Envoy v1.38.5 without and with ecdh_curves
    "U14-FIX": ("kong:latest", CERT + KONG_ENV + ["-e", "KONG_NGINX_PROXY_SSL_ECDH_CURVE=X25519MLKEM768:X25519"], [], 8443),
    "E1385-DEF": ("envoyproxy/envoy:v1.38.5", CERT + m(CONF / "envoy.yaml", "/etc/envoy/envoy.yaml"), [], 8443),
    "E1385-ECDH": ("envoyproxy/envoy:v1.38.5", CERT + m(CONF / "envoy-ecdh.yaml", "/etc/envoy/envoy.yaml"), [], 8443),
}

def run(argv, timeout=60, check=False):
    p = subprocess.run(argv, capture_output=True, text=True, timeout=timeout)
    if check and p.returncode:
        raise RuntimeError(f"{argv}: rc={p.returncode} {p.stderr[-500:]}")
    return p

def probe(port, pq_only):
    cmd = f"timeout 15 openssl s_client -connect target:{port} -servername probe.test" + (" -groups X25519MLKEM768" if pq_only else "") + " </dev/null 2>&1; echo RC=$?"
    return run(["docker", "exec", CLIENT, "sh", "-c", cmd], timeout=40).stdout

def parse(txt):
    g = re.search(r"^Negotiated TLS1\.3 group: (\S+)", txt, re.M)
    t = re.search(r"^(?:Peer|Server) Temp Key: ([^\n]+)", txt, re.M)
    pr = re.search(r"^\s*Protocol\s*:\s*(\S+)", txt, re.M)
    cipher = re.search(r"Cipher is (\S+)", txt)
    ok = bool(cipher) and cipher.group(1) != "(NONE)"
    group = g.group(1) if g else (t.group(1).split(",")[0].strip() if t and ok else None)
    return {"handshake": ok, "group": group if ok else None, "tls13_group_line": g.group(1) if g else None,
            "temp_key_line": t.group(1) if t else None, "protocol": pr.group(1) if pr else None}

def unit(name):
    image, args, cmd, port = UNITS[name]
    image = PIN.get(image, image)
    d = OUT / name
    d.mkdir(parents=True, exist_ok=True)
    run(["docker", "rm", "-f", "target"])
    argv = ["docker", "run", "-d", "--name", "target", "--network", NET] + LIMITS + args + [image] + cmd
    (d / "docker-run.json").write_text(json.dumps(argv, indent=1) + "\n")
    rec = {"unit": name, "image": image, "image_id": run(["docker", "image", "inspect", "--format", "{{.Id}}", image]).stdout.strip()}
    p = run(argv)
    if p.returncode:
        rec.update(result="EXCLUDED_SETUP", reason=f"start rc={p.returncode}: {p.stderr.strip()[-300:]}")
        return rec
    t0, ready = time.time(), False
    while time.time() - t0 < READY_S:
        if run(["docker", "inspect", "-f", "{{.State.Running}}", "target"]).stdout.strip() != "true":
            break
        if "Cipher is" in probe(port, False):
            ready = True
            break
        time.sleep(3)
    rec["ready_s"] = round(time.time() - t0, 1)
    if ready:
        for meas, pq in (("M1", False), ("M2", True)):
            reps = []
            for i in range(REPEATS):
                txt = probe(port, pq)
                (d / f"{meas}_{i}.txt").write_text(txt)
                reps.append(parse(txt))
            rec[meas] = reps
    logs = run(["docker", "logs", "target"])
    (d / "container.log").write_text(logs.stdout + logs.stderr)
    run(["docker", "rm", "-f", "target"])
    if not ready:
        rec.update(result="EXCLUDED_SETUP", reason="no TLS handshake before ready limit or container exited")
        return rec
    m1 = [r["group"] for r in rec["M1"]]
    m2 = [r["handshake"] and r["group"] == "X25519MLKEM768" for r in rec["M2"]]
    rec["stable"] = len(set(m1)) == 1 and len(set(m2)) == 1
    rec["m1_group"] = m1[0] if rec["stable"] else m1
    rec["m2_pq_ok"] = m2[0] if rec["stable"] else m2
    rec["result"] = "UNSTABLE" if not rec["stable"] else ("PQ" if m1[0] == "X25519MLKEM768" else "NO_PQ")
    return rec

def main(names):
    run(["docker", "network", "create", "--internal", NET])
    run(["docker", "rm", "-f", CLIENT])
    run(["docker", "run", "-d", "--name", CLIENT, "--network", NET] + LIMITS + [CLIENT_IMG, "sleep", "infinity"], check=True)
    OUT.mkdir(exist_ok=True)
    (OUT / "client-openssl.txt").write_text(run(["docker", "exec", CLIENT, "openssl", "version", "-a"]).stdout)
    try:
        with (OUT / "results.jsonl").open("a") as f:
            for n in names:
                rec = unit(n)
                rec["ts"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
                f.write(json.dumps(rec, sort_keys=True) + "\n"); f.flush()
                print(n, rec["result"], rec.get("m1_group"), "M2ok=", rec.get("m2_pq_ok"), rec.get("reason", ""), flush=True)
    finally:
        run(["docker", "rm", "-f", "target", CLIENT])
        run(["docker", "network", "rm", NET])

if __name__ == "__main__":
    main(sys.argv[1:] or list(UNITS))
