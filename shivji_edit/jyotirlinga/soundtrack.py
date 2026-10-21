"""Soundtrack for the Dwadash Jyotirlinga edit (55.5 s), timed to project/index.html.

Reuses the synthesised instruments in ../sfx.py and the Raga Shivaranjani score in ../music.py:
tabla keherwa throughout (one 8-bol cycle per temple), a bansuri melody extended over all 12
beats, and a temple bell on every temple change.

Usage: python3 soundtrack.py OUT.wav
"""
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from music import D, G, P, R, S, compose  # noqa: E402
from sfx import (SR, drone, ghanti_scatter, om_choir, place, reverb, shankh,  # noqa: E402
                 t_axis, tanpura_bed, temple_bell, whoosh)

# Output times; keep in sync with index.html
DUR = 55.5
INTRO = 0.0
BEAT0, BEAT_LEN, N = 3.2, 3.6, 12
OUTRO = BEAT0 + N * BEAT_LEN  # 46.4: ring complete, Har Har Mahadev
CREDITS = 50.6
BEATS = [BEAT0 + k * BEAT_LEN for k in range(N)]
BOL = BEAT_LEN / 8  # one keherwa cycle per temple

# Four bansuri phrases (offset in beat, semitone, length), cycled over the 12 temples
PHRASES = {
    "A": [(0.15, G, 0.45), (0.60, R, 0.40), (1.00, G, 0.50), (1.50, P, 1.00), (2.60, D, 0.40), (3.00, P, 0.45)],
    "B": [(0.15, D, 0.40), (0.55, S + 12, 0.45), (1.00, R + 12, 0.40), (1.40, S + 12, 0.60), (2.10, D, 0.45), (2.60, P, 0.85)],
    "C": [(0.15, P, 0.40), (0.55, D, 0.40), (0.95, S + 12, 1.00), (2.05, D, 0.35), (2.40, P, 0.40), (2.80, G, 0.65)],
    "D": [(0.15, G, 0.40), (0.55, P, 0.45), (1.00, D, 0.50), (1.50, P, 0.40), (1.90, G, 0.40), (2.30, R, 0.40), (2.70, S, 0.75)],
}
ORDER = "ABCDABCDACBD"


def flute_line():
    notes = [  # alaap under the title
        (0.55, P, 0.50), (1.05, D, 0.40), (1.45, S + 12, 1.00), (2.45, D, 0.30), (2.75, P, 0.40),
    ]
    for k, ph in enumerate(ORDER):
        notes += [(BEATS[k] + o, n, ln) for o, n, ln in PHRASES[ph]]
    # resolution to Sa as the ring completes, held into the credits
    notes += [(OUTRO + 0.6, G, 0.70), (OUTRO + 1.3, R, 0.70), (OUTRO + 2.0, S, 2.60)]
    return notes


def main(out_path):
    dur = DUR
    mix = np.zeros((int(dur * SR) + SR * 6, 2))
    T = np.arange(mix.shape[0] + SR * 2) / SR

    tp = tanpura_bed(dur + 1)
    tp_env = np.clip((T[: len(tp)] - 0.3) / 1.5, 0, 1) * np.clip((dur - T[: len(tp)]) / 2.5, 0, 1)
    place(mix, tp * tp_env, 0.0, 0.12)
    d = drone(dur + 1)
    place(mix, d * np.clip(T[: len(d)] / 1.0, 0, 1) * np.clip((dur - T[: len(d)]) / 2.0, 0, 1), 0.0, 0.08)

    # intro: shankh + Om, bell lands on the title
    place(mix, om_choir(3.4), INTRO, 0.20)
    place(mix, shankh(), 0.15, 0.30)
    place(mix, temple_bell(520, 5.0), 0.9, 0.30, pan=0.1)

    # a bell (cycling raga pitches) and a soft whoosh on every temple change
    bell_hz = [587, 660, 698, 784, 880, 523]  # Sa Re ga Pa Dha (and Pa below) around D5
    for k, b in enumerate(BEATS):
        place(mix, whoosh(0.7, rise=True), b - 0.55, 0.07, pan=0.3 if k % 2 else -0.3)
        place(mix, temple_bell(bell_hz[k % len(bell_hz)], 3.0), b, 0.18, pan=[-0.25, 0.25][k % 2])
    # aarti hand-bells on the Kashi Vishwanath beat and the final temple
    for k in (6, 11):
        g = ghanti_scatter(2.0, hits=7)
        i = int(BEATS[k] * SR)
        mix[i:i + len(g)] += g * 0.08

    score = compose(dur, flute=flute_line(), tabla_span=(BEAT0 - 0.1, OUTRO + 0.4),
                    run_up_at=BEAT0 - 0.6, run_down_at=OUTRO - 0.05, bol_len=BOL)
    mix[: int(dur * SR)] += score

    # outro: all 12 lights complete
    place(mix, temple_bell(293.66 * 2, 6.0), OUTRO, 0.36)
    place(mix, om_choir(4.0), OUTRO + 0.2, 0.24)
    place(mix, shankh(233, 3.0), OUTRO + 0.9, 0.26)
    # credits: one last soft bell
    place(mix, temple_bell(880, 4.0), CREDITS, 0.14)

    mix[:, 0] = reverb(mix[:, 0], wet=0.30)
    mix[:, 1] = reverb(mix[:, 1], wet=0.30)
    mix = mix[: int(dur * SR)]
    mix *= np.clip((dur - t_axis(dur)) / 2.0, 0, 1)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1])
