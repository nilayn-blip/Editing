"""Synthesize the sound design for the Shivji temple edit.

Everything is generated procedurally (no third-party samples), so the
result is royalty-free. Output: 48 kHz stereo WAV of SFX only; the
original location audio is mixed in later by build.sh.

Usage: python3 sfx.py OUT.wav DURATION_SECONDS
"""
import sys

import numpy as np
from scipy.io import wavfile
from scipy.signal import butter, sosfilt, fftconvolve

SR = 48000
rng = np.random.default_rng(108)


def t_axis(dur):
    return np.arange(int(dur * SR)) / SR


def lowpass(x, hz, order=4):
    return sosfilt(butter(order, hz, "low", fs=SR, output="sos"), x)


def highpass(x, hz, order=4):
    return sosfilt(butter(order, hz, "high", fs=SR, output="sos"), x)


def bandpass(x, lo, hi, order=4):
    return sosfilt(butter(order, [lo, hi], "band", fs=SR, output="sos"), x)


def temple_bell(f0=520.0, dur=4.5):
    """Struck brass bell: inharmonic partials, each with its own decay."""
    t = t_axis(dur)
    # ratios of a typical temple ghanta (hum, prime, tierce, quint, nominal...)
    partials = [(0.5, 0.55, 3.2), (1.0, 1.0, 2.4), (1.19, 0.55, 1.9),
                (1.5, 0.35, 1.5), (2.0, 0.45, 1.2), (2.51, 0.25, 0.8),
                (2.93, 0.18, 0.6), (3.76, 0.12, 0.4), (4.8, 0.08, 0.25)]
    y = np.zeros_like(t)
    for ratio, amp, decay in partials:
        f = f0 * ratio
        beat = 1 + 0.15 * np.sin(2 * np.pi * (0.8 + ratio * 0.3) * t)  # shimmer
        y += amp * beat * np.sin(2 * np.pi * f * t + rng.uniform(0, 6.28)) * np.exp(-t / decay)
    strike = highpass(rng.standard_normal(len(t)), 2500) * np.exp(-t / 0.006) * 0.6
    y = y + strike
    return y / np.abs(y).max()


def shankh(f0=233.0, dur=3.2):
    """Conch blow: breathy nasal tone with slow swell, pitch bend and vibrato."""
    t = t_axis(dur)
    env = np.clip(t / 0.5, 0, 1) ** 1.5 * np.clip((dur - t) / 0.9, 0, 1)
    bend = 1 - 0.06 * np.exp(-t / 0.25)  # starts slightly flat, rises into pitch
    vib = 1 + 0.006 * np.sin(2 * np.pi * 5.2 * t) * np.clip(t - 0.6, 0, 1)
    phase = 2 * np.pi * np.cumsum(f0 * bend * vib) / SR
    y = np.zeros_like(t)
    for k, a in enumerate([1.0, 0.7, 0.55, 0.3, 0.22, 0.12, 0.08, 0.05], start=1):
        y += a * np.sin(k * phase)
    y = np.tanh(1.6 * y)  # reedy saturation
    breath = bandpass(rng.standard_normal(len(t)), 800, 3500) * 0.12
    y = lowpass(y + breath, 3200) * env
    return y / np.abs(y).max()


def whoosh(dur=1.0, rise=True):
    """Filtered-noise sweep for zoom transitions."""
    t = t_axis(dur)
    n = rng.standard_normal(len(t))
    pos = t / dur if rise else 1 - t / dur
    # crude time-varying bandpass: crossfade between filtered copies
    bands = [bandpass(n, 200 * 1.6 ** i, 200 * 1.6 ** i * 2.2, 2) for i in range(7)]
    idx = pos * (len(bands) - 1)
    y = np.zeros_like(t)
    for i, b in enumerate(bands):
        y += b * np.clip(1 - np.abs(idx - i), 0, 1)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    y *= env
    return y / np.abs(y).max()


def damru(dur=1.4, start_rate=7.0, end_rate=16.0):
    """Accelerating two-headed drum roll (alternating high/low membrane hits)."""
    out = np.zeros(int(dur * SR))
    t = 0.0
    k = 0
    while t < dur - 0.15:
        rate = start_rate + (end_rate - start_rate) * (t / dur)
        f = 180 if k % 2 == 0 else 145
        hl = t_axis(0.15)
        hit = np.sin(2 * np.pi * f * hl * (1 + 0.5 * np.exp(-hl / 0.01))) * np.exp(-hl / 0.045)
        hit += 0.3 * bandpass(rng.standard_normal(len(hl)), 1000, 4000) * np.exp(-hl / 0.008)
        i = int(t * SR)
        out[i:i + len(hit)] += hit * (0.7 + 0.3 * (t / dur))
        t += 1 / rate
        k += 1
    out *= np.clip((dur - t_axis(dur)) / 0.1, 0, 1)
    return out / np.abs(out).max()


def drone(dur, f0=73.4):
    """Soft low 'Om' pad sitting under everything."""
    t = t_axis(dur)
    y = np.zeros_like(t)
    for k, a in [(1, 1.0), (2, 0.5), (3, 0.25), (4, 0.18), (6, 0.08)]:
        y += a * np.sin(2 * np.pi * f0 * k * t * (1 + 0.0015 * k))
        y += a * 0.6 * np.sin(2 * np.pi * f0 * k * t * (1 - 0.0012 * k))
    y *= 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t)
    y = lowpass(y, 900)
    return y / np.abs(y).max()


def reverb(x, seconds=2.5, wet=0.35):
    ir_t = t_axis(seconds)
    ir = rng.standard_normal(len(ir_t)) * np.exp(-ir_t / (seconds / 6))
    ir = lowpass(ir, 6000)
    ir /= np.sqrt((ir ** 2).sum())
    w = fftconvolve(x, ir)[: len(x)]
    return (1 - wet) * x + wet * w * 3


def place(track, clip, at, gain, pan=0.0):
    i = int(at * SR)
    n = min(len(clip), track.shape[0] - i)
    if n <= 0:
        return
    l, r = np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4)
    track[i:i + n, 0] += clip[:n] * gain * l * 1.414
    track[i:i + n, 1] += clip[:n] * gain * r * 1.414


def main(out_path, dur):
    mix = np.zeros((int(dur * SR) + SR * 4, 2))

    # bed: low drone fades in, swells under the end card
    d = drone(dur + 1)
    env = np.clip(t_axis(dur + 1) / 1.5, 0, 1) * np.clip((dur - t_axis(dur + 1)) / 1.2, 0, 1)
    place(mix, d * env, 0.0, 0.10)

    # opening: conch + bell under the title
    place(mix, shankh(), 0.05, 0.40)
    place(mix, temple_bell(520), 0.45, 0.30, pan=-0.25)

    # camera punch-in towards the shivling (1.17s - 2.8s)
    place(mix, whoosh(1.5, rise=True), 1.05, 0.30)
    place(mix, temple_bell(620, 5.0), 2.75, 0.38, pan=0.2)  # lands on the darshan

    # hold on the deity: damru roll building to the lower-third
    place(mix, damru(1.3), 3.35, 0.26, pan=0.15)
    place(mix, temple_bell(780, 3.5), 4.7, 0.20, pan=-0.3)

    # small reframe (7.2s) and pull-out (8.4s - 9.2s)
    place(mix, whoosh(0.6, rise=True), 7.05, 0.12)
    place(mix, whoosh(1.2, rise=False), 8.3, 0.24)

    # end card
    place(mix, temple_bell(520, 5.0), 9.6, 0.36)
    place(mix, shankh(233, 3.4), 10.4, 0.30)
    place(mix, temple_bell(780, 4.0), 11.3, 0.18, pan=0.3)

    mix[:, 0] = reverb(mix[:, 0], wet=0.30)
    mix[:, 1] = reverb(mix[:, 1], wet=0.30)
    mix = mix[: int(dur * SR)]
    fade = np.clip((dur - t_axis(dur)) / 0.8, 0, 1)
    mix *= fade[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]))
