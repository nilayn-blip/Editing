"""Reel kit for @nirva_nataless: one reel.json -> a narrated, captioned devotional reel (HyperFrames).

The format grew out of ../status (Mahadev) and ../krishna: a black hook card, public-domain paintings with
slow push-ins and soft dissolves, one caption per spoken line revealed word by word in sync with a Hindi
TTS narrator, an original raga score that dips under the voice, and an end card with the closing line,
@nirva_nataless and "Follow for more". The watermark "Nirvana ✦ Nilay" is shown throughout.

Usage (from shivji_edit/):
  python3 reel_kit/kit.py reels/NN-slug all          # every step below, in order
  python3 reel_kit/kit.py reels/NN-slug STEP [...]   # fetch | assemble | narrate | sound | build | render
  python3 reel_kit/kit.py reels/NN-slug myvoice REC.m4a sound build render   # use the owner's own recording

reel.json fields: slug, title, pace ("short" 15-20 s | "medium"), hook_style ("bold" | "elegant"),
hook_over_image (default: true for short), raga (see RAGAS), end_sound ("om" | "ghanti"), intro {spoken, caption},
lines [{spoken, caption}], end {spoken, caption}, paintings [{key, file, focus?, inset?, author?}],
caption_post (Instagram caption with hashtags). In captions, *word* is highlighted in gold. "spoken" is what the voice reads (English words spelt in
Devanagari); "caption" is what appears on screen (Hindi with English words, as people speak).
"""
import glob
import html
import json
import os
import shutil
import subprocess
import sys
import urllib.request
import wave
import zlib

KIT = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(KIT)  # shivji_edit/
sys.path.insert(0, ROOT)

HANDLE = "@nirva_nataless"
VOICE_URL = "https://huggingface.co/rhasspy/piper-voices/resolve/main/hi/hi_IN/{name}/medium/hi_IN-{name}-medium.onnx"
VOICE_CACHE = os.path.expanduser("~/.cache/piper-voices")
RAGAS = {  # scale degrees in semitones above Sa
    "shivaranjani": [0, 2, 3, 7, 9],
    "bhupali": [0, 2, 4, 7, 9],
    "durga": [0, 2, 5, 7, 9],
    "malkauns": [0, 3, 5, 8, 10],
    "yaman": [0, 2, 4, 6, 7, 9, 11],
    "bhairav": [0, 1, 4, 5, 7, 8, 11],
}
CHROME = sorted(glob.glob("/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell"))


def load(d):
    return json.load(open(os.path.join(d, "reel.json")))


def run(cmd, **kw):
    print("+", " ".join(cmd) if isinstance(cmd, list) else cmd, flush=True)
    return subprocess.run(cmd, check=True, **kw)


# ---------------------------------------------------------------- fetch / assemble
def step_fetch(d, r):
    lst = os.path.join(d, ".dl", "list.txt")
    os.makedirs(os.path.dirname(lst), exist_ok=True)
    with open(lst, "w") as f:
        for p in r["paintings"]:
            f.write(f'{p["key"]}|{p["file"]}\n')
    # standard-size thumbnails only, polite and sequential; waits out Wikimedia's rate limits
    run([sys.executable, "-I", os.path.join(KIT, "tools", "fetch.py"), lst, os.path.join(d, ".dl", "a"), "1920"])
    missing = [p["key"] for p in r["paintings"] if not os.path.exists(os.path.join(d, ".dl", "a", p["key"] + ".jpg"))]
    if missing:
        sys.exit(f"still missing: {missing} (re-run fetch; it resumes)")


def step_assemble(d, r):
    from PIL import Image
    meta = json.load(open(os.path.join(d, ".dl", "a", "meta.json")))
    assets = os.path.join(d, "project", "assets")
    for f in glob.glob(os.path.join(assets, "p[0-9][0-9].jpg")):
        os.remove(f)
    TW, TH = 1300, 2310  # cover box: frame x ~1.2 for the Ken Burns move
    photos = []
    for n, p in enumerate(r["paintings"], 1):
        m = meta[p["key"]]
        im = Image.open(os.path.join(d, ".dl", "a", p["key"] + ".jpg")).convert("RGB")
        if p.get("inset"):
            l, t, rr, b = p["inset"]
            im = im.crop((round(im.width * l), round(im.height * t), round(im.width * (1 - rr)), round(im.height * (1 - b))))
        s = max(TW / im.width, TH / im.height)
        if s < 1:
            im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
        focus = p.get("focus", "50% 40%")
        fx, fy = (float(v.rstrip("%")) / 100 for v in focus.split())
        maxw = round(im.height * 0.8)  # keep a 0.8:1 window around the focus (frame is 0.5625:1)
        if im.width > maxw:
            x0 = min(max(round(fx * im.width - maxw / 2), 0), im.width - maxw)
            fx = (fx * im.width - x0) / maxw
            im = im.crop((x0, 0, x0 + maxw, im.height))
            focus = f"{fx * 100:.0f}% {fy * 100:.0f}%"
        fn = f"p{n:02d}.jpg"
        im.save(os.path.join(assets, fn), quality=88, optimize=True, progressive=True)
        photos.append(dict(key=p["key"], file=fn, focus=focus, alt=m["title"][5:].rsplit(".", 1)[0], title=m["title"],
                           author=p.get("author") or m["artist"], license=m["license"], license_url=m["license_url"],
                           page=m["page"], original=m["original"].split("?")[0]))
        print(p["key"], fn, im.size, m["license"])
    json.dump(photos, open(os.path.join(d, "photos.json"), "w"), indent=2, ensure_ascii=False)


# ---------------------------------------------------------------- narration + timing
def voice_model(name):
    path = os.path.join(VOICE_CACHE, f"hi_IN-{name}-medium.onnx")
    if not os.path.exists(path):
        os.makedirs(VOICE_CACHE, exist_ok=True)
        for suffix in ("", ".json"):
            urllib.request.urlretrieve(VOICE_URL.format(name=name) + suffix, path + suffix)
    return path


def wav_len(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def step_narrate(d, r, length_scale=1.12):
    model = voice_model(r.get("voice", "pratham"))
    out = os.path.join(d, "narration")
    os.makedirs(out, exist_ok=True)
    items = [r["intro"]] + r["lines"] + [r["end"]]
    durs = []
    for i, it in enumerate(items):
        path = os.path.join(out, f"l{i}.wav")
        run(["piper", "-m", model, "-c", model + ".json", "--length-scale", str(length_scale),
             "--sentence-silence", "0.1", "-f", path], input=it["spoken"].encode(), stderr=subprocess.DEVNULL)
        durs.append(round(wav_len(path), 3))
    write_timing(d, r, items, durs, voice="tts")


# pace profiles: lead-in, hook gap, minimum segment, breath after a line, voice offset in a segment, tail
PACES = {
    "medium": dict(lead=0.5, hook_gap=0.6, hook_min=3.0, seg_min=5.0, breath=2.4, offset=0.45, tail=1.8),
    "short": dict(lead=0.3, hook_gap=0.35, hook_min=2.0, seg_min=3.2, breath=1.3, offset=0.3, tail=1.3),
}


def write_timing(d, r, items, durs, voice):
    """One segment per line, long enough for the voice plus a breath; the hook and the end card around them."""
    P = PACES[r.get("pace", "medium")]
    img0 = round(max(P["hook_min"], P["lead"] + durs[0] + P["hook_gap"]), 2)
    t, segs = img0, []
    for dd in durs[1:-1]:
        seg = round(max(P["seg_min"], dd + P["breath"]), 2)
        segs.append([round(t, 2), seg])
        t += seg
    end = round(t, 2)
    starts = [P["lead"]] + [s + P["offset"] for s, _ in segs] + [end + P["offset"]]
    dur = round(end + P["offset"] + durs[-1] + P["tail"], 2)
    hook_img = bool(r.get("hook_over_image", r.get("pace") == "short"))
    img_start = 0.0 if hook_img else img0  # paintings/photos start under the hook when it sits on an image
    n_img = len(r["paintings"])
    if hook_img and n_img == len(segs) + 2:  # one image per beat: hook, each line, end card
        img_times = [0.0] + [s for s, _ in segs] + [end]
    elif not hook_img and n_img == len(segs) + 1:  # one per line, the last one also under the end card
        img_times = [s for s, _ in segs] + [end]
    else:  # spread evenly
        img_times = [round(img_start + k * (end - img_start) / n_img, 3) for k in range(n_img)]
    timing = dict(dur=dur, img0=img0, img_start=img_start, hook_over_image=hook_img, end=end, segments=segs,
                  img_times=img_times, img_len=round((end - img_start) / n_img, 3), voice=voice,
                  lines=[dict(spoken=it["spoken"], caption=it["caption"], start=round(s, 2), dur=dd, wav=f"narration/l{i}.wav")
                         for i, (it, s, dd) in enumerate(zip(items, starts, durs))])
    json.dump(timing, open(os.path.join(d, "timing.json"), "w"), indent=1, ensure_ascii=False)
    print(json.dumps({k: timing[k] for k in ("dur", "img0", "end", "img_len", "voice")}))


def step_myvoice(d, r, src):
    """Use the owner's own recording: one take, all lines in order (hook, lines, end), ~1 s pause between lines.

    Cleans it (rumble cut, denoise, gentle compression, level), splits it at the pauses into one file per
    line, and rewrites timing.json so captions follow the real voice. Run `sound build render` afterwards.
    """
    import numpy as np
    from scipy.io import wavfile
    items = [r["intro"]] + r["lines"] + [r["end"]]
    out = os.path.join(d, "narration")
    os.makedirs(out, exist_ok=True)
    clean = os.path.join(d, ".work", "myvoice_clean.wav")
    os.makedirs(os.path.dirname(clean), exist_ok=True)
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-ac", "1", "-ar", "48000", "-af",
         "highpass=f=80,afftdn=nf=-25,acompressor=threshold=-20dB:ratio=3:attack=10:release=200,loudnorm=I=-18:TP=-2", clean])
    sr, x = wavfile.read(clean)
    x = x.astype(float) / 32768
    hop = int(0.02 * sr)
    rms = np.sqrt(np.convolve(x ** 2, np.ones(hop) / hop, mode="same"))[::hop]
    thr = max(np.percentile(rms, 20) * 3, rms.max() * 0.04)
    voiced = rms > thr
    # voiced regions, bridging pauses shorter than 0.35 s (breaths inside a line)
    regs, i = [], 0
    while i < len(voiced):
        if voiced[i]:
            j = i
            while j < len(voiced) and voiced[j]:
                j += 1
            if regs and (i - regs[-1][1]) * 0.02 < 0.35:
                regs[-1][1] = j
            else:
                regs.append([i, j])
            i = j
        else:
            i += 1
    regs = [g for g in regs if (g[1] - g[0]) * 0.02 > 0.25]  # drop clicks
    n = len(items)
    while len(regs) > n:  # merge across the shortest pause until one region per line
        k = min(range(len(regs) - 1), key=lambda k: regs[k + 1][0] - regs[k][1])
        regs[k:k + 2] = [[regs[k][0], regs[k + 1][1]]]
    if len(regs) < n:
        sys.exit(f"heard {len(regs)} lines but the script has {n}: please re-record with a clear ~1 s pause between lines")
    durs = []
    for k, (a, b) in enumerate(regs):
        a, b = max(0, a * hop - int(0.08 * sr)), min(len(x), b * hop + int(0.12 * sr))
        seg = x[a:b] * np.clip(np.minimum(np.arange(b - a), np.arange(b - a)[::-1]) / (0.01 * sr), 0, 1)
        wavfile.write(os.path.join(out, f"l{k}.wav"), sr, (seg * 32767).astype(np.int16))
        durs.append(round((b - a) / sr, 3))
    write_timing(d, r, items, durs, voice="owner")


# ---------------------------------------------------------------- soundtrack
def step_sound(d, r):
    import numpy as np
    from scipy.io import wavfile
    from scipy.signal import resample_poly
    from music import bansuri, pad, santoor_run
    from sfx import (SR, bandpass, drone, ghanti_scatter, highpass, om_choir, place, reverb, t_axis,
                     tanpura_bed, temple_bell)

    T_ = json.load(open(os.path.join(d, "timing.json")))
    scale = RAGAS[r.get("raga", "shivaranjani")]
    rng = np.random.default_rng(zlib.crc32(r["slug"].encode()))
    notes = sorted(set([s - 12 for s in scale if s >= 7] + scale + [12 + s for s in scale if s <= 4]))

    def phrase(t0, span):
        """A slow, singing bansuri phrase: stepwise motion, last note long, resolving to Sa or Pa."""
        out, t, i = [], t0, notes.index(0) + int(rng.integers(0, 3))
        while t < t0 + span - 1.6:
            ln = float(rng.choice([0.7, 0.9, 1.1, 1.4]))
            out.append((round(t, 2), notes[i], ln))
            t += ln + 0.1
            i = int(np.clip(i + rng.choice([-1, 1, 1, 2, -2]), 0, len(notes) - 1))
        out.append((round(t, 2), int(rng.choice([0, 7])), max(1.2, t0 + span - t)))
        return out

    flute = phrase(0.6, T_["img0"] - 0.6)
    for s, seg in T_["segments"]:
        flute += phrase(s + 0.6, seg - 0.8)
    flute += [(T_["end"] + 0.3, scale[2], 0.6), (T_["end"] + 0.9, scale[1], 0.6), (T_["end"] + 1.5, 0, 1.4)]

    def load_voice(path):
        sr, x = wavfile.read(path)
        x = x.astype(float) / 32768
        x = resample_poly(x if x.ndim == 1 else x.mean(axis=1), SR, sr)
        x = highpass(x, 75)
        x = x + 0.25 * bandpass(x, 150, 350) - 0.25 * bandpass(x, 5500, 8500)
        x = reverb(x, seconds=1.2, wet=0.12)
        return x / np.abs(x).max()

    def mixdown(voice_only):
        dur = T_["dur"]
        n = int(dur * SR)
        music = np.zeros((n + SR * 8, 2))
        T = np.arange(music.shape[0] + SR * 2) / SR
        tp = tanpura_bed(dur + 1)
        place(music, tp * np.clip(T[: len(tp)] / 2.0, 0, 1), 0.0, 0.06 if voice_only else 0.12)
        dr = drone(dur + 1)
        place(music, dr * np.clip(T[: len(dr)] / 2.5, 0, 1), 0.0, 0.03 if voice_only else 0.07)
        if not voice_only:
            p = pad(dur + 1)
            place(music, p * np.clip((T[: len(p)] - 1.0) / 3.0, 0, 1), 0.0, 0.09)
            place(music, bansuri(dur, flute), 0.0, 0.30, pan=0.05)
            for k, (s, _) in enumerate(T_["segments"]):
                run_notes = [notes[min(len(notes) - 1, notes.index(0) + k % 3 + j)] for j in range(4)]
                place(music, santoor_run(run_notes, 0.12), s + 0.05, 0.08, pan=[-0.3, 0.3][k % 2])
            if r.get("end_sound", "om") == "om":
                place(music, om_choir(3.0), T_["end"] - 0.2, 0.10)
            else:
                g = ghanti_scatter(2.4, hits=6)
                i = int(T_["end"] * SR)
                music[i:i + len(g)] += g * 0.05
        place(music, temple_bell(587, 4.0), T_["end"], 0.16)
        music[:, 0] = reverb(music[:, 0], seconds=3.5, wet=0.4)
        music[:, 1] = reverb(music[:, 1], seconds=3.5, wet=0.4)
        music = music[:n]
        voice, gate = np.zeros(n), np.zeros(n)
        for ln in T_["lines"]:
            v = load_voice(os.path.join(d, ln["wav"]))
            i = int(ln["start"] * SR)
            m = min(len(v), n - i)
            voice[i:i + m] += v[:m]
            gate[max(0, i - int(0.25 * SR)):i + m + int(0.3 * SR)] = 1.0
        a64 = np.exp(-64 / (0.18 * SR))
        env, acc = np.zeros(n), 0.0
        for k in range(0, n, 64):
            acc = a64 * acc + (1 - a64) * gate[k]
            env[k:k + 64] = acc
        mix = music * (1.0 - (1.0 - 10 ** (-7 / 20)) * env)[:, None] * 0.9 + voice[:, None] * 0.55
        mix *= (np.clip(t_axis(dur) / 0.6, 0, 1) * np.clip((dur - t_axis(dur)) / 1.0, 0, 1))[:, None]
        mix /= max(1.0, np.abs(mix).max() / 0.89)
        return mix

    work = os.path.join(d, ".work")
    os.makedirs(work, exist_ok=True)
    for name, vo in (("full", False), ("voice_only", True)):
        wavfile.write(os.path.join(work, name + ".wav"), SR, (mixdown(vo) * 32767).astype(np.int16))
    # loudness: -14 LUFS for the full mix (gain + gentle limiter, two passes)
    src, dst = os.path.join(work, "full.wav"), os.path.join(d, "project", "assets", "soundtrack.mp3")
    gain = 0.0
    for _ in range(3):
        run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", src, "-af",
             f"volume={gain:.2f}dB,alimiter=limit=0.84:level=false", "-ar", "48000", "-c:a", "libmp3lame", "-b:a", "192k", dst])
        lufs = measure_lufs(dst)
        if abs(lufs + 14) < 0.15:
            break
        gain += -14 - lufs
    print("soundtrack LUFS", lufs)


def measure_lufs(path):
    out = subprocess.run(["ffmpeg", "-hide_banner", "-i", path, "-af", "ebur128", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    summ = out[out.rfind("Summary:"):]
    return float(summ.split("I:")[1].split("LUFS")[0])


# ---------------------------------------------------------------- composition
STAR = ('<svg class="star" viewBox="-10 -10 20 20"><path d="M0,-9 C1,-2 2,-1 9,0 C2,1 1,2 0,9 '
        'C-1,2 -2,1 -9,0 C-2,-1 -1,-2 0,-9Z" fill="#f7c64a" /></svg>')


def e(s):
    return html.escape(s, quote=True)


def words(id_, text, top, extra_cls=""):
    """Caption words as spans for the word-by-word reveal; *word* is highlighted in gold."""
    ws = "".join(f'<span class="w hl">{e(w.replace("*", ""))}</span>' if "*" in w else f'<span class="w">{e(w)}</span>'
                 for w in text.split())
    return f'<div id="{id_}" class="cap {extra_cls}" style="top: {top}px">{ws}</div>'


def end_note(photos):
    att = [f'{p["author"]} ({p["license"]})' for p in photos if not p["license"].lower().startswith(("public domain", "cc0"))]
    return "Images via Wikimedia Commons · public domain" + (" · " + ", ".join(att) if att else "")


def build_html(r, T_, photos):
    css = open(os.path.join(KIT, "style.css")).read()
    n = len(photos)
    imgs = "\n".join(
        f'        <div class="ph" id="ph{k + 1}"><img id="img{k + 1}" src="assets/{p["file"]}" alt="{e(p["alt"])}" '
        f'data-layout-allow-overflow style="object-position: {p["focus"]}" /></div>' for k, p in enumerate(photos))
    L = T_["lines"]
    secs = []
    for i, (s, seg) in enumerate(T_["segments"], 1):
        top = 900 if len(L[i]["caption"]) < 34 else 860
        secs.append(f'''      <section id="s{i}" class="clip full" data-start="{s}" data-duration="{round(seg + 0.2, 2)}" data-track-index="3">
        {words(f"cap{i}", L[i]["caption"], top)}
      </section>''')
    vo = [[l["start"], l["dur"], len(l["caption"].split())] for l in L]
    return f"""<!doctype html>
<html lang="hi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>{e(r["title"])}</title>
    <script src="assets/gsap.min.js"></script>
    <style>
{css}    </style>
  </head>
  <body>
    <!-- generated by reel_kit/kit.py from reel.json, photos.json and timing.json; edit those -->
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{T_["dur"]}">
      <div id="photos">
{imgs}
      </div>
      <audio id="score" src="assets/soundtrack.mp3" data-start="0" data-duration="{T_["dur"]}" data-track-index="5" data-volume="1"></audio>

      <div id="look" class="clip full" data-start="0" data-duration="{T_["dur"]}" data-track-index="1">
        <div id="grade" class="full"></div>
        <div id="center-dim" class="full"></div>
        <div id="embers" class="full"></div>
        <div id="vignette" class="full"></div>
        <div id="grain"></div>
      </div>

      <div id="overlay" class="clip full" data-start="0" data-duration="{T_["dur"]}" data-track-index="2">
        <div id="wm"><span>NIRVANA</span>{STAR}<span>NILAY</span></div>
      </div>

      <section id="intro" class="clip full" data-start="0" data-duration="{T_["img0"] + 0.2}" data-track-index="3">
        {words("cap0", L[0]["caption"], 820 if r.get("hook_style", "bold") == "bold" else 880, "hook" if r.get("hook_style", "bold") == "bold" else "intro")}
      </section>
{chr(10).join(secs)}

      <section id="ending" class="clip full" data-start="{T_["end"]}" data-duration="{round(T_["dur"] - T_["end"], 2)}" data-track-index="4">
        <div id="end-deva">{e(L[-1]["caption"])}</div>
        <div id="end-handle">{HANDLE}</div>
        <div id="end-follow">FOLLOW FOR MORE {STAR}</div>
        <div id="end-note">{e(end_note(photos))}</div>
      </section>

      <div id="black"></div>
    </div>

    <script>
      const DUR = {T_["dur"]}, IMG0 = {T_["img0"]}, IMG_START = {T_.get("img_start", T_["img0"])}, END = {T_["end"]}, NPH = {n};
      const IMG_T = {json.dumps(T_["img_times"])};  // start time of each image
      // narration: [start, duration, words] per spoken line; segments: [start, length]
      const VO = {json.dumps(vo)};
      const SEG = {json.dumps(T_["segments"])};

      let seed = {zlib.crc32(r["slug"].encode()) % 100000 + 1};
      const rand = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;

      const embers = document.getElementById("embers");
      const EMBERS = [];
      for (let i = 0; i < 26; i++) {{
        const el = document.createElement("div");
        el.className = "ember";
        const s = 0.5 + rand() * 1.2;
        el.style.left = (rand() * 1060).toFixed(0) + "px";
        el.style.top = (900 + rand() * 1100).toFixed(0) + "px";
        el.style.width = el.style.height = (7 * s).toFixed(1) + "px";
        embers.appendChild(el);
        EMBERS.push({{ el, rise: 300 + rand() * 500, sway: 20 + rand() * 50, peak: 0.3 + rand() * 0.4 }});
      }}

      const tl = gsap.timeline({{ paused: true }});
      tl.fromTo("#black", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.4, ease: "none" }}, 0);
      tl.to("#black", {{ opacity: 1, duration: 0.9, ease: "none" }}, DUR - 0.9);
      for (let t = 0; t < DUR; t += 1 / 15) {{
        tl.set("#grain", {{ x: Math.round(rand() * 200 - 100), y: Math.round(rand() * 200 - 100) }}, t);
      }}
      EMBERS.forEach((p, i) => {{
        tl.fromTo(p.el, {{ y: 0, x: 0 }}, {{ y: -p.rise * 2, x: (i % 2 ? 1 : -1) * p.sway, duration: DUR - IMG0, ease: "none" }}, IMG0);
        tl.fromTo(p.el, {{ opacity: 0 }}, {{ opacity: p.peak, duration: 1.0 }}, IMG0 + (i % 5) * 0.15);
        tl.to(p.el, {{ opacity: p.peak * 0.3, duration: 1.2, yoyo: true, repeat: Math.max(1, Math.floor((DUR - IMG0) / 2.4) - 1), ease: "sine.inOut" }}, IMG0 + 1.2 + (i % 6) * 0.3);
      }});

      const reveal = (sel, [t0, len, nw]) => {{
        tl.fromTo(`${{sel}} .w`, {{ opacity: 0, y: 8, filter: "blur(6px)" }},
          {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.45, stagger: (len * 0.92) / nw, ease: "power2.out" }}, t0 - 0.05);
      }};
      reveal("#cap0", VO[0]);
      tl.to("#cap0", {{ opacity: 0, duration: 0.5, ease: "power1.in" }}, IMG0 - 0.55);

      for (let k = 0; k < NPH; k++) {{
        const t0 = IMG_T[k];
        const len = (k === NPH - 1 ? DUR : IMG_T[k + 1]) - t0;
        const dir = k % 2 ? 1 : -1;
        const tin = Math.max(0, t0 - 0.45);
        tl.fromTo(`#ph${{k + 1}}`, {{ opacity: 0 }}, {{ opacity: 1, duration: k === 0 ? (IMG_START === 0 ? 0.4 : 1.0) : 0.9, ease: "sine.inOut" }}, tin);
        tl.fromTo(`#img${{k + 1}}`, {{ scale: 1.04, x: -dir * 14, y: 0 }}, {{ scale: 1.16, x: dir * 14, y: -18, duration: len + 0.9, ease: "none" }}, tin);
        if (k > 0) tl.set(`#ph${{k}}`, {{ opacity: 0 }}, t0 + 0.5);
      }}

      tl.fromTo("#center-dim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8 }}, IMG_START === 0 ? 0 : IMG0 - 0.2);
      tl.to("#center-dim", {{ opacity: 0, duration: 0.6 }}, END - 0.4);
      SEG.forEach(([s, len], i) => {{
        reveal(`#cap${{i + 1}}`, VO[i + 1]);
        tl.to(`#cap${{i + 1}}`, {{ opacity: 0, duration: 0.45, ease: "power1.in" }}, s + len - 0.5);
      }});

      tl.fromTo("#wm", {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.8 }}, 0.5);

      tl.to("#photos", {{ filter: "blur(8px) brightness(0.55)", duration: 0.9, ease: "power2.inOut" }}, END - 0.3);
      tl.fromTo("#end-deva", {{ opacity: 0, scale: 1.08, y: 20 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.9, ease: "power3.out" }}, VO[VO.length - 1][0] - 0.2);
      tl.fromTo("#end-handle", {{ opacity: 0, y: 14 }}, {{ opacity: 1, y: 0, duration: 0.6, ease: "power2.out" }}, VO[VO.length - 1][0] + 0.6);
      tl.fromTo("#end-follow", {{ opacity: 0 }}, {{ opacity: 0.9, duration: 0.6 }}, VO[VO.length - 1][0] + 0.9);
      tl.fromTo("#end-note", {{ opacity: 0 }}, {{ opacity: 0.7, duration: 0.6 }}, VO[VO.length - 1][0] + 1.0);

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def build_credits(r, photos):
    lines = [f"# Credits: {r['title']}", "",
             "All paintings come from [Wikimedia Commons](https://commons.wikimedia.org/), used under the licences below "
             "(read from the Commons API). In the video they are cropped to 9:16, colour-graded and animated, with captions on top. "
             "CC BY / CC BY-SA works are also credited in the closing note on screen.", "",
             "| # | Painting | Author | Licence | Asset |", "|---|---|---|---|---|"]
    lines += [f"| {k + 1} | [{p['title'][5:]}]({p['page']}) | {p['author']} | {p['license']} | `{p['file']}` |" for k, p in enumerate(photos)]
    lines += ["", "Original files:", ""] + [f"{k + 1}. {p['original']}" for k, p in enumerate(photos)]
    lines += ["", "Narration: Piper TTS voice hi_IN-pratham-medium (dataset CC BY-NC-SA 4.0, non-commercial use).",
              "Music: original synthesised score (reel_kit/kit.py with ../music.py and ../sfx.py), Raga " + r.get("raga", "shivaranjani").title() + ".",
              "Fonts: Tiro Devanagari Sanskrit and Cinzel (SIL Open Font License). GSAP vendored.", ""]
    return "\n".join(lines)


def build_readme(r, T_):
    rows = [f"| {l['start']:.1f} s | {l['caption']} |" for l in T_["lines"]]
    return "\n".join([
        f"# {r['title']}", "",
        f"Reel for Instagram ({HANDLE}): {T_['dur']} s, 1080x1920, 30 fps, -14 LUFS. Built with `reel_kit/kit.py` from `reel.json`.", "",
        "- `output/reel.mp4`: narration + original score.",
        "- `output/reel_voice_only.mp4`: narration only, to add a song from Instagram's music library (song ~30–40%, original audio 100%).", "",
        "| Voice starts | Caption |", "|---|---|", *rows, "",
        "## Post", "", r.get("caption_post", ""), "",
        "Paintings and licences: [CREDITS.md](CREDITS.md). Rebuild: `python3 reel_kit/kit.py " + os.path.relpath(r["_dir"], ROOT) + " all` from `shivji_edit/`.", ""])


def step_build(d, r):
    T_ = json.load(open(os.path.join(d, "timing.json")))
    photos = json.load(open(os.path.join(d, "photos.json")))
    r["_dir"] = d
    with open(os.path.join(d, "project", "index.html"), "w") as f:
        f.write(build_html(r, T_, photos))
    with open(os.path.join(d, "CREDITS.md"), "w") as f:
        f.write(build_credits(r, photos))
    with open(os.path.join(d, "README.md"), "w") as f:
        f.write(build_readme(r, T_))


# ---------------------------------------------------------------- render
def step_render(d, r):
    env = dict(os.environ, HYPERFRAMES_BROWSER_PATH=CHROME[-1]) if CHROME else os.environ
    proj, out, work = os.path.join(d, "project"), os.path.join(d, "output"), os.path.join(d, ".work")
    os.makedirs(out, exist_ok=True)
    chk = subprocess.run(["npx", "-y", "hyperframes@0.8.184", "check"], cwd=proj, env=env, capture_output=True, text=True)
    tail = [l for l in (chk.stdout + chk.stderr).splitlines() if "error(s)" in l or "Check" in l or "✗" in l]
    print("\n".join(tail))
    if "Check passed" not in chk.stdout + chk.stderr:
        sys.exit("hyperframes check failed")
    master = os.path.join(work, "master.mp4")
    run(["npx", "-y", "hyperframes@0.8.184", "render", "--quality", "delivery", "--fps", "30", "--output", master],
        cwd=proj, env=env, stdout=subprocess.DEVNULL)
    final, vo = os.path.join(out, "reel.mp4"), os.path.join(out, "reel_voice_only.mp4")
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", master, "-c:v", "libx264", "-preset", "slow", "-crf", "20",
         "-tune", "film", "-pix_fmt", "yuv420p", "-profile:v", "high", "-movflags", "+faststart", "-c:a", "copy", final])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", os.path.join(work, "voice_only.wav"), "-af",
         "loudnorm=I=-16:TP=-1.5", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", os.path.join(work, "vo.m4a")])
    run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", final, "-i", os.path.join(work, "vo.m4a"),
         "-map", "0:v", "-map", "1:a", "-c", "copy", "-movflags", "+faststart", vo])
    for f in (final, vo):
        info = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "stream=width,height,r_frame_rate:format=duration",
                               "-of", "csv=p=0", f], capture_output=True, text=True).stdout.split()
        print(os.path.basename(f), info, "LUFS", measure_lufs(f), f"{os.path.getsize(f) / 1e6:.1f} MB")


def scaffold(d):
    proj = os.path.join(d, "project")
    os.makedirs(os.path.join(proj, "assets"), exist_ok=True)
    for f in glob.glob(os.path.join(KIT, "assets", "*")):
        dst = os.path.join(proj, "assets", os.path.basename(f))
        if not os.path.exists(dst):
            shutil.copy(f, dst)
    slug = load(d)["slug"]
    for name, body in (("hyperframes.json", open(os.path.join(KIT, "hyperframes.json")).read()),
                       ("meta.json", json.dumps({"id": slug, "name": slug}, indent=2) + "\n")):
        with open(os.path.join(proj, name), "w") as f:
            f.write(body)


STEPS = {"fetch": step_fetch, "assemble": step_assemble, "narrate": step_narrate, "sound": step_sound,
         "build": step_build, "render": step_render}  # plus: myvoice RECORDING (replaces narrate)


def main():
    d = os.path.abspath(sys.argv[1])
    steps = sys.argv[2:] or ["all"]
    if steps == ["all"]:
        steps = list(STEPS)
    scaffold(d)
    r = load(d)
    if steps[0] == "myvoice":
        step_myvoice(d, r, os.path.abspath(steps[1]))
        steps = steps[2:]
    for s in steps:
        print(f"== {s}", flush=True)
        STEPS[s](d, r)


if __name__ == "__main__":
    main()
