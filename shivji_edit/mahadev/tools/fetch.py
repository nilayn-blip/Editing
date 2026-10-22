"""Usage: python3 -I fetch.py LISTFILE OUTDIR WIDTH  (LISTFILE: one 'key|File:title' per line)
Fetches standard-size Commons thumbnails (via upload.wikimedia.org) politely: sequential,
spaced, honouring Retry-After. Writes OUTDIR/<key>.jpg and OUTDIR/meta.json."""
import json, os, sys, time, urllib.request, urllib.error
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wm import api, UA, strip
lst, out, width = sys.argv[1], sys.argv[2], int(sys.argv[3])
os.makedirs(out, exist_ok=True)
items = [l.strip().split("|", 1) for l in open(lst) if l.strip()]
meta = {}
mp = os.path.join(out, "meta.json")
if os.path.exists(mp) and len(json.load(open(mp))) >= len(items): meta = json.load(open(mp)); items = []
for i in range(0, len(items), 40):
    chunk = items[i:i + 40]
    d = api({"action": "query", "titles": "|".join(t for _, t in chunk), "prop": "imageinfo",
             "iiprop": "url|size|extmetadata", "iiurlwidth": width})
    norm = {n["from"]: n["to"] for n in d["query"].get("normalized", [])}
    pages = {p["title"]: p for p in d["query"]["pages"]}
    for key, t in chunk:
        p = pages.get(norm.get(t, t))
        if not p or "imageinfo" not in p: print("MISSING", key, t, flush=True); continue
        ii = p["imageinfo"][0]; m = ii["extmetadata"]
        g = lambda k: strip(m.get(k, {}).get("value", ""))
        meta[key] = dict(title=p["title"], width=ii["width"], height=ii["height"], page=ii["descriptionurl"],
                         original=ii["url"], thumb=ii["thumburl"].split("?")[0].replace("thumb.wikimedia.org", "upload.wikimedia.org"),
                         thumbwidth=ii.get("thumbwidth"), thumbheight=ii.get("thumbheight"),
                         license=g("LicenseShortName"), license_url=g("LicenseUrl"), artist=g("Artist"),
                         credit=g("Credit"), usage_terms=g("UsageTerms"), attribution_required=g("AttributionRequired"))
    time.sleep(2)
if items: json.dump(meta, open(mp, "w"), indent=1, ensure_ascii=False)
for key, m in meta.items():
    fn = os.path.join(out, key + ".jpg")
    if "/thumb/" not in m["thumb"]:  # requested width >= original: never pull originals, use the 1280 bucket
        base, name = m["original"].split("?")[0].rsplit("/", 1)
        m["thumb"] = base.replace("/commons/", "/commons/thumb/") + "/" + name + "/1280px-" + name
    if os.path.exists(fn) and os.path.getsize(fn) > 5000: continue
    backoff = 60
    while True:
        try:
            req = urllib.request.Request(m["thumb"], headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r: data = r.read()
            open(fn, "wb").write(data); print("ok", key, len(data), flush=True); break
        except urllib.error.HTTPError as e:
            w = max(int(e.headers.get("retry-after") or 60), backoff)
            backoff = min(backoff * 2, 900)
            print(f"HTTP {e.code} {key}, waiting {w}s", flush=True)
            if e.code not in (429, 503): break
            time.sleep(w)
        except Exception as e:
            print("err", key, e, flush=True); time.sleep(30)
    time.sleep(20)
print("DONE", flush=True)
