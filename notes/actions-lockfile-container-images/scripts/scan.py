#!/usr/bin/env python3
"""scan.py REPO_DIR... : find container images a GitHub Actions lockfile would not pin.

Walks .github/workflows/*.yml the way the runner does: step `uses:`, local reusable
workflows, local `./` actions and, for remote actions, their action.yml at the referenced
ref (composite actions are followed). Reads action files anonymously from
raw.githubusercontent.com and caches them in --cache. Runs nothing from any repository.

Finding kinds (one JSON line per repository on stdout):
  workflow-docker-tag   `uses: docker://image:tag` in the repository's own workflow
                        (gh actions-lock prints a warning for these)
  action-image-tag      a Docker container action whose action.yml says image: docker://...:tag
  action-dockerfile     a Docker container action built from its Dockerfile at run time;
                        `base` lists FROM images that are not pinned by digest
  composite-docker-tag  `uses: docker://image:tag` inside a remote composite action
  job-container-tag     jobs.<id>.container / services image by tag (not a `uses:` dependency)
  composite-local-path  a remote composite action calls `./...`; gh actions-lock cannot lock it
An image is pinned when it carries @sha256:.
"""
import argparse, concurrent.futures as cf, json, os, re, sys, threading, urllib.error, urllib.request
import yaml

RAW = "https://raw.githubusercontent.com"
lock = threading.Lock()
cache = {}


def fetch(url):
    with lock:
        if url in cache:
            return cache[url]
    body = None
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "actions-lock-gap"})
            with urllib.request.urlopen(req, timeout=30) as r:
                body = r.read().decode("utf-8", "replace")
            break
        except urllib.error.HTTPError as e:
            if e.code == 404:
                break
        except Exception:
            pass
    with lock:
        cache[url] = body
    return body


def load_yaml(text):
    try:
        d = yaml.safe_load(text)
        return d if isinstance(d, dict) else None
    except Exception:
        return None


def pinned(image):
    return "@sha256:" in image


def parse_remote(uses):
    # owner/repo[/path]@ref
    if "@" not in uses or uses.startswith(("./", "docker://", "$/")) or "${{" in uses:
        return None
    left, ref = uses.rsplit("@", 1)
    parts = left.split("/")
    if len(parts) < 2 or not parts[0] or not parts[1]:
        return None
    return parts[0], parts[1], "/".join(parts[2:]), ref


def remote_action(owner, repo, path, ref):
    base = f"{RAW}/{owner}/{repo}/{ref}/" + (path + "/" if path else "")
    for name in ("action.yml", "action.yaml"):
        t = fetch(base + name)
        if t is not None:
            return load_yaml(t), base
    return None, base


def from_lines(dockerfile):
    stages, out = set(), []
    for line in dockerfile.splitlines():
        m = re.match(r"\s*FROM\s+(?:--platform=\S+\s+)?(\S+)(?:\s+AS\s+(\S+))?", line, re.I)
        if not m:
            continue
        img = m.group(1)
        if img.lower() != "scratch" and img.lower() not in stages and "$" not in img:
            out.append(img)
        if m.group(2):
            stages.add(m.group(2).lower())
    return out


class Scan:
    def __init__(self, root):
        self.root = root
        self.findings = []
        self.remote_uses = 0
        self.remote_reusable = 0
        self.seen = set()

    def add(self, kind, via, **kw):
        self.findings.append(dict(kind=kind, via=via, **kw))

    def steps(self, steps, via, ctx):
        for st in steps or []:
            if not isinstance(st, dict) or not isinstance(st.get("uses"), str):
                continue
            self.use(st["uses"].strip(), via, ctx)

    def use(self, uses, via, ctx):
        if uses.startswith("docker://"):
            img = uses[len("docker://"):]
            if not pinned(img):
                self.add("workflow-docker-tag" if ctx == "own" else "composite-docker-tag", via, image=img)
            return
        if uses.startswith("./"):
            if ctx != "own":
                # gh actions-lock refuses to onboard the workflow (CompositeLocalPathError)
                self.add("composite-local-path", via, path=uses)
                return
            d = os.path.join(self.root, uses[2:])
            for name in ("action.yml", "action.yaml"):
                p = os.path.join(d, name)
                if os.path.isfile(p):
                    a = load_yaml(open(p, encoding="utf-8", errors="replace").read())
                    if a:
                        self.action(a, uses, None, "own")
                    break
            return
        r = parse_remote(uses)
        if not r:
            return
        self.remote_uses += 1
        key = uses
        if key in self.seen:
            return
        self.seen.add(key)
        a, base = remote_action(*r)
        if a:
            self.action(a, uses, base, "remote")

    def action(self, a, via, base, ctx):
        runs = a.get("runs") or {}
        if not isinstance(runs, dict):
            return
        using = str(runs.get("using", "")).lower()
        if using == "composite":
            self.steps(runs.get("steps"), via, "remote" if ctx == "remote" else "own")
        elif using == "docker":
            image = str(runs.get("image", "")).strip()
            if image.startswith("docker://"):
                img = image[len("docker://"):]
                if not pinned(img):
                    self.add("action-image-tag", via, image=img)
            elif image:
                df = None
                if base:
                    df = fetch(base + image)
                else:
                    p = os.path.join(self.root, via[2:], image)
                    if os.path.isfile(p):
                        df = open(p, encoding="utf-8", errors="replace").read()
                froms = from_lines(df) if df else None
                unpinned = [f for f in (froms or []) if not pinned(f)]
                if froms is None or unpinned:
                    self.add("action-dockerfile", via, dockerfile=image, base=unpinned if froms is not None else None)

    def workflow(self, w, via, ctx):
        jobs = w.get("jobs") or {}
        if not isinstance(jobs, dict):
            return
        for jid, job in jobs.items():
            if not isinstance(job, dict):
                continue
            c = job.get("container")
            imgs = [c] if isinstance(c, str) else [c.get("image")] if isinstance(c, dict) else []
            for s in (job.get("services") or {}).values() if isinstance(job.get("services"), dict) else []:
                if isinstance(s, dict):
                    imgs.append(s.get("image"))
            for img in imgs:
                if isinstance(img, str) and img and "${{" not in img and not pinned(img):
                    self.add("job-container-tag", via, image=img)
            u = job.get("uses")
            if isinstance(u, str):
                u = u.strip()
                if u.startswith("./"):
                    p = os.path.join(self.root, u[2:])
                    if os.path.isfile(p) and p not in self.seen:
                        self.seen.add(p)
                        sub = load_yaml(open(p, encoding="utf-8", errors="replace").read())
                        if sub:
                            self.workflow(sub, u, "own")
                elif parse_remote(u):
                    # A remote reusable workflow is covered by the lockfile of the repository
                    # that defines it, not by this one (GitHub Docs), so it is not followed.
                    self.remote_reusable += 1
            self.steps(job.get("steps"), via, ctx)


def scan_repo(path):
    wdir = os.path.join(path, ".github", "workflows")
    files = sorted(f for f in os.listdir(wdir) if f.endswith((".yml", ".yaml"))) if os.path.isdir(wdir) else []
    s = Scan(path)
    for f in files:
        w = load_yaml(open(os.path.join(wdir, f), encoding="utf-8", errors="replace").read())
        if w:
            s.workflow(w, f".github/workflows/{f}", "own")
    return dict(repo=os.path.basename(path.rstrip("/")).replace("__", "/", 1), workflows=len(files),
                remote_uses=s.remote_uses, remote_reusable=s.remote_reusable, findings=s.findings)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repos", nargs="+")
    ap.add_argument("--cache", default="action-cache.json")
    ap.add_argument("-j", type=int, default=16)
    a = ap.parse_args()
    if os.path.exists(a.cache):
        cache.update(json.load(open(a.cache)))
    with cf.ThreadPoolExecutor(a.j) as ex:
        for res in ex.map(scan_repo, a.repos):
            print(json.dumps(res), flush=True)
    json.dump(cache, open(a.cache, "w"), sort_keys=True)


if __name__ == "__main__":
    main()
