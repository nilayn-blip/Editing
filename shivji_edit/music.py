"""Original devotional score for the Shivji temple edit (fully synthesised, copyright-free).

Raga Shivaranjani (S R g P D, Sa = D) over the tanpura bed in sfx.py:
  - santoor shimmer on the hook -> wide cut and into the end card
  - bansuri (bamboo flute) alaap over the wide shot, melody over the darshan, resolving to Sa
  - soft tabla keherwa under the darshan hold
  - warm Sa-Pa string pad

compose(dur) returns a dry stereo float array at 48 kHz; sfx.py adds reverb and mixes it.
"""
import numpy as np
from scipy.signal import lfilter

from sfx import SR, bandpass, highpass, lowpass, rng, t_axis

SA = 293.66  # D4, an octave above the tanpura Sa
# Shivaranjani degrees in semitones above Sa
S, R, G, P, D = 0, 2, 3, 7, 9


def hz(semi):
    return SA * 2 ** (semi / 12)


# ------------------------------------------------------------------ bansuri
# (start s, semitone, length s)
FLUTE = [
    # alaap over the wide shot
    (1.55, P, 0.50), (2.05, D, 0.40), (2.45, S + 12, 1.10), (3.55, D, 0.32), (3.87, P, 0.75),
    # melody over the darshan
    (4.55, G, 0.40), (4.95, R, 0.33), (5.28, G, 0.50), (5.78, P, 0.90),
    (6.68, D, 0.40), (7.08, S + 12, 0.45), (7.53, R + 12, 0.35), (7.88, S + 12, 0.50),
    (8.38, D, 0.40), (8.78, P, 0.85),
    # resolution under the end card
    (9.70, G, 0.60), (10.30, R, 0.60), (10.90, S, 1.55),
]


def bansuri(dur, notes=FLUTE):
    t = t_axis(dur)
    semi = np.full(len(t), np.nan)
    amp = np.zeros(len(t))
    vib_gate = np.zeros(len(t))
    for start, note, length in notes:
        i0, i1 = int(start * SR), min(len(t), int((start + length) * SR))
        semi[i0:i1] = note
        lt = t[i0:i1] - start
        env = np.clip(lt / 0.06, 0, 1) * np.clip((length - lt) / 0.14, 0, 1) ** 0.7
        amp[i0:i1] = np.maximum(amp[i0:i1], env)
        vib_gate[i0:i1] = np.clip((lt - 0.25) / 0.3, 0, 1)
    # hold pitch through rests, then glide (meend) between notes with a one-pole smoother
    first = np.flatnonzero(~np.isnan(semi))[0]
    semi[:first] = semi[first]
    for i in range(1, len(semi)):
        if np.isnan(semi[i]):
            semi[i] = semi[i - 1]
    a = np.exp(-1 / (0.045 * SR))
    semi = lfilter([1 - a], [1, -a], semi, zi=[semi[0] * a])[0]
    semi += 0.22 * vib_gate * np.sin(2 * np.pi * 5.4 * t)
    phase = 2 * np.pi * np.cumsum(hz(semi)) / SR
    tone = np.sin(phase) + 0.22 * np.sin(2 * phase) + 0.07 * np.sin(3 * phase)
    breath = bandpass(rng.standard_normal(len(t)), 900, 3200) * 0.10
    chiff = highpass(rng.standard_normal(len(t)), 2500) * 0.15
    attack = np.zeros(len(t))
    for start, _, _ in notes:
        i0 = int(start * SR)
        n = min(len(t) - i0, int(0.05 * SR))
        attack[i0:i0 + n] = np.exp(-np.arange(n) / (0.012 * SR))
    y = (tone + breath) * amp + chiff * attack * 0.5
    return lowpass(y, 6000) / np.abs(y).max()


# ------------------------------------------------------------------ santoor
def santoor_note(f, dur=1.6):
    t = t_axis(dur)
    y = np.zeros_like(t)
    for k, a, d in [(1, 1.0, 0.9), (2.005, 0.45, 0.5), (3.01, 0.25, 0.3), (4.02, 0.12, 0.2)]:
        # paired strings, slightly detuned, for the santoor chorus
        y += a * (np.sin(2 * np.pi * f * k * t) + np.sin(2 * np.pi * f * k * 1.003 * t)) * np.exp(-t / d)
    y += highpass(rng.standard_normal(len(t)), 3000) * np.exp(-t / 0.004) * 0.6  # hammer
    return y / np.abs(y).max()


def santoor_run(notes, step):
    seq = [santoor_note(hz(n)) for n in notes]
    out = np.zeros(int((len(notes) * step + 1.7) * SR))
    for k, s in enumerate(seq):
        i = int(k * step * SR)
        out[i:i + len(s)] += s * (0.6 + 0.4 * k / len(seq))
    return out / np.abs(out).max()


# ------------------------------------------------------------------ tabla
def _bayan(t, boom=True):
    if not boom:  # 'ka': flat slap
        return lowpass(rng.standard_normal(len(t)), 600) * np.exp(-t / 0.02) * 0.7
    f = 85 + 25 * (1 - np.exp(-t / 0.08))  # 'ghe' pitch rise
    return np.sin(2 * np.pi * np.cumsum(f) / SR) * np.exp(-t / 0.28)


def _dayan(t, open_=True):
    d = 0.22 if open_ else 0.045
    y = sum(a * np.sin(2 * np.pi * SA * k * t) * np.exp(-t / (d / k ** 0.3)) for k, a in [(1, 1), (2, 0.6), (3, 0.35), (4, 0.2)])
    return y + bandpass(rng.standard_normal(len(t)), 2000, 6000) * np.exp(-t / 0.006) * (0.3 if open_ else 0.8)


def tabla_bol(bol):
    t = t_axis(0.6)
    return {
        "dha": _bayan(t) * 0.8 + _dayan(t),
        "ge": _bayan(t),
        "na": _dayan(t),
        "ti": _dayan(t, False) * 0.7,
        "ka": _bayan(t, False),
        "dhi": _bayan(t) * 0.8 + _dayan(t, False),
    }[bol]


KEHERWA = ["dha", "ge", "na", "ti", "na", "ka", "dhi", "na"]


def tabla(start, end, bol_len=0.395):
    out = np.zeros(int((end + 1) * SR))
    t, k = start, 0
    while t < end:
        b = tabla_bol(KEHERWA[k % 8])
        accent = 1.0 if k % 8 in (0, 6) else 0.7
        i = int(t * SR)
        out[i:i + len(b)] += b * accent
        t += bol_len
        k += 1
    return out / np.abs(out).max()


# ------------------------------------------------------------------ pad
def pad(dur):
    t = t_axis(dur)
    y = np.zeros_like(t)
    for f in (SA / 2, SA * 3 / 4, SA):  # Sa - Pa - Sa'
        for det in (-0.004, 0.0, 0.004):
            ph = (f * (1 + det) * t) % 1.0
            y += 2 * ph - 1  # saw
    y = lowpass(y, 1100)
    return y / np.abs(y).max()


# ------------------------------------------------------------------ score
def compose(dur, flute=FLUTE, tabla_span=(4.1, 9.25), run_up_at=0.62, run_down_at=9.25):
    n = int(dur * SR)
    T = t_axis(dur)
    L = np.zeros(n)
    R_ = np.zeros(n)

    def add(x, at, gain, pan=0.0):
        i = int(at * SR)
        m = min(len(x), n - i)
        if m <= 0:
            return
        L[i:i + m] += x[:m] * gain * np.cos((pan + 1) * np.pi / 4) * 1.414
        R_[i:i + m] += x[:m] * gain * np.sin((pan + 1) * np.pi / 4) * 1.414

    p = pad(dur)
    p_env = np.clip((T - 0.6) / 2.0, 0, 1) * (0.75 + 0.25 * np.clip((T - 4.1) / 1.5, 0, 1)) * np.clip((dur - T) / 1.5, 0, 1)
    add(p * p_env, 0, 0.10)

    add(santoor_run([S, R, G, P, D, S + 12, R + 12, G + 12, P + 12], 0.055), run_up_at, 0.20, pan=-0.2)
    add(santoor_run([P + 12, G + 12, R + 12, S + 12, D, P, G, R, S], 0.07), run_down_at, 0.16, pan=0.2)

    add(bansuri(dur, flute), 0, 0.30, pan=0.05)

    t0, t1 = tabla_span
    tb = tabla(t0, t1)
    tb_env = np.clip((T[: len(tb)] - t0) / 0.8, 0, 1) * np.clip((t1 + 0.25 - T[: len(tb)]) / 0.4, 0, 1)
    add(tb * tb_env, 0, 0.22, pan=-0.1)

    return np.stack([L, R_], axis=1)
