# Om Namah Shivaya (HyperFrames)

Output: `output/om_namah_shivaya.mp4`: 36 s, 1080x1920, 30 fps, -14 LUFS, for Instagram Reels.
The style is slow and cinematic, like an aarti. Watermark: **Nirvana ✦ Nilay**, at the top right throughout.
Rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) v0.8.184.

| Time | Picture | Sound |
|---|---|---|
| 0 – 2.6 s | **Hook:** a huge ॐ appears out of a blur under god-rays. **॥ पञ्चाक्षर मन्त्र ॥ / THE FIVE SACRED SYLLABLES OF SHIVA** | Deep gong, shankh, Om chant |
| 2.6 – 24.6 s | **Five syllable beats (न म शि वा य), 4.4 s each.** Each has a full-bleed photo with a slow Ken Burns move, a gold light-leak crossfade, the syllable huge and glowing, its line from Adi Shankara's *Shiva Panchakshara Stotram* ("…तस्मै नकाराय नमः शिवाय"), and a short English gloss. A row of the five syllables at the top lights up one by one | Deep bell and santoor shimmer on each syllable, slow bansuri alaap, tabla from the third syllable |
| 24.6 – 29 s | **Climax:** a burst of light, then a rotating 108-bead mandala, ॐ, and the syllables gathering into **ॐ नमः शिवाय** over Mount Kailash | Damru roll, gong, shankh, aarti hand-bells |
| 29 – 33.4 s | **॥ हर हर महादेव ॥** and the call to action **COMMENT ॐ नमः शिवाय & SHARE** | Big bell, hand-bells, flute resolves to Sa |
| 33.4 – 36 s | Credits card listing every photographer and licence | Last bell, fade out |

The whole video also has a warm grade, a vignette, drifting incense haze, rising diya embers and a light film grain.

The photos are from Wikimedia Commons. See [CREDITS.md](CREDITS.md).

## Files
- `photos.json`: the six photos in beat order (five syllables, then Kailash), with their Commons metadata and focal points.
- `make_index.py`: generates `project/index.html` and `CREDITS.md`. Edit the text and timing here.
- `soundtrack.py`: the score and sound effects. It reuses `../music.py` and `../sfx.py`.
- `tools/`: `fetch.py` downloads standard-size Commons thumbnails politely and records their licences. `assemble.py` resizes them into `project/assets/` and writes `photos.json`.

## Rebuild
```
pip install numpy scipy pillow
python3 -I tools/fetch.py tools/photos.txt /tmp/dl/a 1920        # only to change photos
python3 -I tools/assemble.py /tmp/dl project m1,m2,m3,m4,m5,m6
python3 soundtrack.py /tmp/st.wav
ffmpeg -i /tmp/st.wav -af "volume=1.4dB,alimiter=limit=0.84:level=false" -c:a libmp3lame -b:a 192k project/assets/soundtrack.mp3   # -14.0 LUFS
python3 make_index.py
cd project
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell   # resolve the glob
npx hyperframes@0.8.184 check
npx hyperframes@0.8.184 render --quality delivery --fps 30 --output /tmp/master.mp4
ffmpeg -i /tmp/master.mp4 -c:v libx264 -preset slow -crf 18 -pix_fmt yuv420p -movflags +faststart -c:a copy ../output/om_namah_shivaya.mp4
```

## Posting tips
- Cover frame: about 26.5 s, where the mantra has formed over the mandala.
- Caption idea: *ॐ नमः शिवाय 🙏 The five sacred syllables of Mahadev, from Adi Shankara's Shiva Panchakshara Stotram. Comment ॐ नमः शिवाय if you chant it daily. #mahadev #omnamahshivaya #harharmahadev #shiva #bholenath #shivaya #panchakshara #sanatandharma #mahakal #shivbhakt*
- Photo credits: the credits card is in the video. You can also paste the lines from CREDITS.md into the caption.
