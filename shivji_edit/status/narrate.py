"""Synthesise the Hindi narration with Piper and write timing.json for make_index.py and soundtrack.py.

Each caption is spoken by a Piper neural TTS voice. The measured length of each spoken line sets the
reel's timing, so the word-by-word caption reveal and the voice stay in sync.

Usage: python3 narrate.py VOICE.onnx [LENGTH_SCALE]
  VOICE.onnx: a Piper voice, e.g. hi_IN-pratham-medium.onnx from
  https://huggingface.co/rhasspy/piper-voices (its .onnx.json config must sit beside it).
"""
import json
import os
import subprocess
import sys
import wave

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "narration")

# (spoken text for the Hindi voice, on-screen caption). Captions mix Hindi and English the way people
# speak; the English words are spelt in Devanagari for the voice so it pronounces them naturally.
LINES = [
    ("लाइफ़ बहुत ईज़ी हो जाती है, जब समझ आ जाता है...", "Life बहुत easy हो जाती है, जब समझ आ जाता है…"),
    ("मिला तो उनकी कृपा,", "मिला तो उनकी कृपा,"),
    ("नहीं मिला तो उनकी इच्छा।", "नहीं मिला तो उनकी इच्छा \u201d"),
    ("बस ट्रस्ट रखो, महादेव सब देख रहे हैं।", "बस trust रखो, महादेव सब देख रहे हैं \u201d"),
    ("हर हर महादेव।", "॥ हर हर महादेव ॥"),
]
N_IMG, IMG_LEN = 7, 3.0


def wav_len(path):
    with wave.open(path) as w:
        return w.getnframes() / w.getframerate()


def main(model, length_scale=1.12):
    os.makedirs(OUT, exist_ok=True)
    durs = []
    for i, (spoken, _) in enumerate(LINES):
        path = os.path.join(OUT, f"l{i}.wav")
        subprocess.run(["piper", "-m", model, "-c", model + ".json", "--length-scale", str(length_scale),
                        "--sentence-silence", "0.1", "-f", path], input=spoken.encode(), check=True,
                       stderr=subprocess.DEVNULL)
        durs.append(round(wav_len(path), 3))

    # intro line on the black card, then seven paintings at 3 s; captions change every 7 s
    l0 = 0.5
    img0 = round(max(3.0, l0 + durs[0] + 0.6), 2)
    caps = [img0, round(img0 + 7.0, 2), round(img0 + 14.0, 2)]
    end = round(img0 + N_IMG * IMG_LEN, 2)
    starts = [l0, caps[0] + 0.5, caps[1] + 0.3, caps[2] + 0.4, end + 0.5]
    dur = round(max(end + 2.6, starts[4] + durs[4] + 1.2), 2)
    timing = {
        "voice": os.path.basename(model),
        "length_scale": length_scale,
        "dur": dur, "img0": img0, "img_len": IMG_LEN, "captions": caps, "end": end,
        "lines": [{"spoken": s, "caption": c, "start": round(t, 2), "dur": d, "wav": f"narration/l{i}.wav"}
                  for i, ((s, c), t, d) in enumerate(zip(LINES, starts, durs))],
    }
    with open(os.path.join(HERE, "timing.json"), "w") as f:
        json.dump(timing, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: timing[k] for k in ("dur", "img0", "captions", "end")}), durs)


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]) if len(sys.argv) > 2 else 1.12)
