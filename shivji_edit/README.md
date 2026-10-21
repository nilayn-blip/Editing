# Shivji temple edit

Source: `IMG_8328.mov` (iPhone, 10.6 s, 1080x1920 HLG HDR).
Output: `output/shivji_temple_edit.mp4` (12.5 s, 1080x1920, 30 fps, H.264 + AAC, SDR Rec.709, -14 LUFS).

| Output time | Picture | Sound |
|---|---|---|
| 0.0 – 0.9 s | **Hook:** close-up of the shivling with a slow digital push, god-rays and embers | Bell strike, "Om" chant, riser |
| 0.9 s | Gold flash cut | — |
| 0.9 – 2.1 s | Wide shot through the doorway, cropped tight so the donation box/QR stays out of frame. Title **ॐ नमः शिवाय / OM NAMAH SHIVAYA** | Shankh (conch); tanpura starts |
| 2.1 – 4.1 s | Camera push-in slowed to 0.8x with frame blending, plus a warm light leak | Whoosh, then a bell as it lands |
| 4.1 – 9.5 s | Darshan hold slowed to 0.8x (motion-interpolated) with a slow push-in. Lower third **॥ हर हर महादेव ॥ / HAR HAR MAHADEV** | Damru roll, distant ghantis, bell |
| 9.4 – 12.5 s | Held close-up, blurred, with an end card: rotating mandala, **ॐ**, *हर हर महादेव*, MAHADEV DARSHAN · AHMEDABAD · 2026 | Bell, "Om" chant, shankh, fade out |

Also applied:
- iPhone HLG HDR converted to SDR with a warm grade, so colours don't wash out on Instagram or WhatsApp
- vidstab stabilisation
- the jerky 7.2 s reframe and the 8.4 s pull-out are cut, so the video ends on the deity
- the original audio is noise-reduced and kept low under the tanpura and drone bed
- loudness is set to -14 LUFS with a -1 dBTP limit

All sound is synthesised in `sfx.py` (tanpura, formant "Om" choir, bells, shankh, damru, whooshes), so there are no third-party samples.

## Rebuild
```
pip install numpy scipy pillow     # Pillow needs raqm for Devanagari shaping
./build.sh IMG_8328.mov FONT_DIR output/shivji_temple_edit.mp4
```
`FONT_DIR` must contain `tiro.ttf` (Tiro Devanagari Sanskrit) and `cinzel.ttf` (Cinzel), both OFL Google Fonts.
To change any text or timing, edit the `frame()` timeline in `overlays.py` and the `place(...)` calls in `sfx.py`.
