"""Soundtrack for the HyperFrames Mahakal edit (15.5 s), timed to prep_footage.sh and index.html.

Reuses the synthesised instruments in ../sfx.py and the Raga Shivaranjani score in ../music.py.

Usage: python3 soundtrack.py OUT.wav [AMBIENCE.wav]
"""
import os
import sys

import numpy as np
from scipy.io import wavfile

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))

from music import D, G, P, R, S, compose  # noqa: E402
from sfx import (SR, damru, drone, ghanti_scatter, highpass, om_choir, place, reverb,  # noqa: E402
                 shankh, t_axis, tanpura_bed, temple_bell, whoosh)

DUR = 15.5

# Output times; keep in sync with index.html
CUT_WIDE, CUT_ZOOM, CUT_HOLD, CUT_END = 0.90, 2.07, 4.07, 11.2
BEATS = (4.55, 6.75, 8.95)  # 12 Jyotirlingas / south-facing / Bhasma Aarti

FLUTE = [
    # alaap over the wide shot
    (1.55, P, 0.50), (2.05, D, 0.40), (2.45, S + 12, 1.10), (3.55, D, 0.32), (3.87, P, 0.75),
    # melody over the darshan
    (4.60, G, 0.45), (5.05, R, 0.40), (5.45, G, 0.55), (6.00, P, 1.00),
    (7.10, D, 0.45), (7.55, S + 12, 0.50), (8.05, R + 12, 0.40), (8.45, S + 12, 0.55),
    (9.00, D, 0.50), (9.50, P, 1.10), (10.70, D, 0.45),
    # resolution under the Lord of Time end card
    (11.70, G, 0.70), (12.40, R, 0.70), (13.10, S, 1.90),
]


def kaal_gong():
    """Deep gong + sub boom for the 'Mahakal' hook."""
    g = temple_bell(180, 6.0)
    t = t_axis(6.0)
    boom = np.sin(2 * np.pi * 52 * t * (1 + 0.3 * np.exp(-t / 0.08))) * np.exp(-t / 1.2)
    y = 0.7 * g + 0.6 * boom
    return y / np.abs(y).max()


def clock_tick():
    t = t_axis(0.08)
    y = np.sin(2 * np.pi * 2600 * t) * np.exp(-t / 0.012)
    y += highpass(np.random.default_rng(3).standard_normal(len(t)), 3000) * np.exp(-t / 0.002) * 0.5
    return y / np.abs(y).max()


def main(out_path, amb_path=None):
    dur = DUR
    mix = np.zeros((int(dur * SR) + SR * 6, 2))
    T = np.arange(mix.shape[0] + SR * 2) / SR

    tp = tanpura_bed(dur + 1)
    tp_env = np.clip((T[: len(tp)] - 0.9) / 1.5, 0, 1) * np.clip((dur - T[: len(tp)]) / 1.6, 0, 1)
    place(mix, tp * tp_env, 0.0, 0.12)
    d = drone(dur + 1)
    place(mix, d * np.clip(T[: len(d)] / 1.0, 0, 1) * np.clip((dur - T[: len(d)]) / 1.2, 0, 1), 0.0, 0.09)

    if amb_path:
        sr, amb = wavfile.read(amb_path)
        amb = amb.astype(float) / 32768
        if amb.ndim == 1:
            amb = np.stack([amb, amb], axis=1)
        n = min(len(amb), int((CUT_END - 0.2) * SR))
        env = np.clip(t_axis(n / SR) / 0.5, 0, 1) * np.clip((n / SR - t_axis(n / SR)) / 1.5, 0, 1)
        mix[:n] += amb[:n] * env[:, None] * 0.28

    # hook: Mahakal gong + chant, riser into the flash cut
    place(mix, kaal_gong(), 0.02, 0.42)
    place(mix, om_choir(3.6), 0.0, 0.20)
    place(mix, whoosh(0.6, rise=True), 0.4, 0.20)

    # wide shot + title
    place(mix, shankh(), 0.95, 0.34)

    # push-in, damru builds into the darshan, bell lands
    place(mix, whoosh(1.9, rise=True), 2.05, 0.26)
    place(mix, damru(1.1, 6.0, 18.0), 2.95, 0.20, pan=0.15)
    place(mix, temple_bell(520, 5.0), CUT_HOLD - 0.02, 0.36, pan=0.15)

    # one soft chime per info beat
    for k, b in enumerate(BEATS):
        place(mix, temple_bell([880, 780, 980][k], 2.5), b, 0.14, pan=[-0.3, 0.3, 0.0][k])
    # Bhasma Aarti beat: hand-bells of the aarti
    g = ghanti_scatter(2.2, hits=9)
    i = int(BEATS[2] * SR)
    mix[i:i + len(g)] += g * 0.12

    score = compose(dur, flute=FLUTE, tabla_span=(CUT_HOLD, 10.95), run_up_at=0.62, run_down_at=CUT_END - 0.1)
    mix[: int(dur * SR)] += score

    # end card: Lord of Time
    place(mix, whoosh(0.5, rise=False), CUT_END - 0.15, 0.12)
    place(mix, temple_bell(520, 5.0), CUT_END + 0.1, 0.34)
    place(mix, om_choir(3.6), CUT_END, 0.22)
    tick = clock_tick()
    for k in range(4):
        place(mix, tick, CUT_END + 0.6 + k, 0.05 + 0.01 * k, pan=0.2 if k % 2 else -0.2)
    place(mix, shankh(233, 2.8), CUT_END + 1.0, 0.24)
    place(mix, kaal_gong(), CUT_END + 2.4, 0.22)

    mix[:, 0] = reverb(mix[:, 0], wet=0.30)
    mix[:, 1] = reverb(mix[:, 1], wet=0.30)
    mix = mix[: int(dur * SR)]
    mix *= np.clip((dur - t_axis(dur)) / 0.9, 0, 1)[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
