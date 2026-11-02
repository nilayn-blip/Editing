"""Peaceful soundtrack + Hindi narration for the Mahadev status reel, timed by timing.json (from narrate.py).

Calm and minimal, like the reference's "peaceful music": tanpura + soft drone + Sa-Pa pad, a slow
bansuri melody in Raga Shivaranjani, gentle santoor arpeggios on each caption change and a soft bell
on the last line. No percussion. Built from the synthesised instruments in ../sfx.py and ../music.py.
The narration (Piper TTS, narration/l*.wav) sits on top; the music dips under the voice.

Usage: python3 soundtrack.py OUT.wav [--voice-only]
  --voice-only: narration over a very soft tanpura only, for adding a song from Instagram's own
  music library when posting (Instagram licenses that music; a recording burnt into the file is not).
"""
import json
import os
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import resample_poly

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))

from music import D, G, P, R, S, bansuri, pad, santoor_run  # noqa: E402
from sfx import (SR, bandpass, drone, highpass, lowpass, om_choir, place, reverb, t_axis,  # noqa: E402
                 tanpura_bed, temple_bell)

TIMING = json.load(open(os.path.join(HERE, "timing.json")))
DUR, END = TIMING["dur"], TIMING["end"]
C1, C2, C3 = TIMING["captions"]


def flute_line():
    """Slow bansuri phrases placed relative to the caption changes."""
    phrases = [
        (0.6, [(0.0, S, 1.3), (1.4, R, 0.7), (2.1, G, 1.4)]),
        (C1 + 0.9, [(0.0, P, 1.6), (1.7, G, 0.8), (2.6, R, 0.8), (3.5, S, 2.2)]),
        (C2 + 0.5, [(0.0, D - 12, 0.9), (1.0, S, 1.0), (2.1, R, 0.9), (3.1, G, 2.8)]),
        (C3 + 0.4, [(0.0, P, 1.1), (1.2, D, 1.1), (2.4, S + 12, 2.2), (4.7, D, 0.7), (5.5, P, 1.0)]),
        (END + 0.2, [(0.0, G, 0.6), (0.6, R, 0.6), (1.2, S, 1.2)]),
    ]
    return [(t0 + o, n, ln) for t0, notes in phrases for o, n, ln in notes]


def load_voice(path):
    sr, x = wavfile.read(path)
    x = x.astype(float) / 32768
    if x.ndim > 1:
        x = x.mean(axis=1)
    x = resample_poly(x, SR, sr)
    # warm, present narrator: trim rumble, a little body, gentle de-ess, soft short room
    x = highpass(x, 75)
    x = x + 0.25 * bandpass(x, 150, 350)
    x = x - 0.25 * bandpass(x, 5500, 8500)
    x = reverb(x, seconds=1.2, wet=0.12)
    return x / np.abs(x).max()


def main(out_path, voice_only=False):
    dur = DUR
    n = int(dur * SR)
    music = np.zeros((n + SR * 8, 2))
    T = np.arange(music.shape[0] + SR * 2) / SR

    tp = tanpura_bed(dur + 1)
    place(music, tp * np.clip(T[: len(tp)] / 2.0, 0, 1), 0.0, 0.06 if voice_only else 0.12)
    d = drone(dur + 1)
    place(music, d * np.clip(T[: len(d)] / 2.5, 0, 1), 0.0, 0.03 if voice_only else 0.07)
    p = pad(dur + 1) * (0 if voice_only else 1)
    place(music, p * np.clip((T[: len(p)] - 1.0) / 3.0, 0, 1), 0.0, 0.09)
    if not voice_only:
        place(music, bansuri(dur, flute_line()), 0.0, 0.30, pan=0.05)

    runs = [[S, G, P, S + 12], [R, P, D, R + 12], [G, D, S + 12, G + 12]]
    for k, t in enumerate((C1, C2, C3)):
        if not voice_only:
            place(music, santoor_run(runs[k], 0.12), t + 0.05, 0.09, pan=[-0.3, 0.3, 0.0][k])
    if not voice_only:
        place(music, om_choir(3.0), END - 0.2, 0.10)
    place(music, temple_bell(587, 4.0), END, 0.16)

    music[:, 0] = reverb(music[:, 0], seconds=3.5, wet=0.4)
    music[:, 1] = reverb(music[:, 1], seconds=3.5, wet=0.4)
    music = music[:n]

    # narration track and a smooth ducking envelope (music -7 dB under the voice)
    voice = np.zeros(n)
    gate = np.zeros(n)
    for ln in TIMING["lines"]:
        v = load_voice(os.path.join(HERE, ln["wav"]))
        i = int(ln["start"] * SR)
        m = min(len(v), n - i)
        voice[i:i + m] += v[:m]
        gate[max(0, i - int(0.25 * SR)):i + m + int(0.3 * SR)] = 1.0
    a = np.exp(-1 / (0.18 * SR))
    env = np.zeros(n)
    acc = 0.0
    for k in range(0, n, 64):  # one-pole smoothing at block rate
        acc = a ** 64 * acc + (1 - a ** 64) * gate[k]
        env[k:k + 64] = acc
    duck = 1.0 - (1.0 - 10 ** (-7 / 20)) * env

    mix = music * duck[:, None] * 0.9
    mix += voice[:, None] * 0.55
    mix *= (np.clip(t_axis(dur) / 0.6, 0, 1) * np.clip((dur - t_axis(dur)) / 1.0, 0, 1))[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1], "--voice-only" in sys.argv[2:])
