"""Build project/index.html and CREDITS.md for the Dwadash Jyotirlinga edit from photos.json.

photos.json lists one Wikimedia Commons photo per temple (title, author, licence, URLs, focal point),
so the on-screen credits card and CREDITS.md always match the files in project/assets/.

Usage: python3 make_index.py
"""
import html
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

# Output times; keep in sync with soundtrack.py
DUR = 55.5
BEAT0, BEAT_LEN, N = 3.2, 3.6, 12
OUTRO = BEAT0 + N * BEAT_LEN  # 46.4
CREDITS = 50.6

DEVA_NUM = "१ २ ३ ४ ५ ६ ७ ८ ९ १० ११ १२".split()

# (Devanagari name, Latin name, place, line of the Dwadash Jyotirlinga Stotram)
TEMPLES = [
    ("सोमनाथ", "SOMNATH", "PRABHAS PATAN · GUJARAT", "सौराष्ट्रे सोमनाथं च"),
    ("मल्लिकार्जुन", "MALLIKARJUNA", "SRISAILAM · ANDHRA PRADESH", "श्रीशैले मल्लिकार्जुनम्"),
    ("महाकालेश्वर", "MAHAKALESHWAR", "UJJAIN · MADHYA PRADESH", "उज्जयिन्यां महाकालम्"),
    ("ओंकारेश्वर", "OMKARESHWAR", "KHANDWA · MADHYA PRADESH", "ओङ्कारममलेश्वरम्"),
    ("केदारनाथ", "KEDARNATH", "RUDRAPRAYAG · UTTARAKHAND", "हिमालये तु केदारम्"),
    ("भीमाशंकर", "BHIMASHANKAR", "PUNE · MAHARASHTRA", "डाकिन्यां भीमशङ्करम्"),
    ("काशी विश्वनाथ", "KASHI VISHWANATH", "VARANASI · UTTAR PRADESH", "वाराणस्यां तु विश्वेशम्"),
    ("त्र्यंबकेश्वर", "TRIMBAKESHWAR", "NASHIK · MAHARASHTRA", "त्र्यम्बकं गौतमीतटे"),
    ("बैद्यनाथ", "BAIDYANATH", "DEOGHAR · JHARKHAND", "श्रीवैद्यनाथं तमहं नमामि"),
    ("नागेश्वर", "NAGESHWAR", "DWARKA · GUJARAT", "नागेशं दारुकावने"),
    ("रामेश्वरम्", "RAMESHWARAM", "RAMANATHASWAMY · TAMIL NADU", "सेतुबन्धे तु रामेशम्"),
    ("घृष्णेश्वर", "GRISHNESHWAR", "ELLORA · MAHARASHTRA", "घुश्मेशं च शिवालये"),
]

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
        background: #0a0300;
        --gold-1: #fff4c8;
        --gold-2: #f7c64a;
        --gold-3: #c4801c;
        --cream: #ffecbe;
      }
      .full {
        position: absolute;
        inset: 0;
      }

      /* photos: full-bleed, cover, Ken Burns on the img */
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
      }

      /* type */
      .deva {
        font-family: "Tiro Devanagari Sanskrit", serif;
        line-height: 1.25;
        background: linear-gradient(180deg, var(--gold-1) 0%, var(--gold-2) 55%, var(--gold-3) 100%);
        -webkit-background-clip: text;
        background-clip: text;
        color: transparent;
        filter: drop-shadow(0 4px 6px rgba(20, 6, 0, 0.8)) drop-shadow(0 0 22px rgba(255, 150, 30, 0.55));
        white-space: nowrap;
      }
      .latin {
        font-family: "Cinzel", serif;
        color: var(--cream);
        letter-spacing: 0.24em;
        text-shadow: 0 2px 6px rgba(20, 6, 0, 0.9), 0 0 14px rgba(255, 150, 30, 0.5);
        white-space: nowrap;
      }
      .stack {
        position: absolute;
        left: 0;
        right: 0;
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
      }
      .rule {
        position: relative;
        width: 560px;
        height: 24px;
        margin: 6px 0 10px;
      }
      .rule .line {
        position: absolute;
        left: 0;
        right: 0;
        top: 11px;
        height: 2px;
        background: linear-gradient(90deg, transparent, var(--gold-2) 20%, var(--gold-2) 80%, transparent);
        box-shadow: 0 0 8px rgba(255, 170, 40, 0.8);
      }
      .rule .gem {
        position: absolute;
        left: 270px;
        top: 2px;
        width: 20px;
        height: 20px;
        background: var(--gold-2);
        clip-path: polygon(50% 0, 100% 50%, 50% 100%, 0 50%);
        box-shadow: 0 0 10px rgba(255, 170, 40, 0.9);
      }
      .band-top {
        position: absolute;
        left: 0;
        right: 0;
        top: 0;
        height: 620px;
        background: linear-gradient(180deg, rgba(18, 6, 0, 0.8) 0%, rgba(18, 6, 0, 0.45) 50%, rgba(18, 6, 0, 0) 100%);
      }
      .band-bottom {
        position: absolute;
        left: 0;
        right: 0;
        bottom: 0;
        height: 1020px;
        background: linear-gradient(0deg, rgba(18, 6, 0, 0.92) 0%, rgba(18, 6, 0, 0.78) 38%, rgba(18, 6, 0, 0.35) 70%, rgba(18, 6, 0, 0) 100%);
      }

      /* light */
      #rays {
        position: absolute;
        left: -660px;
        top: -1260px;
        width: 2400px;
        height: 2400px;
        border-radius: 50%;
        background: repeating-conic-gradient(
          from 0deg,
          rgba(255, 214, 140, 0.55) 0deg 3deg,
          rgba(255, 214, 140, 0) 6deg 16deg
        );
        -webkit-mask-image: radial-gradient(circle, #000 0%, rgba(0, 0, 0, 0.6) 35%, transparent 70%);
        mask-image: radial-gradient(circle, #000 0%, rgba(0, 0, 0, 0.6) 35%, transparent 70%);
        filter: blur(14px);
        mix-blend-mode: screen;
        opacity: 0;
      }
      .leak {
        position: absolute;
        inset: -200px;
        mix-blend-mode: screen;
        opacity: 0;
      }
      #leak-l {
        background: radial-gradient(ellipse 60% 45% at 25% 40%, rgba(255, 214, 140, 1) 0%, rgba(255, 160, 60, 0.6) 40%, rgba(255, 120, 30, 0) 75%);
      }
      #leak-r {
        background: radial-gradient(ellipse 60% 45% at 75% 55%, rgba(255, 220, 150, 1) 0%, rgba(255, 150, 50, 0.6) 40%, rgba(255, 110, 20, 0) 75%);
      }
      .ember {
        position: absolute;
        width: 10px;
        height: 10px;
        border-radius: 50%;
        background: radial-gradient(circle, #fff8dc 0%, #ffd27a 35%, rgba(255, 170, 60, 0) 70%);
        opacity: 0;
      }

      /* persistent ring of 12 lights */
      #ring {
        position: absolute;
        left: 400px;
        top: 70px;
        width: 280px;
        height: 280px;
        overflow: visible;
      }

      /* intro */
      #intro-stack {
        top: 760px;
      }
      #intro-deva {
        font-size: 104px;
      }
      #intro-l1 {
        font-size: 38px;
        letter-spacing: 0.16em;
      }

      /* temple beats */
      .beat .badge {
        position: absolute;
        left: 470px;
        top: 1080px;
        width: 140px;
        height: 140px;
      }
      .beat .stack {
        top: 1236px;
      }
      .beat .stotra {
        font-size: 50px;
        opacity: 0.92;
      }
      .beat .name {
        font-size: 124px;
        margin-top: 2px;
      }
      .beat .latin.en {
        font-size: 46px;
        letter-spacing: 0.2em;
      }
      .beat .latin.place {
        font-size: 28px;
        letter-spacing: 0.22em;
        margin-top: 14px;
        opacity: 0.88;
      }

      /* outro */
      #outro-stack {
        top: 1150px;
      }
      #outro-deva {
        font-size: 112px;
      }
      #outro-l1 {
        font-size: 36px;
        letter-spacing: 0.18em;
      }

      /* credits card */
      #credits-stack {
        top: 560px;
      }
      #credits-stack .head {
        font-size: 34px;
        letter-spacing: 0.2em;
        margin-bottom: 8px;
      }
      #credits-stack .sub {
        font-size: 22px;
        letter-spacing: 0.12em;
        opacity: 0.8;
        margin-bottom: 26px;
      }
      #credits-stack .cr {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 25px;
        line-height: 1.62;
        color: var(--cream);
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9);
        white-space: nowrap;
      }
      #credits-stack .cr b {
        font-family: "Cinzel", serif;
        font-weight: 700;
        color: var(--gold-2);
        letter-spacing: 0.08em;
      }
      #credits-stack .cr i {
        color: #e9d39a;
        opacity: 0.85;
      }
      #credits-stack .foot {
        font-family: Georgia, "Times New Roman", serif;
        font-size: 21px;
        line-height: 1.5;
        color: var(--cream);
        opacity: 0.75;
        margin-top: 24px;
        white-space: nowrap;
      }
      #black {
        position: absolute;
        inset: 0;
        background: #000;
      }
"""


def e(s):
    return html.escape(s, quote=True)


def short_licence(lic):
    return lic.replace("Public domain", "Public Domain")


def build_html(photos):
    beats_t = [round(BEAT0 + k * BEAT_LEN, 3) for k in range(N)]
    imgs, sections, credits = [], [], []
    for k, (deva, en, place, stotra) in enumerate(TEMPLES):
        p = photos[k]
        imgs.append(
            f'        <div class="ph" id="ph{k + 1}"><img id="img{k + 1}" src="assets/{p["file"]}" '
            f'alt="{e(p["alt"])}" data-layout-allow-overflow style="object-position: {p["focus"]}" /></div>'
        )
        sections.append(f"""
      <!-- {k + 1}. {en.title()} -->
      <section id="b{k + 1}" class="clip full beat" data-start="{beats_t[k]}" data-duration="{BEAT_LEN}" data-track-index="3">
        <svg class="badge" viewBox="-70 -70 140 140">
          <circle r="62" fill="#1a0a02" fill-opacity="0.72" stroke="#f7c64a" stroke-width="3" />
          <circle r="53" fill="none" stroke="#f7c64a" stroke-width="1" opacity="0.6" />
          <text x="0" y="{18 if k < 9 else 16}" text-anchor="middle" font-family="Tiro Devanagari Sanskrit" font-size="{60 if k < 9 else 50}" fill="#ffe6a0">{DEVA_NUM[k]}</text>
        </svg>
        <div class="stack">
          <div class="deva stotra">{e(stotra)}</div>
          <div class="deva name">{e(deva)}</div>
          <div class="rule"><div class="line"></div><div class="gem"></div></div>
          <div class="latin en">{e(en)}</div>
          <div class="latin place">{e(place)}</div>
        </div>
      </section>""")
        credits.append(
            f'          <div class="cr"><b>{k + 1}. {e(en.title())}</b> — {e(p["author"])} · <i>{e(short_licence(p["license"]))}</i></div>'
        )

    return f"""<!doctype html>
<html lang="hi">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1080, height=1920" />
    <title>Dwadash Jyotirlinga</title>
    <script src="assets/gsap.min.js"></script>
    <style>{CSS}    </style>
  </head>
  <body>
    <!-- generated by ../make_index.py from ../photos.json; edit there -->
    <div id="root" data-composition-id="main" data-start="0" data-width="1080" data-height="1920" data-duration="{DUR}">
      <!-- photos (Wikimedia Commons, see CREDITS.md); wrapper is untimed so it can be blurred for the outro -->
      <div id="photos">
{chr(10).join(imgs)}
      </div>
      <audio id="score" src="assets/soundtrack.mp3" data-start="0" data-duration="{DUR}" data-track-index="5" data-volume="1"></audio>

      <!-- legibility bands, light leaks, god-rays, embers -->
      <div id="light" class="clip full" data-start="0" data-duration="{DUR}" data-track-index="1">
        <div id="band-top" class="band-top"></div>
        <div id="band-bottom" class="band-bottom"></div>
        <div id="rays"></div>
        <div id="leak-l" class="leak"></div>
        <div id="leak-r" class="leak"></div>
        <div id="embers" class="full"></div>
      </div>

      <!-- persistent ring of 12 lights, one lit per temple -->
      <div id="ring-layer" class="clip full" data-start="0" data-duration="{DUR}" data-track-index="2">
        <svg id="ring" viewBox="-140 -140 280 280">
          <defs>
            <filter id="glow" x="-1" y="-1" width="3" height="3"><feGaussianBlur stdDeviation="6" /></filter>
          </defs>
          <g id="ring-spin">
            <circle r="104" fill="none" stroke="#f7c64a" stroke-width="1.5" opacity="0.55" />
            <circle r="84" fill="none" stroke="#f7c64a" stroke-width="0.8" opacity="0.35" />
            <g id="lights"></g>
          </g>
          <text id="ring-om" x="0" y="26" text-anchor="middle" font-family="Tiro Devanagari Sanskrit" font-size="74" fill="#f7c64a">ॐ</text>
        </svg>
      </div>

      <!-- intro -->
      <section id="intro" class="clip full" data-start="0" data-duration="{BEAT0 + 0.2}" data-track-index="3">
        <div id="intro-stack" class="stack">
          <div id="intro-deva" class="deva">॥ द्वादश ज्योतिर्लिंग ॥</div>
          <div id="intro-rule" class="rule"><div class="line"></div><div class="gem"></div></div>
          <div id="intro-l1" class="latin">THE 12 JYOTIRLINGAS OF SHIVA</div>
        </div>
      </section>
{"".join(sections)}

      <!-- outro: all twelve lights, Har Har Mahadev -->
      <section id="outro" class="clip full" data-start="{OUTRO}" data-duration="{round(CREDITS - OUTRO + 0.2, 2)}" data-track-index="4">
        <div id="outro-stack" class="stack">
          <div id="outro-deva" class="deva">॥ हर हर महादेव ॥</div>
          <div id="outro-rule" class="rule"><div class="line"></div><div class="gem"></div></div>
          <div id="outro-l1" class="latin">THE 12 JYOTIRLINGAS OF SHIVA</div>
        </div>
      </section>

      <!-- credits card (required by CC BY / CC BY-SA) -->
      <section id="credits" class="clip full" data-start="{CREDITS}" data-duration="{round(DUR - CREDITS, 2)}" data-track-index="4">
        <div id="credits-stack" class="stack">
          <div class="latin head">PHOTOGRAPHS</div>
          <div class="latin sub">WIKIMEDIA COMMONS · USED UNDER THEIR LICENCES</div>
{chr(10).join(credits)}
          <div class="foot">Photos cropped and animated. Licence texts: creativecommons.org/licenses</div>
          <div class="foot" style="margin-top: 4px">Music: original synthesised score in Raga Shivaranjani</div>
        </div>
      </section>

      <div id="black"></div>
    </div>

    <script>
      // Output times; keep in sync with make_index.py and soundtrack.py
      const DUR = {DUR};
      const BEAT0 = {BEAT0}, BEAT_LEN = {BEAT_LEN}, N = {N};
      const OUTRO = {OUTRO}, CREDITS = {CREDITS};
      const BEATS = Array.from({{ length: N }}, (_, k) => BEAT0 + k * BEAT_LEN);
      const NS = "http://www.w3.org/2000/svg";

      // seeded PRNG (determinism: no Math.random)
      let seed = 1212;
      const rand = () => ((seed = (seed * 16807) % 2147483647) - 1) / 2147483646;

      // build: embers and the 12 ring lights
      const embers = document.getElementById("embers");
      const EMBERS = [];
      for (let i = 0; i < 34; i++) {{
        const el = document.createElement("div");
        el.className = "ember";
        const s = 0.5 + rand() * 1.3;
        el.style.left = (rand() * 1060).toFixed(0) + "px";
        el.style.top = (500 + rand() * 1500).toFixed(0) + "px";
        el.style.width = el.style.height = (8 * s).toFixed(1) + "px";
        embers.appendChild(el);
        EMBERS.push({{ el, rise: 300 + rand() * 600, sway: 20 + rand() * 50, peak: 0.35 + rand() * 0.45 }});
      }}
      const lights = document.getElementById("lights");
      const LIGHTS = [];
      for (let k = 0; k < N; k++) {{
        const ang = (k / N) * Math.PI * 2 - Math.PI / 2;
        const g = document.createElementNS(NS, "g");
        g.setAttribute("transform", `translate(${{(104 * Math.cos(ang)).toFixed(2)}} ${{(104 * Math.sin(ang)).toFixed(2)}})`);
        const dim = document.createElementNS(NS, "circle");
        dim.setAttribute("r", "6");
        dim.setAttribute("fill", "none");
        dim.setAttribute("stroke", "#f7c64a");
        dim.setAttribute("stroke-width", "1.5");
        dim.setAttribute("opacity", "0.6");
        const halo = document.createElementNS(NS, "circle");
        halo.setAttribute("r", "14");
        halo.setAttribute("fill", "#ffb43c");
        halo.setAttribute("filter", "url(#glow)");
        halo.setAttribute("opacity", "0");
        const core = document.createElementNS(NS, "circle");
        core.setAttribute("r", "8");
        core.setAttribute("fill", "#fff4c8");
        core.setAttribute("opacity", "0");
        g.appendChild(dim);
        g.appendChild(halo);
        g.appendChild(core);
        lights.appendChild(g);
        LIGHTS.push({{ halo, core }});
      }}

      // timeline
      const tl = gsap.timeline({{ paused: true }});

      // fade in / out
      tl.fromTo("#black", {{ opacity: 1 }}, {{ opacity: 0, duration: 0.6, ease: "none" }}, 0);
      tl.to("#black", {{ opacity: 1, duration: 0.8, ease: "none" }}, DUR - 0.8);

      // god-rays: intro and outro
      tl.fromTo("#rays", {{ rotation: 0 }}, {{ rotation: 40, duration: DUR, ease: "none" }}, 0);
      tl.fromTo("#rays", {{ opacity: 0 }}, {{ opacity: 0.34, duration: 1.0 }}, 0.2);
      tl.to("#rays", {{ opacity: 0.08, duration: 0.8 }}, BEAT0 - 0.4);
      tl.to("#rays", {{ opacity: 0.34, duration: 1.2 }}, OUTRO);
      tl.to("#rays", {{ opacity: 0.12, duration: 1.0 }}, CREDITS);

      // embers rise all the way through
      EMBERS.forEach((p, i) => {{
        tl.fromTo(p.el, {{ y: 0, x: 0 }}, {{ y: -p.rise * 3, x: (i % 2 ? 1 : -1) * p.sway, duration: DUR, ease: "none" }}, 0);
        tl.fromTo(p.el, {{ opacity: 0 }}, {{ opacity: p.peak, duration: 0.8 }}, 0.3 + (i % 5) * 0.1);
        tl.to(p.el, {{ opacity: p.peak * 0.3, duration: 1.2, yoyo: true, repeat: 19, ease: "sine.inOut" }}, 1.2 + (i % 6) * 0.3);
      }});

      // bands: top band always behind the ring, bottom band for the temple text
      tl.fromTo("#band-top", {{ opacity: 0.6 }}, {{ opacity: 1, duration: 0.6 }}, BEAT0 - 0.5);
      tl.fromTo("#band-bottom", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6 }}, BEAT0 - 0.4);

      // ring: appears in the intro, spins slowly, one light per temple
      tl.fromTo("#ring", {{ scale: 0.7, opacity: 0, transformOrigin: "50% 50%" }}, {{ scale: 1, opacity: 1, duration: 1.2, ease: "power3.out" }}, 0.4);
      tl.fromTo("#ring-spin", {{ rotation: 0, svgOrigin: "0 0" }}, {{ rotation: 30, svgOrigin: "0 0", duration: DUR, ease: "none" }}, 0);
      LIGHTS.forEach((l, k) => {{
        const t = BEATS[k] + 0.15;
        tl.fromTo(l.core, {{ opacity: 0, scale: 0.2, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.45, ease: "back.out(3)" }}, t);
        tl.fromTo(l.halo, {{ opacity: 0, scale: 0.4, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1.8, duration: 0.5, ease: "power2.out" }}, t);
        tl.to(l.halo, {{ opacity: 0.55, scale: 1, duration: 0.9, ease: "sine.inOut" }}, t + 0.5);
      }});
      tl.fromTo("#ring-om", {{ opacity: 0.55 }}, {{ opacity: 1, duration: 0.6, yoyo: true, repeat: 1, ease: "sine.inOut" }}, OUTRO);

      // intro title
      tl.fromTo("#intro-deva", {{ y: 30, scale: 1.1, opacity: 0 }}, {{ y: 0, scale: 1, opacity: 1, duration: 1.1, ease: "power3.out" }}, 0.35);
      tl.fromTo("#intro-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.8, ease: "power2.out" }}, 0.75);
      tl.fromTo("#intro-l1", {{ y: 16, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "power2.out" }}, 1.0);
      tl.to("#intro-stack", {{ opacity: 0, scale: 1.04, duration: 0.5, ease: "power1.in" }}, BEAT0 - 0.45);

      // photos: crossfade in under a gold light leak, Ken Burns alternating push and pan
      const KB = [
        {{ from: {{ scale: 1.02, x: 0, y: 0 }}, to: {{ scale: 1.16, x: 0, y: -20 }} }},   // push in
        {{ from: {{ scale: 1.14, x: -60, y: 0 }}, to: {{ scale: 1.14, x: 60, y: 0 }} }},  // pan right
        {{ from: {{ scale: 1.17, x: 0, y: -20 }}, to: {{ scale: 1.03, x: 0, y: 0 }} }},   // pull out
        {{ from: {{ scale: 1.14, x: 60, y: 0 }}, to: {{ scale: 1.14, x: -60, y: 0 }} }},  // pan left
      ];
      BEATS.forEach((t0, k) => {{
        const id = `#ph${{k + 1}}`, img = `#img${{k + 1}}`;
        const kb = KB[k % 4];
        tl.fromTo(id, {{ opacity: 0 }}, {{ opacity: 1, duration: k === 0 ? 0.9 : 0.7, ease: "sine.inOut" }}, t0 - 0.45);
        tl.fromTo(img, kb.from, {{ ...kb.to, duration: BEAT_LEN + 1.0, ease: "sine.inOut" }}, t0 - 0.45);
        // the previous photo stays underneath, then is hidden once covered
        if (k > 0) tl.set(`#ph${{k}}`, {{ opacity: 0 }}, t0 + 0.3);
        const leak = k % 2 ? "#leak-r" : "#leak-l";
        tl.fromTo(leak, {{ opacity: 0, x: k % 2 ? 80 : -80 }}, {{ opacity: 0.75, x: 0, duration: 0.45, ease: "sine.in" }}, t0 - 0.45);
        tl.to(leak, {{ opacity: 0, x: k % 2 ? -60 : 60, duration: 0.7, ease: "sine.out" }}, t0);
      }});
      // last photo keeps drifting under the outro
      tl.to("#img12", {{ scale: 1.2, duration: DUR - OUTRO, ease: "none" }}, OUTRO + 0.55);

      // temple text: shared in/out
      BEATS.forEach((t0, k) => {{
        const id = `#b${{k + 1}}`;
        tl.fromTo(`${{id}} .badge`, {{ scale: 0.5, opacity: 0, rotation: -40, transformOrigin: "50% 50%" }}, {{ scale: 1, opacity: 1, rotation: 0, duration: 0.55, ease: "back.out(1.8)" }}, t0 + 0.05);
        tl.fromTo(`${{id}} .stotra`, {{ y: 18, opacity: 0 }}, {{ y: 0, opacity: 0.92, duration: 0.6, ease: "power2.out" }}, t0 + 0.15);
        tl.fromTo(`${{id}} .name`, {{ y: 30, scale: 1.08, opacity: 0 }}, {{ y: 0, scale: 1, opacity: 1, duration: 0.7, ease: "power3.out" }}, t0 + 0.25);
        tl.fromTo(`${{id}} .rule`, {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.6, ease: "power2.out" }}, t0 + 0.45);
        tl.fromTo(`${{id}} .en`, {{ y: 14, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.5, ease: "power2.out" }}, t0 + 0.55);
        tl.fromTo(`${{id}} .place`, {{ opacity: 0 }}, {{ opacity: 0.88, duration: 0.5 }}, t0 + 0.75);
        tl.to([`${{id}} .badge`, `${{id}} .stack`], {{ opacity: 0, duration: 0.35, ease: "power1.in" }}, t0 + BEAT_LEN - 0.4);
      }});

      // outro: blur the last photo, ring moves to centre and all twelve lights chase
      tl.to("#band-bottom", {{ opacity: 0.6, duration: 0.8 }}, OUTRO);
      tl.fromTo("#photos", {{ filter: "blur(0px) brightness(1) saturate(1)" }},
        {{ filter: "blur(20px) brightness(0.5) saturate(0.85)", duration: 1.0, ease: "power2.inOut" }}, OUTRO - 0.1);
      tl.to("#ring", {{ y: 560, scale: 2.1, duration: 1.2, ease: "power3.inOut" }}, OUTRO);
      LIGHTS.forEach((l, k) => {{
        tl.to(l.halo, {{ opacity: 1, scale: 1.6, duration: 0.18, yoyo: true, repeat: 1, ease: "sine.inOut" }}, OUTRO + 1.2 + k * 0.06);
      }});
      tl.fromTo("#outro-deva", {{ y: 26, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.8, ease: "power3.out" }}, OUTRO + 0.9);
      tl.fromTo("#outro-rule", {{ scaleX: 0 }}, {{ scaleX: 1, duration: 0.8, ease: "power2.out" }}, OUTRO + 1.2);
      tl.fromTo("#outro-l1", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.6 }}, OUTRO + 1.5);
      tl.to("#outro-stack", {{ opacity: 0, duration: 0.4, ease: "power1.in" }}, CREDITS - 0.4);

      // credits: ring returns to the top, list fades in
      tl.to("#ring", {{ y: 0, scale: 0.9, duration: 0.9, ease: "power3.inOut" }}, CREDITS - 0.4);
      tl.to("#photos", {{ filter: "blur(28px) brightness(0.3) saturate(0.7)", duration: 0.8 }}, CREDITS - 0.4);
      tl.to("#band-bottom", {{ opacity: 0, duration: 0.6 }}, CREDITS - 0.4);
      tl.fromTo("#credits-stack", {{ y: 20, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.7, ease: "power2.out" }}, CREDITS + 0.1);

      window.__timelines["main"] = tl;
    </script>
  </body>
</html>
"""


def build_credits(photos):
    lines = [
        "# Photo credits: Dwadash Jyotirlinga",
        "",
        "All photographs come from [Wikimedia Commons](https://commons.wikimedia.org/). Each is used under the licence",
        "shown, as read from the Commons API (`prop=imageinfo&iiprop=url|extmetadata`). In the video the photos are",
        "downscaled, cropped to 9:16 and animated (Ken Burns move, colour overlay and text). Those changes are released",
        "under the same licence as the source photo where that licence is CC BY-SA. A credits card at the end of the",
        "video lists every photographer and licence.",
        "",
        "| # | Temple | File | Author | Licence | Asset |",
        "|---|---|---|---|---|---|",
    ]
    for k, p in enumerate(photos):
        lic = p["license"]
        lic_md = f"[{lic}]({p['license_url']})" if p.get("license_url") else lic
        lines.append(
            f"| {k + 1} | {TEMPLES[k][1].title()} | [{p['title'][5:]}]({p['page']}) | {p['author']} | {lic_md} | `{p['file']}` |"
        )
    lines += [
        "",
        "Original files:",
        "",
    ]
    for k, p in enumerate(photos):
        lines.append(f"{k + 1}. {p['original']}")
    lines += [
        "",
        "The text of the Dwadash Jyotirlinga Stotram shown on screen is a traditional Sanskrit hymn in the public domain.",
        "The music and sound effects are synthesised from scratch by `../music.py`, `../sfx.py` and `soundtrack.py`.",
        "The fonts, Tiro Devanagari Sanskrit and Cinzel, are under the SIL Open Font License. GSAP is vendored from the earlier Mahakal project.",
        "",
    ]
    return "\n".join(lines)


def main():
    photos = json.load(open(os.path.join(HERE, "photos.json")))
    assert len(photos) == N
    with open(os.path.join(HERE, "project", "index.html"), "w") as f:
        f.write(build_html(photos))
    with open(os.path.join(HERE, "CREDITS.md"), "w") as f:
        f.write(build_credits(photos))


if __name__ == "__main__":
    main()
