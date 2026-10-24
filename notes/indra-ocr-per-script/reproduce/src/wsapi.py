"""Minimal MediaWiki API client for Wikisource (POST, polite UA, retries)."""
import json, time, urllib.parse, urllib.request

UA = {"User-Agent": "CyberNativeResearch/0.1 (research; hello@cybernative.ai)"}


def api(lang, **params):
    params.update(format="json", formatversion=2)
    data = urllib.parse.urlencode(params).encode()
    url = f"https://{lang}.wikisource.org/w/api.php"
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=data, headers=UA)
            with urllib.request.urlopen(req, timeout=90) as r:
                return json.load(r)
        except Exception as e:
            if attempt == 5:
                raise
            time.sleep((15 if getattr(e, "code", None) == 429 else 3) * (attempt + 1))


def fetch_bytes(url, timeout=120):
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout) as r:
                return r.read()
        except Exception as e:
            if attempt == 5 or getattr(e, "code", None) in (400, 404):
                raise
            time.sleep((15 if getattr(e, "code", None) == 429 else 3) * (attempt + 1))
