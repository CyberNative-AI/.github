"""Minimal JSON-RPC client for the Odoo web client's own endpoints."""
import http.cookiejar
import json
import urllib.request


class Odoo:
    def __init__(self, url, db, login="admin", password="admin"):
        self.url = url
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        self.calls = []
        self.post("/web/session/authenticate", {"db": db, "login": login, "password": password})

    def post(self, path, params):
        body = json.dumps({"jsonrpc": "2.0", "method": "call", "id": 1, "params": params}).encode()
        req = urllib.request.Request(self.url + path, body, {"Content-Type": "application/json"})
        res = json.load(self.op.open(req, timeout=900))
        if res.get("error"):
            raise RuntimeError(json.dumps(res["error"])[:2000])
        return res["result"]

    def kw(self, model, method, args, kwargs=None):
        self.calls.append((model, method, args[:1]))
        return self.post("/web/dataset/call_kw/%s/%s" % (model, method),
                         {"model": model, "method": method, "args": args, "kwargs": kwargs or {}})

    def button(self, model, method, ids):
        """What a list/form header button of type object sends."""
        self.calls.append((model, method, [ids]))
        return self.post("/web/dataset/call_button/%s/%s" % (model, method),
                         {"model": model, "method": method, "args": [ids], "kwargs": {"context": {"lang": "en_US", "tz": "UTC"}}})

    def list_ids(self, model, domain, order=""):
        """The ids a list view shows, in the order it shows them (web_search_read like the client)."""
        r = self.kw(model, "web_search_read", [], {"domain": domain, "specification": {"display_name": {}},
                                                   "order": order, "limit": 1000,
                                                   "context": {"lang": "en_US", "tz": "UTC"}})
        return [x["id"] for x in r["records"]]
