"""Compare what an image URL returns to Chrome 154 and Chrome 155 request headers.

Chrome 155 adds image/jxl to the Accept header it sends for images. A CDN that negotiates the
format on Accept (for example Cloudinary f_auto) may answer it with a different file.

Usage: python3 jxlcheck.py URL [URL ...]
Standard library only. Two GET requests per URL, 0.5 s apart, no compression, nothing saved.
"""
import sys
import time
import urllib.request

ACCEPT = {
    "154": "image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
    "155": "image/jxl,image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
}


def headers(v):
    return {
        "User-Agent": f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{v}.0.0.0 Safari/537.36",
        "Accept": ACCEPT[v],
        "Accept-Encoding": "identity",
        "Accept-Language": "en-US,en;q=0.9",
        "sec-ch-ua": f'"Chromium";v="{v}", "Google Chrome";v="{v}", "Not_A Brand";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"Windows"',
        "Sec-Fetch-Dest": "image",
    }


def sniff(b):
    if b.startswith(b"\xff\x0a") or b.startswith(b"\x00\x00\x00\x0cJXL \r\n\x87\n"):
        return "jxl"
    if b[4:8] == b"ftyp" and b[8:12] in (b"avif", b"avis"):
        return "avif"
    if b.startswith(b"RIFF") and b[8:12] == b"WEBP":
        return "webp"
    if b.startswith(b"\xff\xd8\xff"):
        return "jpeg"
    if b.startswith(b"\x89PNG\r\n\x1a\n"):
        return "png"
    if b.startswith((b"GIF87a", b"GIF89a")):
        return "gif"
    return "other"


def fetch(url, v):
    req = urllib.request.Request(url, headers=headers(v))
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read()
        return sniff(body), len(body)


def main(urls):
    if not urls:
        sys.exit(__doc__)
    print("chrome154\tchrome155\tratio\turl")
    for i, url in enumerate(urls):
        if i:
            time.sleep(0.5)
        try:
            f4, n4 = fetch(url, "154")
            time.sleep(0.5)
            f5, n5 = fetch(url, "155")
        except Exception as e:  # report and continue with the next URL
            print(f"error\terror\t-\t{url}\t({e})")
            continue
        ratio = f"{n5 / n4:.2f}x" if n4 else "-"
        print(f"{f4} {n4:,} B\t{f5} {n5:,} B\t{ratio}\t{url}")


if __name__ == "__main__":
    main(sys.argv[1:])
