# Shivji temple edit

Source: `IMG_8328.mov` (iPhone, 10.6 s, 1080x1920 HLG HDR).
Output: `output/shivji_temple_edit.mp4` (13 s, 1080x1920, 30 fps, H.264 + AAC, SDR Rec.709).

| Time | Picture | Sound |
|---|---|---|
| 0.0 – 2.5 s | Fade in on the wide shot (reframed so the donation box/QR is out of frame). Title **ॐ नमः शिवाय / OM NAMAH SHIVAYA** | Shankh (conch) + temple bell |
| 1.2 – 2.8 s | Camera push-in, with a warm light leak | Whoosh, then a bell as it lands on the shivling |
| 2.8 – 8.4 s | God-rays and golden embers. Lower third **॥ हर हर महादेव ॥ / HAR HAR MAHADEV** | Damru roll, bell |
| 8.4 – 9.2 s | Camera pull-out | Reverse whoosh |
| 9.4 – 13 s | Blurred freeze with an end card: rotating mandala, **ॐ**, *हर हर महादेव*, MAHADEV DARSHAN · AHMEDABAD · 2026 | Bell + shankh, fade out |

All sound effects are synthesised in `sfx.py`, so there are no third-party samples. The low drone and the original temple audio (kept at about 40 %) run underneath.

## Rebuild
```
pip install numpy scipy pillow     # Pillow needs raqm for Devanagari shaping
./build.sh IMG_8328.mov FONT_DIR output/shivji_temple_edit.mp4
```
`FONT_DIR` must contain `tiro.ttf` (Tiro Devanagari Sanskrit) and `cinzel.ttf` (Cinzel), both OFL Google Fonts.
To change any text or timing, edit the `frame()` timeline in `overlays.py` and the `place(...)` calls in `sfx.py`.
