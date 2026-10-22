"""Usage: python3 -I assemble.py DLDIR PROJECTDIR KEYS -> resized assets + photos.json (focus from focus.json)."""
import json, os, sys, glob
from PIL import Image
dl, proj = sys.argv[1], sys.argv[2]
meta, where = {}, {}
for d in sorted(glob.glob(os.path.join(dl, "*"))):
    for f in glob.glob(os.path.join(d, "meta*.json")):
        for k, v in json.load(open(f)).items():
            fn = os.path.join(d, k + ".jpg")
            if not os.path.exists(fn): continue
            if k not in meta or os.path.getsize(fn) > os.path.getsize(os.path.join(where[k], k + ".jpg")):
                meta[k], where[k] = v, d  # keep the largest download of each photo
ORDER = sys.argv[3].split(",")
INSET = {"s4": (0.04, 0.03, 0.04, 0.03), "s6": (0.06, 0.05, 0, 0.02)}  # key: (l, t, r, b): paper borders
AUTHOR = {"s1": "Unknown artist", "s2": "Nandalal Bose (illustrator)", "s4": "Unknown artist, Kullu school", "s6": "Unknown artist"}  # tidy "Unknown authorUnknown author" etc.
LABEL = {}
FOCUS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "focus.json")))
TW, TH = 1300, 2310  # cover box: frame x ~1.2 for the Ken Burns move
photos = []
for n, key in enumerate(ORDER, 1):
    m = meta[key]
    im = Image.open(os.path.join(where[key], key + ".jpg")).convert("RGB")
    if key in INSET:
        l, t, r, b = INSET[key]; im = im.crop((round(im.width * l), round(im.height * t), round(im.width * (1 - r)), round(im.height * (1 - b))))
    s = max(TW / im.width, TH / im.height)
    if s < 1: im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    focus = FOCUS.get(key, "50% 50%")
    fx, fy = (float(v.rstrip("%")) / 100 for v in focus.split())
    maxw = round(im.height * 0.8)  # wide photos: keep a 0.8:1 window around the focus (frame is 0.5625:1)
    if im.width > maxw:
        x0 = min(max(round(fx * im.width - maxw / 2), 0), im.width - maxw)
        fx = (fx * im.width - x0) / maxw
        im = im.crop((x0, 0, x0 + maxw, im.height))
        focus = f"{fx * 100:.0f}% {fy * 100:.0f}%"
    fn = f"p{n:02d}.jpg"
    im.save(os.path.join(proj, "assets", fn), quality=88, optimize=True, progressive=True)
    photos.append(dict(label=LABEL.get(key, key), file=fn, focus=focus, alt=m["title"][5:].rsplit(".", 1)[0],
        title=m["title"], author=AUTHOR.get(key, m["artist"]), license=m["license"],
        license_url=m["license_url"], page=m["page"], original=m["original"].split("?")[0],
        source_size=f'{m["width"]}x{m["height"]}', used_size=f"{im.width}x{im.height}"))
    print(key, fn, im.size, m["license"], "|", m["artist"])
json.dump(photos, open(os.path.join(os.path.dirname(proj.rstrip("/")), "photos.json"), "w"), indent=2, ensure_ascii=False)
