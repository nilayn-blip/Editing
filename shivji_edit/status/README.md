# Mahadev status reel (HyperFrames)

Outputs (29 s, 1080x1920, 30 fps, for Instagram Reels; watermark **Nirvana ✦ Nilay** at the top right):
- `output/mahadev_status.mp4`: Hindi narration, mixed Hindi-English captions and an original peaceful score. -14 LUFS.
- `output/mahadev_status_voice_only.mp4`: the same picture with the narration over a very soft tanpura only. Use this one to add a song such as *Namami Shamishan* from Instagram's own music library when posting. Instagram licenses that music; a recording burnt into the file is not licensed and can get the reel muted. A good balance is the song at about 30–40% and original audio at 100%.

The format follows the reference Short "Mahadev status video" (@Bharat_tana). I studied it from its title, description
and thumbnails only; nothing from it was downloaded or reused.

| Time | Painting | Spoken and captioned |
|---|---|---|
| 0 – 5 s | Black card | *Life बहुत easy हो जाती है, जब समझ आ जाता है…* |
| 5 – 11 s | Ganga descending onto Shiva; Nilakantha | *मिला तो उनकी कृपा,* |
| 11 – 17 s | **Shiva and Parvati on Kailash** (Raja Ravi Varma); **Shiva and Parvati with Ganesha and Kartikeya** (Pahari) | *नहीं मिला तो उनकी इच्छा ”* |
| 17 – 26 s | Shiva under trees; Vishvarupa; Ravi Varma's Markandeya | *बस trust रखो, महादेव सब देख रहे हैं ”* |
| 26 – 29 s | The last painting blurs | **॥ हर हर महादेव ॥**, with a small credit for the paintings |

Each line is shown once, mixing Hindi and English the way people speak, and exactly what the narrator says. The words appear in step with the voice. Each painting gets about 3 s with a slow push-in and a soft dissolve, under a dark, moody grade, a vignette, light grain and a few rising embers.

## Sources
- **Paintings:** from Wikimedia Commons. Six are public domain and one, the Ravi Varma print from the Wellcome Collection, is CC BY 4.0 and is credited on screen. See [CREDITS.md](CREDITS.md).
- **Narration:** [Piper](https://github.com/rhasspy/piper) neural TTS, voice `hi_IN-pratham-medium`. The voice was trained on AI4Bharat data under **CC BY-NC-SA 4.0**, so it is fine for a personal, non-commercial Instagram account. For paid or brand content, re-record the lines yourself or use a voice licensed for commercial use. The English words are spelt in Devanagari for the voice so it pronounces them naturally.
- **Music:** an original synthesised score in `soundtrack.py` (tanpura, pad, slow bansuri, soft santoor). The music dips under the voice.

## Rebuild
```
pip install numpy scipy pillow piper-tts
# voice: hi_IN-pratham-medium.onnx + .onnx.json from https://huggingface.co/rhasspy/piper-voices (hi/hi_IN/pratham/medium)
python3 narrate.py /path/to/hi_IN-pratham-medium.onnx      # narration/l*.wav + timing.json
python3 -I tools/fetch.py tools/photos.txt /tmp/dl/a 1920    # only to change paintings
python3 -I tools/assemble.py /tmp/dl project s3,s2,w1,w2,s6,s1,s5
python3 soundtrack.py /tmp/st.wav
ffmpeg -i /tmp/st.wav -af "volume=-0.7dB,alimiter=limit=0.84:level=false" -c:a libmp3lame -b:a 192k project/assets/soundtrack.mp3   # -14.0 LUFS
python3 make_index.py
cd project
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-*/chrome-linux/headless_shell   # resolve the glob
npx hyperframes@0.8.184 check
npx hyperframes@0.8.184 render --quality delivery --fps 30 --output /tmp/master.mp4
ffmpeg -i /tmp/master.mp4 -c:v libx264 -preset slow -crf 20 -tune film -pix_fmt yuv420p -movflags +faststart -c:a copy ../output/mahadev_status.mp4
# voice-only version: same picture, narration-only audio
python3 ../soundtrack.py /tmp/vo.wav --voice-only
ffmpeg -i /tmp/vo.wav -af loudnorm=I=-16:TP=-1.5 -c:a aac -b:a 192k /tmp/vo.m4a
ffmpeg -i ../output/mahadev_status.mp4 -i /tmp/vo.m4a -map 0:v -map 1:a -c copy ../output/mahadev_status_voice_only.mp4
```

## Posting tips
- Cover frame: about 14 s, the Ravi Varma Shiva–Parvati painting with the full quote on screen.
- Caption idea: *मिला तो उनकी कृपा, नहीं मिला तो उनकी इच्छा 🙏 Har Har Mahadev. #mahadev #mahadevstatus #bholenath #shivparvati #harharmahadev #mahakal #shiva #shivbhakt #bhakti #spiritualshorts*
