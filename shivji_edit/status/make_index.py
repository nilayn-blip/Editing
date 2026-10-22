"""Build project/index.html and CREDITS.md for the Mahadev status reel from photos.json.

Format of a "Mahadev status" short: a black quote card, then moody Shiva paintings with slow push-ins and
soft dissolves, and one small centred serif quote building word by word ("mila to unki kripa, nahi mila
to unki ichchha"), ending on ॥ हर हर महादेव ॥. The paintings are public domain / CC0 (Wikimedia Commons).

Usage: python3 make_index.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Output times; keep in sync with soundtrack.py
DUR = 24.5
IMG0, IMG_LEN = 3.0, 3.2
END = 22.2
CAPTIONS = (3.0, 9.4, 15.8)

INTRO = "Life gets a lot easier when you realise…"
# (Hinglish line as in the reference, Devanagari line)
LINES = [
    ("mila to unki kripa,", "मिला तो उनकी कृपा,"),
    ("nahi mila to unki ichchha ”", "नहीं मिला तो उनकी इच्छा"),
    ("bas bharosa rakho, Mahadev sab dekh rahe hain ”", "बस भरोसा रखो, महादेव सब देख रहे हैं"),
]

STAR = ('<svg class="star" viewBox="-10 -10 20 20"><path d="M0,-9 C1,-2 2,-1 9,0 C2,1 1,2 0,9 '
        'C-1,2 -2,1 -9,0 C-2,-1 -1,-2 0,-9Z" fill="#f7c64a" /></svg>')

CSS = """
      @font-face {
        font-family: "Tiro Devanagari Sanskrit";
        src: url("assets/TiroDevanagariSanskrit-Regular.ttf") format("truetype");
      }
      @font-face {
        font-family: "Cinzel";
        src: url("assets/Cinzel.ttf") format("truetype");
        font-weight: 400 900;
      }
      * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
      }
      html,
      body {
        width: 1080px;
        height: 1920px;
        overflow: hidden;
        background: #000;
      }
      #root {
        position: relative;
        width: 100%;
        height: 100%;
        overflow: hidden;
        background: #000;
      }
      .full {
        position: absolute;
        inset: 0;
      }

      /* paintings: full-bleed, cover, slow push-in */
      #photos {
        position: absolute;
        inset: 0;
        overflow: hidden;
      }
      .ph {
        position: absolute;
        inset: 0;
        overflow: hidden;
        opacity: 0;
      }
      .ph img {
        position: absolute;
        inset: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        filter: brightness(0.78) contrast(1.12) saturate(1.08);
      }

      /* moody grade */
      #grade {
        background: linear-gradient(180deg, rgba(20, 10, 40, 0.35) 0%, rgba(0, 0, 0, 0) 40%, rgba(60, 20, 0, 0.3) 100%);
        mix-blend-mode: multiply;
      }
      #center-dim {
        background: radial-gradient(ellipse 90% 16% at 50% 50%, rgba(0, 0, 0, 0.5) 0%, rgba(0, 0, 0, 0) 100%);
        opacity: 0;
      }
      #vignette {
        background: radial-gradient(ellipse 85% 70% at 50% 48%, rgba(0, 0, 0, 0) 50%, rgba(0, 0, 0, 0.8) 100%);
      }
      #grain {
        position: absolute;
        inset: -120px;
        background: url("assets/grain.png");
        mix-blend-mode: overlay;
        opacity: 0.1;
      }
      .ember {
        position: absolute;
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background: radial-gradient(circle, #fff8dc 0%, #ffd27a 35%, rgba(255, 170, 60, 0) 70%);
        opacity: 0;
      }

      /* captions: small centred serif, like the reference */
      .cap {
        position: absolute;
        left: 60px;
        right: 60px;
        display: flex;
        flex-wrap: wrap;
        justify-content: center;
        gap: 0 14px;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 44px;
        line-height: 1.35;
        color: #fbf6ec;
        text-align: center;
        text-shadow: 0 2px 8px rgba(0, 0, 0, 0.95), 0 0 18px rgba(0, 0, 0, 0.7);
      }
      .cap .w {
        opacity: 0;
      }
      .hi {
        position: absolute;
        left: 0;
        right: 0;
        text-align: center;
        font-family: "Tiro Devanagari Sanskrit", serif;
        font-size: 34px;
        line-height: 1.3;
        color: #f2c661;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.95), 0 0 14px rgba(255, 150, 30, 0.45);
        white-space: nowrap;
        opacity: 0;
      }
      #intro-cap {
        top: 922px;
        font-size: 40px;
      }

      /* ending */
      #end-deva {
        position: absolute;
        left: 0;
        right: 0;
        top: 860px;
        text-align: center;
        font-family: "Tiro Devanagari Sanskrit", serif;
        font-size: 104px;
        line-height: 1.25;
        background: linear-gradient(180deg, #fff4c8 0%, #f7c64a 55%, #c4801c 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        filter: drop-shadow(0 4px 6px rgba(20, 6, 0, 0.85)) drop-shadow(0 0 22px rgba(255, 150, 30, 0.6));
        white-space: nowrap;
      }
      #end-note {
        position: absolute;
        left: 0;
        right: 0;
        top: 1500px;
        text-align: center;
        font-family: Georgia, "Times New Roman", serif;
        font-size: 22px;
        color: #e8dcc4;
        opacity: 0.7;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);
      }

      /* watermark */
      #wm {
        position: absolute;
        right: 54px;
        top: 150px;
        display: flex;
        align-items: center;
        gap: 12px;
        font-family: "Cinzel", serif;
        font-size: 30px;
        font-weight: 600;
        letter-spacing: 0.14em;
        color: #ffecbe;
        text-shadow: 0 2px 6px rgba(0, 0, 0, 0.85), 0 0 12px rgba(255, 150, 30, 0.45);
        opacity: 0;
      }
      #wm .star {
        width: 24px;
        height: 24px;
        filter: drop-shadow(0 0 6px rgba(255, 180, 60, 0.9));
      }
      #black {
        position: absolute;
        inset: 0;
        background: #000;
      }
"""


def e(s):
    return html.escape(s, quote=True)


def words(id_, text, top, extra=""):
    ws = "".join(f'<span class="w">{e(w)}</span>' for w in text.split())
    return f'<div id="{id_}" class="cap" style="top: {top}px{extra}">{ws}</div>'


def build_html(photos):
    n = len(photos)
    imgs = "\n".join(
        f'        <div class="ph" id="ph{k + 1}"><img id="img{k + 1}" src="assets/{p["file"]}" alt="{e(p["alt"])}" '
        f'data-layout-allow-overflow style="object-position: {p["focus"]}" /></div>'
        for k, p in enumerate(photos)
    )
    c1, c2, c3 = CAPTIONS
    return f"""<!doctype html>
<html lang="hi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Mahadev Status</title>
    <script src="assets/gsap.min.js"></script>
    <style>{CSS}    </style>
  </head>
  <body>
    <!-- generated by ../make_index.py from ../photos.json; edit there -->
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{DUR}">
      <!-- paintings (public domain / CC0, Wikimedia Commons; see CREDITS.md) -->
      <div id="photos">
{imgs}
      </div>
      <audio id="score" src="assets/soundtrack.mp3" data-start="0" data-duration="{DUR}" data-track-index="5" data-volume="1"></audio>

      <!-- grade, embers, vignette, grain -->
      <div id="look" class="clip full" data-start="0" data-duration="{DUR}" data-track-index="1">
        <div id="grade" class="full"></div>
        <div id="center-dim" class="full"></div>
        <div id="embers" class="full"></div>
        <div id="vignette" class="full"></div>
        <div id="grain"></div>
      </div>

      <!-- watermark -->
      <div id="overlay" class="clip full" data-start="0" data-duration="{DUR}" data-track-index="2">
        <div id="wm"><span>NIRVANA</span>{STAR}<span>NILAY</span></div>
      </div>

      <!-- intro: black quote card -->
      <section id="intro" class="clip full" data-start="0" data-duration="{IMG0 + 0.2}" data-track-index="3">
        {words("intro-cap", INTRO, 922)}
      </section>

      <!-- the quote, building word by word -->
      <section id="quote" class="clip full" data-start="{c1}" data-duration="{round(c3 - c1 + 0.2, 2)}" data-track-index="3">
        {words("cap1", LINES[0][0], 870)}
        {words("cap2", LINES[1][0], 930)}
        <div id="hi12" class="hi" style="top: 1012px">{e(LINES[0][1])} {e(LINES[1][1])}</div>
      </section>
      <section id="quote2" class="clip full" data-start="{c3}" data-duration="{round(END - c3 + 0.2, 2)}" data-track-index="3">
        {words("cap3", LINES[2][0], 900)}
        <div id="hi3" class="hi" style="top: 1012px">{e(LINES[2][1])}</div>
      </section>

      <!-- ending -->
      <section id="ending" class="clip full" data-start="{END}" data-duration="{round(DUR - END, 2)}" data-track-index="4">
        <div id="end-deva">॥ हर हर महादेव ॥</div>
        <div id="end-note">Paintings: public domain · Wikimedia Commons</div>
      </section>

      <div id="black"></div>
    </div>

    <script>
      // Output times; keep in sync with make_index.py and soundtrack.py
      const DUR = {DUR}, IMG0 = {IMG0}, IMG_LEN = {IMG_LEN}, END = {END}, NPH = {n};
      const C1 = {c1}, C2 = {c2}, C3 = {c3};

      // seeded PRNG (determinism: no Math.random)
      let seed = 1008;
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

      // fade in / out
      tl.fromTo("#black", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.4, ease: "none" }}, 0);
      tl.to("#black", {{ opacity: 1, duration: 0.9, ease: "none" }}, DUR - 0.9);

      // film grain
      for (let t = 0; t < DUR; t += 1 / 15) {{
        tl.set("#grain", {{ x: Math.round(rand() * 200 - 100), y: Math.round(rand() * 200 - 100) }}, t);
      }}

      // embers drift up once the paintings start
      EMBERS.forEach((p, i) => {{
        tl.fromTo(p.el, {{ y: 0, x: 0 }}, {{ y: -p.rise * 2, x: (i % 2 ? 1 : -1) * p.sway, duration: DUR - IMG0, ease: "none" }}, IMG0);
        tl.fromTo(p.el, {{ opacity: 0 }}, {{ opacity: p.peak, duration: 1.0 }}, IMG0 + (i % 5) * 0.15);
        tl.to(p.el, {{ opacity: p.peak * 0.3, duration: 1.2, yoyo: true, repeat: 7, ease: "sine.inOut" }}, IMG0 + 1.2 + (i % 6) * 0.3);
      }});

      // word-by-word reveal
      const reveal = (sel, t0, step) => tl.fromTo(`${{sel}} .w`, {{ opacity: 0, y: 8, filter: "blur(6px)" }},
        {{ opacity: 1, y: 0, filter: "blur(0px)", duration: 0.55, stagger: step, ease: "power2.out" }}, t0);

      // intro quote card
      reveal("#intro-cap", 0.35, 0.28);
      tl.to("#intro-cap", {{ opacity: 0, duration: 0.5, ease: "power1.in" }}, IMG0 - 0.55);

      // paintings: slow push-in with a gentle drift, long soft dissolves
      for (let k = 0; k < NPH; k++) {{
        const t0 = IMG0 + k * IMG_LEN;
        const len = k === NPH - 1 ? DUR - t0 : IMG_LEN;
        const dir = k % 2 ? 1 : -1;
        tl.fromTo(`#ph${{k + 1}}`, {{ opacity: 0 }}, {{ opacity: 1, duration: k === 0 ? 1.0 : 0.9, ease: "sine.inOut" }}, t0 - 0.45);
        tl.fromTo(`#img${{k + 1}}`, {{ scale: 1.04, x: -dir * 14, y: 0 }}, {{ scale: 1.16, x: dir * 14, y: -18, duration: len + 0.9, ease: "none" }}, t0 - 0.45);
        if (k > 0) tl.set(`#ph${{k}}`, {{ opacity: 0 }}, t0 + 0.5);
      }}

      // captions
      tl.fromTo("#center-dim", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8 }}, C1 - 0.2);
      tl.to("#center-dim", {{ opacity: 0, duration: 0.6 }}, END - 0.4);
      reveal("#cap1", C1 + 0.4, 0.3);
      reveal("#cap2", C2 + 0.1, 0.3);
      tl.fromTo("#hi12", {{ opacity: 0 }}, {{ opacity: 0.95, duration: 0.8 }}, C2 + 1.8);
      tl.to(["#cap1", "#cap2", "#hi12"], {{ opacity: 0, duration: 0.5, ease: "power1.in" }}, C3 - 0.5);
      reveal("#cap3", C3 + 0.2, 0.26);
      tl.fromTo("#hi3", {{ opacity: 0 }}, {{ opacity: 0.95, duration: 0.8 }}, C3 + 2.4);
      tl.to(["#cap3", "#hi3"], {{ opacity: 0, duration: 0.5, ease: "power1.in" }}, END - 0.5);

      // watermark
      tl.fromTo("#wm", {{ opacity: 0 }}, {{ opacity: 0.8, duration: 0.8 }}, 0.5);

      // ending
      tl.to("#photos", {{ filter: "blur(8px) brightness(0.6)", duration: 0.9, ease: "power2.inOut" }}, END - 0.3);
      tl.fromTo("#end-deva", {{ opacity: 0, scale: 1.08, y: 20 }}, {{ opacity: 1, scale: 1, y: 0, duration: 0.9, ease: "power3.out" }}, END + 0.1);
      tl.fromTo("#end-note", {{ opacity: 0 }}, {{ opacity: 0.7, duration: 0.6 }}, END + 0.6);

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def build_credits(photos):
    lines = [
        "# Credits: Mahadev status reel",
        "",
        "All paintings come from [Wikimedia Commons](https://commons.wikimedia.org/) and are public domain or CC0, as read",
        "from the Commons API, so no attribution is legally required. They are credited here anyway. In the video they are",
        "cropped to 9:16, colour-graded and animated, with captions on top.",
        "",
        "| # | Painting | Author | Licence | Asset |",
        "|---|---|---|---|---|",
    ]
    for k, p in enumerate(photos):
        lines.append(f"| {k + 1} | [{p['title'][5:]}]({p['page']}) | {p['author']} | {p['license']} | `{p['file']}` |")
    lines += ["", "Original files:", ""]
    lines += [f"{k + 1}. {p['original']}" for k, p in enumerate(photos)]
    lines += [
        "",
        "The quote \"mila to unki kripa, nahi mila to unki ichchha\" is a traditional Hindi saying. The other caption",
        "lines are original. The music is an original synthesised score (`soundtrack.py`, using `../music.py` and `../sfx.py`).",
        "The fonts, Tiro Devanagari Sanskrit and Cinzel, are under the SIL Open Font License. GSAP is vendored from the earlier Mahakal project.",
        "",
    ]
    return "\n".join(lines)


def main():
    photos = json.load(open(os.path.join(HERE, "photos.json")))
    with open(os.path.join(HERE, "project", "index.html"), "w") as f:
        f.write(build_html(photos))
    with open(os.path.join(HERE, "CREDITS.md"), "w") as f:
        f.write(build_credits(photos))


if __name__ == "__main__":
    main()
