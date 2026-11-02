# Mahakal darshan (HyperFrames)

Output: `output/mahakal_darshan.mp4`: 15.5 s, 1080x1920, 30 fps, -14 LUFS. Rendered with [HyperFrames](https://github.com/heygen-com/hyperframes) v0.8.184.

| Time | Picture | Sound |
|---|---|---|
| 0 – 0.9 s | Close-up hook with the **महाकाल** stinger and god-rays | Deep "Kaal" gong, Om chant |
| 0.9 – 3.9 s | Wide shot. Title **जय श्री महाकाल / MAHAKALESHWAR JYOTIRLINGA / UJJAIN** | Shankh, bansuri alaap |
| 2.1 – 4.1 s | Push-in with a warm light leak | Whoosh, damru, bell |
| 4.55 s | **द्वादश ज्योतिर्लिंग**: ring of 12 lights | Tabla starts, chime |
| 6.75 s | **दक्षिणमुखी महाकाल**: compass needle turns south | Chime |
| 8.95 s | **भस्म आरती**: tripundra (three ash lines) drawn on, ash drifting | Aarti hand-bells |
| 11.2 – 15.5 s | Blurred hold. "Lord of Time" clock dial with ॐ, **॥ हर हर महादेव ॥**, MAHAKAL · LORD OF TIME | Bell, clock ticks, shankh, gong, bansuri resolves to Sa |

## Rebuild
```
./prep_footage.sh IMG_8328.mov project/assets/darshan.mp4      # grade, stabilise, re-cut (ffmpeg)
python3 soundtrack.py out.wav [ambience.wav]                     # score + SFX; normalise to -14 LUFS -> project/assets/soundtrack.mp3
cd project
HYPERFRAMES_BROWSER_PATH=<chrome> npx hyperframes@0.8.184 check
HYPERFRAMES_BROWSER_PATH=<chrome> npx hyperframes@0.8.184 render --quality delivery --output ../output/mahakal_darshan.mp4
```
The text and animation are in `project/index.html`, which uses a GSAP timeline. GSAP and the fonts are vendored in `project/assets/`.
