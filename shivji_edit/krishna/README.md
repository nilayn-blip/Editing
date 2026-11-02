# Krishna status reel (HyperFrames)

This reel uses the same format as `../status` (the Mahadev status reel), here for **Shri Krishna**.

Outputs (~28.5 s, 1080x1920, 30 fps, for Instagram Reels; watermark **Nirvana ✦ Nilay** at the top right):
- `output/krishna_status.mp4`: Hindi narration, mixed Hindi-English captions and an original flute score. -14 LUFS.
- `output/krishna_status_voice_only.mp4`: the same picture with the narration over a soft tanpura only. Use this one to add a song from Instagram's music library when posting, such as *Achyutam Keshavam* or *Shri Krishna Govind Hare Murari*. Instagram licenses that music. A good balance is the song at about 30–40% and original audio at 100%.

| Time | Spoken and captioned (word by word, in sync with the voice) |
|---|---|
| 0 – 4.4 s | *Life में जब सब उलझ जाए, तो बस याद रखना…* (black card) |
| 4.4 – 11.4 s | *जो हुआ, अच्छा हुआ,* |
| 11.4 – 18.4 s | *जो हो रहा है, अच्छा हो रहा है,* |
| 18.4 – 25.4 s | *जो होगा, वो भी अच्छा होगा… बस trust रखो ”* |
| 25.4 – 28.6 s | **॥ जय श्री कृष्ण ॥** over Krishna giving the Gita to Arjuna |

The lines are the popular "Gita saar" summary of the Bhagavad Gita's teaching.

## Sources
- **Paintings:** six public-domain or CC0 Krishna paintings (3.5 s each) from Wikimedia Commons, including Kangra, Kishangarh and Pahari works and Krishna giving the Gita to Arjuna. See [CREDITS.md](CREDITS.md).
- **Narration:** [Piper](https://github.com/rhasspy/piper) TTS, voice `hi_IN-pratham-medium`. The voice was trained on data under **CC BY-NC-SA 4.0**, so it is fine for a personal, non-commercial Instagram account. For paid or brand content, record the five lines yourself.
- **Music:** original and synthesised (`soundtrack.py`). The bansuri, Krishna's flute, plays in **Raga Bhupali**, with tanpura, pad and santoor, and ghungroo-like bells on the closing line. The music dips under the voice.

## Rebuild
Same as `../status/README.md`, using this folder:
```
python3 narrate.py /path/to/hi_IN-pratham-medium.onnx
python3 -I tools/fetch.py tools/photos.txt /tmp/dl/a 1920
python3 -I tools/assemble.py /tmp/dl project k1,k2,k4,k5,k6,k3
python3 soundtrack.py /tmp/st.wav && python3 soundtrack.py /tmp/vo.wav --voice-only
ffmpeg -i /tmp/st.wav -af "volume=-0.1dB,alimiter=limit=0.84:level=false" -c:a libmp3lame -b:a 192k project/assets/soundtrack.mp3   # -14 LUFS
python3 make_index.py
cd project && npx hyperframes@0.8.184 check && npx hyperframes@0.8.184 render --quality delivery --fps 30 --output /tmp/master.mp4
```

## Posting tips
- Cover frame: a Radha–Krishna painting with a full line on screen, at about 13 s.
- Caption idea: *जो हुआ, अच्छा हुआ… जो होगा, वो भी अच्छा होगा 🙏 Jai Shri Krishna. #krishna #radhakrishna #jaishrikrishna #bhagavadgita #gitasaar #krishnastatus #radheradhe #bhakti #spiritualshorts #sanatandharma*
