# Dwadash Jyotirlinga (HyperFrames)

Output: `output/dwadash_jyotirlinga.mp4`: 55.5 s, 1080x1920, 30 fps, -14 LUFS, for Instagram Reels and YouTube Shorts.
Rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) v0.8.184.

| Time | Picture | Sound |
|---|---|---|
| 0 – 3.2 s | **॥ द्वादश ज्योतिर्लिंग ॥ / THE 12 JYOTIRLINGAS OF SHIVA** over god-rays and embers. The ring of 12 lights appears at the top | Om chant, shankh, bell, bansuri alaap |
| 3.2 – 46.4 s | One 3.6 s beat per temple, in the stotram order. Each beat has a full-bleed photo with a Ken Burns move that alternates push-in, pan right, pull-out and pan left; a gold number badge (१–१२); the matching line of the Dwadash Jyotirlinga Stotram; the name in Devanagari and Latin; and the place and state. One light on the ring fills in per temple. A soft gold light leak covers each crossfade | Tabla keherwa throughout (one cycle per temple), a bell and soft whoosh on each temple change, bansuri melody |
| 46.4 – 50.6 s | The last photo blurs, the completed ring moves to the centre and its lights chase, then **॥ हर हर महादेव ॥** | Bell, Om chant, shankh, flute resolves to Sa |
| 50.6 – 55.5 s | Credits card listing every photographer and licence | Last bell, fade out |

The photos are from Wikimedia Commons. See [CREDITS.md](CREDITS.md) for each file, author, licence and link.

## Files
- `photos.json`: one photo per temple, with its Commons metadata (title, author, licence, URLs) and the focal point used for the 9:16 crop (`object-position`).
- `make_index.py`: generates `project/index.html` and `CREDITS.md` from `photos.json`. Edit text and timing there, not in the generated HTML.
- `soundtrack.py`: the score and sound effects for this timeline. It reuses `../music.py` and `../sfx.py`.
- `project/`: the HyperFrames project. GSAP, the fonts, the photos and the soundtrack are in `project/assets/`.

## Rebuild
```
pip install numpy scipy
python3 soundtrack.py /tmp/st.wav
ffmpeg -i /tmp/st.wav -af volume=-0.6dB -c:a libmp3lame -b:a 192k project/assets/soundtrack.mp3   # -14.0 LUFS
python3 make_index.py
cd project
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell   # resolve the glob
npx hyperframes@0.8.184 check
npx hyperframes@0.8.184 render --quality delivery --output ../output/dwadash_jyotirlinga.mp4
```
If you change the score, re-measure with `ffmpeg -i project/assets/soundtrack.mp3 -af ebur128 -f null -` and adjust the gain.
