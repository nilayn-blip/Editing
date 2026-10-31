"""Minimal Wikimedia Commons API client (search + imageinfo) with Retry-After handling."""
import json, sys, time, urllib.parse, urllib.request, re
UA = "ShivjiEditBot/1.0 (https://github.com/nilayn-blip/editing; devotional video credits)"
API = "https://commons.wikimedia.org/w/api.php"
def api(params, tries=8):
    params = dict(params, format="json", formatversion="2")
    url = API + "?" + urllib.parse.urlencode(params)
    for k in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": UA}), timeout=60) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code == 429:
                w = int(e.headers.get("retry-after", "20")) + 2
                print(f"  429, sleeping {w}s", file=sys.stderr); time.sleep(w); continue
            raise
    raise SystemExit("rate limited")
def strip(h): return re.sub(r"<[^>]+>", "", h or "").strip()
def search(q, n=25):
    d = api({"action": "query", "generator": "search", "gsrsearch": q + " filetype:bitmap", "gsrnamespace": 6,
             "gsrlimit": n, "prop": "imageinfo", "iiprop": "url|size|extmetadata",
             "iiextmetadatafilter": "LicenseShortName|Artist|ImageDescription"})
    out = []
    for p in d.get("query", {}).get("pages", []):
        ii = p["imageinfo"][0]; m = ii.get("extmetadata") or {}
        out.append((p["title"], ii["width"], ii["height"], m.get("LicenseShortName", {}).get("value"), strip(m.get("Artist", {}).get("value"))[:40]))
    return out
if __name__ == "__main__":
    for q in sys.argv[1:]:
        print("==", q)
        for t in search(q):
            if min(t[1], t[2]) >= 1200: print("  ", t)
        time.sleep(3)
