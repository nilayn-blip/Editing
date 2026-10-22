# Mahadev status reel (HyperFrames)

Output: `output/mahadev_status.mp4`: 26.3 s, 1080x1920, 30 fps, -14 LUFS, for Instagram Reels.
Watermark: **Nirvana ✦ Nilay**, at the top right throughout.

The format follows the reference Short "Mahadev status video" (@Bharat_tana). I studied it from its title, description
and thumbnails only; nothing from it was downloaded or reused.

| Time | Picture | Caption |
|---|---|---|
| 0 – 3 s | Black card | *Life gets a lot easier when you realise…*, word by word, in small white serif |
| 3 – 10 s | Ganga descending onto Shiva, then Nilakantha | *mila to unki kripa,* |
| 10 – 17 s | Shyamala Shiva, then Shiva with family under the tree (Kangra) | *nahi mila to unki ichchha ”*, then the Devanagari line मिला तो उनकी कृपा, नहीं मिला तो उनकी इच्छा |
| 17 – 24 s | Shiva under trees, Vishvarupa, then Ravi Varma's Markandeya | *bas bharosa rakho, Mahadev sab dekh rahe hain ”*, then बस भरोसा रखो, महादेव सब देख रहे हैं |
| 24 – 26.3 s | The last painting blurs | **॥ हर हर महादेव ॥**, with a small credit for the paintings |

Each painting gets a slow push-in with a gentle drift and a soft 0.9 s dissolve. On top are a dark, moody grade, a vignette, light film grain and a few rising embers. The music is calm and has no percussion.

## Sources
- **Paintings:** seven public-domain or CC0 Shiva paintings from Wikimedia Commons. See [CREDITS.md](CREDITS.md).
- **Music:** an original synthesised score in `soundtrack.py`: tanpura, pad, a slow bansuri in Raga Shivaranjani, soft santoor and one bell. YouTube's Audio Library can only be used from a signed-in YouTube Studio account, so it couldn't be used from here. To use a track from it instead, download it, replace `project/assets/soundtrack.mp3` and re-render.

## Rebuild
```
pip install numpy scipy pillow
python3 -I tools/fetch.py tools/photos.txt /tmp/dl/a 1920        # only to change paintings
python3 -I tools/assemble.py /tmp/dl project s3,s2,s4,s7,s6,s1,s5
python3 soundtrack.py /tmp/st.wav
ffmpeg -i /tmp/st.wav -af volume=-1.1dB -c:a libmp3lame -b:a 192k project/assets/soundtrack.mp3   # -14.0 LUFS
python3 make_index.py
cd project
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell   # resolve the glob
npx hyperframes@0.8.184 check
npx hyperframes@0.8.184 render --quality delivery --fps 30 --output /tmp/master.mp4
ffmpeg -i /tmp/master.mp4 -c:v libx264 -preset slow -crf 20 -tune film -pix_fmt yuv420p -movflags +faststart -c:a copy ../output/mahadev_status.mp4
```

## Posting tips
- Cover frame: about 13 s, where the full quote is on screen.
- Caption idea: *मिला तो उनकी कृपा, नहीं मिला तो उनकी इच्छा 🙏 Har Har Mahadev. #mahadev #mahadevstatus #bholenath #harharmahadev #mahakal #shiva #shivbhakt #bhakti #spiritualshorts #sanatandharma*
