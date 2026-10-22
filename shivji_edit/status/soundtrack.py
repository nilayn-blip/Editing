"""Peaceful soundtrack for the Mahadev status reel (26.3 s), timed to make_index.py.

Calm and minimal, like the reference's "peaceful music": tanpura + soft drone + Sa-Pa pad, a slow
bansuri melody in Raga Shivaranjani, gentle santoor arpeggios on each caption change and a soft bell
on the last line. No percussion. Built from the synthesised instruments in ../sfx.py and ../music.py.

Usage: python3 soundtrack.py OUT.wav
"""
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from music import D, G, P, R, S, bansuri, pad, santoor_run  # noqa: E402
from sfx import SR, drone, om_choir, place, reverb, t_axis, tanpura_bed, temple_bell  # noqa: E402

# Output times; keep in sync with make_index.py
DUR = 26.3
IMG0 = 3.0
CAPTIONS = (3.0, 10.0, 17.0)
END = 24.0

FLUTE = [
    # intro, over the black quote card
    (0.6, S, 1.3), (2.0, R, 0.7), (2.7, G, 1.0),
    # "mila to unki kripa"
    (3.9, P, 1.6), (5.6, G, 0.8), (6.5, R, 0.8), (7.4, S, 2.2),
    # "nahi mila to unki ichchha"
    (10.5, D - 12, 0.9), (11.5, S, 1.0), (12.6, R, 0.9), (13.6, G, 2.8),
    # "bas bharosa rakho"
    (17.4, P, 1.1), (18.6, D, 1.1), (19.8, S + 12, 2.2), (22.1, D, 0.7), (22.9, P, 1.0),
    # Har Har Mahadev
    (24.2, G, 0.6), (24.8, R, 0.6), (25.4, S, 0.8),
]


def main(out_path):
    dur = DUR
    n = int(dur * SR)
    mix = np.zeros((n + SR * 8, 2))
    T = np.arange(mix.shape[0] + SR * 2) / SR

    tp = tanpura_bed(dur + 1)
    place(mix, tp * np.clip(T[: len(tp)] / 2.0, 0, 1), 0.0, 0.12)
    d = drone(dur + 1)
    place(mix, d * np.clip(T[: len(d)] / 2.5, 0, 1), 0.0, 0.07)
    p = pad(dur + 1)
    place(mix, p * np.clip((T[: len(p)] - 1.0) / 3.0, 0, 1), 0.0, 0.09)

    fl = bansuri(dur, FLUTE)
    place(mix, fl, 0.0, 0.30, pan=0.05)

    # soft santoor arpeggio on each caption change
    runs = [[S, G, P, S + 12], [R, P, D, R + 12], [G, D, S + 12, G + 12]]
    for k, t in enumerate(CAPTIONS):
        place(mix, santoor_run(runs[k], 0.12), t + 0.05, 0.09, pan=[-0.3, 0.3, 0.0][k])
    place(mix, om_choir(3.0), END - 0.2, 0.10)
    place(mix, temple_bell(587, 4.0), END, 0.16)

    mix[:, 0] = reverb(mix[:, 0], seconds=3.5, wet=0.4)
    mix[:, 1] = reverb(mix[:, 1], seconds=3.5, wet=0.4)
    mix = mix[:n]
    mix *= (np.clip(t_axis(dur) / 0.8, 0, 1) * np.clip((dur - t_axis(dur)) / 1.6, 0, 1))[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1])
