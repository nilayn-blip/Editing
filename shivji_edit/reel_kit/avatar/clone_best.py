"""Speak a reel's script in the owner's cloned voice, best of N takes per line.
Usage: python clone_best.py REEL_DIR VOICEPACK_DIR OUT.wav [N]   (VOICEPACK_DIR from voice_profile.py)
Each line is generated N times (different seeds/settings); every take is transcribed with Whisper and the take
with the best clarity (character error rate vs the script) and closeness to the owner's real voice
(speaker-embedding similarity) is kept. Writes one take with 1 s pauses
(the format `kit.py myvoice` expects) plus OUT_l{k}.wav per line and OUT.json with the scores."""
import json, os, re, sys, unicodedata
import torch, torchaudio
import numpy as np, librosa
from chatterbox.mtl_tts import ChatterboxMultilingualTTS, Conditionals
from faster_whisper import WhisperModel

d, pack, out = sys.argv[1:4]
N = int(sys.argv[4]) if len(sys.argv) > 4 else 4
N_MAX = 2 * N  # unclear lines get extra takes until one is clear (cer <= 0.2)
ONLY = {int(x) for x in os.environ.get("LINES", "").split(",") if x}  # regenerate only these lines, keep the rest
r = json.load(open(d + "/reel.json"))
items = [r["intro"]] + r["lines"] + [r["end"]]
SETTINGS = [dict(exaggeration=0.5, cfg_weight=0.5, temperature=0.6), dict(exaggeration=0.6, cfg_weight=0.4, temperature=0.7),
            dict(exaggeration=0.45, cfg_weight=0.6, temperature=0.55), dict(exaggeration=0.55, cfg_weight=0.5, temperature=0.65)]


def norm(s):
    s = unicodedata.normalize("NFC", s)
    return re.sub(r"[^ऀ-ॿ]", "", s).replace("।", "").replace("॥", "")


def cer(a, b):
    a, b = norm(a), norm(b)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1] / max(1, len(a))


tts = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
tts.conds = Conditionals.load(pack + "/conds.pt")
centre = np.load(pack + "/speaker_centre.npy")
asr = WhisperModel("small", device="cpu", compute_type="int8")
parts, report = [], []
prev = {x["line"]: x for x in json.load(open(out.replace(".wav", ".json")))} if ONLY else {}
for k, it in enumerate(items):
    if ONLY and k not in ONLY:
        wav, sr = torchaudio.load(out.replace(".wav", f"_l{k}.wav"))
        report.append(prev[k])
        parts += [wav, torch.zeros(1, int(tts.sr * 1.0))]
        continue
    best = None
    for n in range(N_MAX):
        if n >= N and best[4] <= 0.2:
            break
        torch.manual_seed(1000 * k + n + (100 if ONLY else 0))  # a redo tries new seeds
        wav = tts.generate(it["spoken"], language_id="hi", **SETTINGS[n % len(SETTINGS)])
        tmp = out.replace(".wav", f"_l{k}_t{n}.wav")
        torchaudio.save(tmp, wav, tts.sr)
        text = " ".join(s.text for s in asr.transcribe(tmp, language="hi", beam_size=5)[0])
        c = cer(it["spoken"], text)
        e = tts.ve.embeds_from_wavs([librosa.resample(wav[0].numpy(), orig_sr=tts.sr, target_sr=16000)], sample_rate=16000)[0]
        sim = float(np.dot(e, centre) / (np.linalg.norm(e) * np.linalg.norm(centre)))
        score = c - 0.5 * sim + (1.0 if c > 0.5 else 0.0)  # clarity first, then voice match; rambling takes lose
        print(f"line {k} take {n}: cer {c:.2f} sim {sim:.3f} | {text}", flush=True)
        if best is None or score < best[0]:
            best = (score, wav, n, text, c, sim)
    torchaudio.save(out.replace(".wav", f"_l{k}.wav"), best[1], tts.sr)
    report.append(dict(line=k, take=best[2], cer=round(best[4], 3), sim=round(best[5], 3), heard=best[3], script=it["spoken"]))
    parts += [best[1], torch.zeros(1, int(tts.sr * 1.0))]
torchaudio.save(out, torch.cat(parts[:-1], dim=1), tts.sr)
json.dump(report, open(out.replace(".wav", ".json"), "w"), ensure_ascii=False, indent=1)
print("done", out, [(x["cer"], x["sim"]) for x in report])
