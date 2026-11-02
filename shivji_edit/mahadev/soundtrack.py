"""Soundtrack for the Om Namah Shivaya edit (36 s), timed to make_index.py.

Slow, cinematic aarti mood built from the synthesised instruments in ../sfx.py and ../music.py:
tanpura + drone + Om choir bed, a slow bansuri alaap in Raga Shivaranjani, a deep bell and a
santoor shimmer on each of the five syllables, soft tabla rising into a damru roll, and a gong,
shankh and aarti hand-bells at the climax.

Usage: python3 soundtrack.py OUT.wav
"""
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from music import D, G, P, R, S, compose, santoor_run  # noqa: E402
from sfx import (SR, damru, drone, ghanti_scatter, om_choir, place, reverb, shankh,  # noqa: E402
                 t_axis, tanpura_bed, temple_bell, whoosh)

# Output times; keep in sync with make_index.py
DUR = 36.0
HOOK = 0.0
BEAT0, BEAT_LEN, N = 2.6, 4.4, 5
CLIMAX = BEAT0 + N * BEAT_LEN  # 24.6: syllables gather into ॐ नमः शिवाय
END = 29.0                     # हर हर महादेव + call to action
CREDITS = 33.4
BEATS = [BEAT0 + k * BEAT_LEN for k in range(N)]

# slow alaap: (start, semitone, length); long held notes with meend between them
FLUTE = [
    (0.9, S, 1.4),
    (BEATS[0] + 0.5, P - 12, 0.9), (BEATS[0] + 1.5, S, 1.2), (BEATS[0] + 2.9, R, 1.2),
    (BEATS[1] + 0.5, G, 1.3), (BEATS[1] + 2.0, R, 0.8), (BEATS[1] + 2.9, S, 1.3),
    (BEATS[2] + 0.5, P, 1.6), (BEATS[2] + 2.3, D, 0.9), (BEATS[2] + 3.3, P, 0.9),
    (BEATS[3] + 0.5, D, 1.0), (BEATS[3] + 1.6, S + 12, 1.7), (BEATS[3] + 3.4, D, 0.8),
    (BEATS[4] + 0.5, P, 0.9), (BEATS[4] + 1.5, G, 1.0), (BEATS[4] + 2.6, R, 1.6),
    (CLIMAX + 0.4, S + 12, 2.4), (CLIMAX + 2.9, D, 0.7), (CLIMAX + 3.6, P, 1.0),
    (END + 0.4, G, 1.0), (END + 1.5, R, 1.0), (END + 2.6, S, 3.6),
]


def gong():
    """Deep gong with a sub boom for the hook and the climax."""
    g = temple_bell(150, 7.0)
    t = t_axis(7.0)
    boom = np.sin(2 * np.pi * 48 * t * (1 + 0.3 * np.exp(-t / 0.08))) * np.exp(-t / 1.4)
    y = 0.7 * g + 0.6 * boom
    return y / np.abs(y).max()


def main(out_path):
    dur = DUR
    mix = np.zeros((int(dur * SR) + SR * 8, 2))
    T = np.arange(mix.shape[0] + SR * 2) / SR

    tp = tanpura_bed(dur + 1)
    place(mix, tp * np.clip(T[: len(tp)] / 1.2, 0, 1) * np.clip((dur - T[: len(tp)]) / 2.5, 0, 1), 0.0, 0.13)
    d = drone(dur + 1)
    place(mix, d * np.clip(T[: len(d)] / 1.0, 0, 1) * np.clip((dur - T[: len(d)]) / 2.5, 0, 1), 0.0, 0.10)
    for at, ln in ((HOOK, 4.0), (BEATS[2], 4.6), (CLIMAX, 4.6), (END, 5.0)):
        place(mix, om_choir(ln), at, 0.17)

    # hook: gong + shankh as the Om ignites
    place(mix, gong(), 0.05, 0.40)
    place(mix, shankh(), 0.35, 0.28)
    place(mix, whoosh(0.9, rise=True), BEAT0 - 0.8, 0.10)

    # each syllable: deep bell + santoor shimmer up the raga
    bells = [392, 440, 466, 523, 587]
    runs = [[S, R, G], [R, G, P], [G, P, D], [P, D, S + 12], [D, S + 12, R + 12]]
    for k, b in enumerate(BEATS):
        place(mix, temple_bell(bells[k], 4.0), b + 0.1, 0.24, pan=[-0.2, 0.2][k % 2])
        place(mix, santoor_run(runs[k], 0.09), b + 0.15, 0.10, pan=[0.25, -0.25][k % 2])
        if k:
            place(mix, whoosh(0.8, rise=True), b - 0.65, 0.06, pan=[0.3, -0.3][k % 2])

    # build: damru roll into the climax
    place(mix, damru(1.6, 6.0, 20.0), CLIMAX - 1.6, 0.20)
    place(mix, whoosh(1.4, rise=True), CLIMAX - 1.3, 0.14)

    score = compose(dur, flute=FLUTE, tabla_span=(BEATS[2] - 0.2, CLIMAX - 0.1),
                    run_up_at=BEAT0 - 0.3, run_down_at=CLIMAX + 0.1, bol_len=BEAT_LEN / 8)
    mix[: int(dur * SR)] += score

    # climax: gong, shankh and aarti hand-bells
    place(mix, gong(), CLIMAX, 0.42)
    place(mix, shankh(233, 3.2), CLIMAX + 0.3, 0.28)
    for at in (CLIMAX + 0.2, END):
        g = ghanti_scatter(3.4, hits=12)
        i = int(at * SR)
        mix[i:i + len(g)] += g * 0.09
    # Har Har Mahadev: big bell; credits: one last soft bell
    place(mix, temple_bell(293.66, 6.0), END + 0.05, 0.36)
    place(mix, temple_bell(880, 3.5), CREDITS, 0.12)

    mix[:, 0] = reverb(mix[:, 0], seconds=3.2, wet=0.36)
    mix[:, 1] = reverb(mix[:, 1], seconds=3.2, wet=0.36)
    mix = mix[: int(dur * SR)]
    mix *= np.clip((dur - t_axis(dur)) / 2.0, 0, 1)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1])
