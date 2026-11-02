"""Build the owner's voice pack from their recordings.
Usage: python voice_profile.py OUTDIR AUDIO1 [AUDIO2 ...]   (any rate/channels; first file = main source)

1. Speech is found with Whisper's VAD + timestamps and cut into utterances (1.2-9 s).
2. Each recording is denoised (noisereduce, noise profile from its own non-speech parts).
3. Every utterance gets an SNR estimate and a speaker embedding (Chatterbox's voice encoder);
   utterances far from the dominant speaker are dropped (other people, PA announcements).
4. The cleanest utterances become the cloning reference (ref.wav, ~10 s, what the decoder uses) and the speaker
   embedding is averaged over ALL clean utterances (steadier identity than one clip).
5. Saves OUTDIR/conds.pt (load with Conditionals.load), ref.wav, profile.json (pitch, pace, similarity report).
"""
import json, os, sys
import numpy as np, librosa, soundfile as sf, noisereduce as nr, torch
from faster_whisper import WhisperModel
from chatterbox.mtl_tts import ChatterboxMultilingualTTS, Conditionals
from chatterbox.models.t3.modules.cond_enc import T3Cond

out, files = sys.argv[1], sys.argv[2:]
os.makedirs(out, exist_ok=True)
SR = 24000
asr = WhisperModel("small", device="cpu", compute_type="int8")
tts = ChatterboxMultilingualTTS.from_pretrained(device="cpu")
ve = tts.ve


def cos(a, b):
    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-9))


utts = []
for fi, f in enumerate(files):
    y, _ = librosa.load(f, sr=SR, mono=True)
    y = librosa.effects.preemphasis(y, coef=0.0)  # no-op, keeps dtype float32
    segs, info = asr.transcribe(f, beam_size=5, vad_filter=True)
    segs = list(segs)
    # energy-based speech regions (Whisper's long segments are too coarse for picking clean utterances)
    iv = librosa.effects.split(y, top_db=28, frame_length=1024, hop_length=256)
    merged = []
    for a, b in iv:
        if merged and a - merged[-1][1] < int(0.35 * SR):
            merged[-1][1] = b
        else:
            merged.append([a, b])
    speech = np.zeros(len(y), bool)
    for a, b in merged:
        speech[a:b] = True
    noise = y[~speech]
    yd = nr.reduce_noise(y=y, sr=SR, y_noise=noise if len(noise) > SR else None, stationary=False, prop_decrease=0.85) if len(noise) > SR // 2 else y
    floor = np.sqrt(np.mean(noise ** 2)) if len(noise) > SR // 2 else 1e-3
    def text_at(a, b):
        return " ".join(s.text.strip() for s in segs if s.end > a and s.start < b)[:120]
    for a, b in merged:
        # split long regions into <= 8 s pieces at the quietest point
        pieces = [(a, b)]
        while any(q - p > 8 * SR for p, q in pieces):
            p, q = next(x for x in pieces if x[1] - x[0] > 8 * SR)
            mid = y[p + 2 * SR:q - 2 * SR]
            e = np.convolve(mid ** 2, np.ones(2400) / 2400, mode="same")
            cut = p + 2 * SR + int(np.argmin(e))
            i = pieces.index((p, q)); pieces[i:i + 1] = [(p, cut), (cut, q)]
        for p, q in pieces:
            if q - p < int(1.2 * SR):
                continue
            raw = y[p:q]
            snr = 20 * np.log10(np.sqrt(np.mean(raw ** 2)) / floor + 1e-9)
            utts.append(dict(file=fi, start=round(p / SR, 2), end=round(q / SR, 2), text=text_at(p / SR, q / SR),
                             lang=info.language, snr=round(float(snr), 1), wav=yd[p:q]))
    print(f"{os.path.basename(f)}: {info.language} {len(merged)} speech regions, noise floor {20*np.log10(floor+1e-9):.1f} dBFS", flush=True)

# speaker embeddings (16 kHz)
embs = ve.embeds_from_wavs([librosa.resample(u["wav"], orig_sr=SR, target_sr=16000) for u in utts], sample_rate=16000)
for u, e in zip(utts, embs):
    u["emb"] = e
# dominant speaker: iterate mean of the most self-similar utterances
centre = np.mean(embs, axis=0)
for _ in range(3):
    sims = np.array([cos(e, centre) for e in embs])
    keep = sims >= np.percentile(sims, 40)
    centre = np.mean(embs[keep], axis=0)
for u in utts:
    u["sim"] = round(cos(u["emb"], centre), 3)
clean = [u for u in utts if u["sim"] >= 0.8 and u["snr"] >= 10]
per_file = {}
for fi, f in enumerate(files):
    fe = [u["emb"] for u in utts if u["file"] == fi]
    if fe:
        per_file[os.path.basename(f)] = dict(utterances=len(fe), speaker_similarity=round(cos(np.mean(fe, axis=0), centre), 3))
print("per-file similarity to the dominant voice:", json.dumps(per_file, ensure_ascii=False), flush=True)

# reference: cleanest utterances first, up to ~10 s (decoder) ; t3 prompt uses the first ~6 s
best = sorted([u for u in clean if u["sim"] >= 0.84 and u["snr"] >= 14], key=lambda u: -(u["sim"] + u["snr"] / 100))
ref, used = [], []
for u in best:
    if sum(len(x) for x in ref) / SR >= 10.0:
        break
    w = u["wav"] / (np.max(np.abs(u["wav"])) + 1e-9) * 0.9
    ref += [w, np.zeros(int(0.18 * SR), np.float32)]
    used.append(u)
ref = np.concatenate(ref).astype(np.float32)
sf.write(os.path.join(out, "ref.wav"), ref, SR)

# conditionals: decoder + prompt tokens from ref.wav, speaker embedding averaged over every clean utterance
tts.prepare_conditionals(os.path.join(out, "ref.wav"), exaggeration=0.5)
spk = torch.from_numpy(np.mean([u["emb"] for u in clean], axis=0, keepdims=True)).float()
c = tts.conds
c.t3 = T3Cond(speaker_emb=spk, cond_prompt_speech_tokens=c.t3.cond_prompt_speech_tokens, emotion_adv=c.t3.emotion_adv)
c.save(os.path.join(out, "conds.pt"))
np.save(os.path.join(out, "speaker_centre.npy"), centre)

# voice traits
allc = np.concatenate([u["wav"] for u in clean])
f0, vf, _ = librosa.pyin(allc, fmin=65, fmax=400, sr=SR, frame_length=2048)
f0 = f0[vf & ~np.isnan(f0)]
words = sum(len(u["text"].split()) for u in clean)
secs = sum(u["end"] - u["start"] for u in clean)
profile = dict(
    sources=[os.path.basename(f) for f in files], per_file=per_file,
    clean_utterances=len(clean), clean_seconds=round(secs, 1), dropped=len(utts) - len(clean),
    pitch_hz=dict(median=round(float(np.median(f0)), 1), p10=round(float(np.percentile(f0, 10)), 1), p90=round(float(np.percentile(f0, 90)), 1)),
    words_per_second=round(words / max(secs, 1e-6), 2),
    reference=[dict(file=os.path.basename(files[u["file"]]), start=u["start"], end=u["end"], snr=u["snr"], sim=u["sim"], text=u["text"]) for u in used],
    all=[dict(file=u["file"], start=u["start"], end=u["end"], snr=u["snr"], sim=u["sim"], lang=u["lang"], text=u["text"]) for u in utts],
)
json.dump(profile, open(os.path.join(out, "profile.json"), "w"), ensure_ascii=False, indent=1)
print(json.dumps({k: v for k, v in profile.items() if k not in ("all",)}, ensure_ascii=False, indent=1))
