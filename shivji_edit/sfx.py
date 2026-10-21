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


def tanpura_note(f0, dur=4.2):
    """Additive tanpura pluck: bright harmonics with the moving 'jawari' buzz peak."""
    t = t_axis(dur)
    y = np.zeros_like(t)
    centre = 4 + 18 * np.exp(-t / 1.4)  # buzz formant sweeps down the harmonics
    for k in range(1, 36):
        if f0 * k > 9000:
            break
        base = 1 / k ** 0.9
        buzz = 1 + 2.5 * np.exp(-((k - centre) ** 2) / 10)
        detune = 1 + 0.0008 * np.sin(2 * np.pi * 0.3 * t + k)
        y += base * buzz * np.sin(2 * np.pi * f0 * k * detune * t + rng.uniform(0, 6.28))
    y *= np.exp(-t / 2.2) * np.clip(t / 0.004, 0, 1)
    return y / np.abs(y).max()


def tanpura_bed(dur, sa=146.83, cycle=2.6):
    """Classic Pa-Sa-Sa-Sa(low) cycle."""
    out = np.zeros(int(dur * SR) + SR * 5)
    pattern = [(0.0, sa * 3 / 4), (0.65, sa), (1.0, sa), (1.6, sa / 2)]
    t0 = 0.0
    while t0 < dur:
        for off, f in pattern:
            n = tanpura_note(f)
            i = int((t0 + off) * SR)
            m = min(len(n), len(out) - i)
            if m > 0:
                out[i:i + m] += n[:m] * (0.8 if f < sa else 0.6)
        t0 += cycle
    out = out[: int(dur * SR)]
    return out / np.abs(out).max()


def om_choir(dur, f0s=(73.42, 146.83, 110.0)):
    """Formant-synthesised group chant of 'Om': open 'o' vowel closing into a nasal 'm' hum."""
    t = t_axis(dur)
    close = np.clip((t / dur - 0.45) / 0.2, 0, 1)  # 0 = 'o', 1 = 'm'
    formants_o = [(500, 90, 1.0), (850, 110, 0.6), (2500, 200, 0.12)]
    formants_m = [(260, 60, 1.0), (1000, 150, 0.06), (2300, 200, 0.02)]
    env = np.clip(t / 0.7, 0, 1) ** 1.3 * np.clip((dur - t) / 1.0, 0, 1)
    y = np.zeros_like(t)
    for v, f0 in enumerate(f0s):
        for voice in range(3):
            fv = f0 * (1 + 0.003 * (voice - 1))
            vib = 1 + 0.004 * np.sin(2 * np.pi * (4.8 + 0.4 * voice) * t + v + voice)
            phase = 2 * np.pi * np.cumsum(fv * vib) / SR
            for k in range(1, 50):
                fk = fv * k
                if fk > 4000:
                    break
                g_o = sum(a * np.exp(-((fk - f) ** 2) / (2 * bw ** 2)) for f, bw, a in formants_o)
                g_m = sum(a * np.exp(-((fk - f) ** 2) / (2 * bw ** 2)) for f, bw, a in formants_m)
                amp = (1 - close) * g_o + close * g_m * 1.3
                y += amp * np.sin(k * phase + rng.uniform(0, 6.28)) / k ** 0.5
    breath = bandpass(rng.standard_normal(len(t)), 400, 1800) * 0.02 * (1 - close)
    y = (y / np.abs(y).max() + breath) * env
    return y / np.abs(y).max()


def ghanti_scatter(dur, hits=7):
    """Distant small hand-bells rung by other devotees."""
    out = np.zeros((int(dur * SR) + SR * 3, 2))
    for _ in range(hits):
        at = rng.uniform(0, dur - 0.5)
        b = temple_bell(rng.uniform(1100, 1700), 2.0)
        place(out, b, at, rng.uniform(0.25, 0.5), pan=rng.uniform(-0.8, 0.8))
    return out[: int(dur * SR)]


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
    mix = np.zeros((int(dur * SR) + SR * 6, 2))
    T = np.arange(mix.shape[0] + SR * 2) / SR

    # musical bed: tanpura from the first cut, low drone underneath
    tp = tanpura_bed(dur + 1)
    tp_env = np.clip((T[: len(tp)] - 0.9) / 1.5, 0, 1) * np.clip((dur - T[: len(tp)]) / 1.6, 0, 1)
    place(mix, tp * tp_env, 0.0, 0.16)
    d = drone(dur + 1)
    place(mix, d * np.clip(T[: len(d)] / 1.0, 0, 1) * np.clip((dur - T[: len(d)]) / 1.2, 0, 1), 0.0, 0.09)

    # hook (0 - 0.9s): bell strike + chant, riser into the flash cut
    place(mix, temple_bell(620, 5.0), 0.02, 0.40)
    place(mix, om_choir(3.6), 0.0, 0.20)
    place(mix, whoosh(0.6, rise=True), 0.4, 0.20)

    # wide shot + title
    place(mix, shankh(), 0.95, 0.36)

    # slowed push-in (2.07s - 4.1s), lands on the darshan
    place(mix, whoosh(1.9, rise=True), 2.05, 0.28)
    place(mix, temple_bell(520, 5.0), 4.05, 0.38, pan=0.15)

    # darshan hold (4.1s - 9.5s): damru into the lower third, distant ghantis
    place(mix, damru(1.3), 4.3, 0.24, pan=0.15)
    g = ghanti_scatter(5.0)
    i = int(4.4 * SR)
    mix[i:i + len(g)] += g * 0.10
    place(mix, temple_bell(780, 3.5), 6.4, 0.18, pan=-0.3)

    # end card (9.35s ->)
    place(mix, whoosh(0.5, rise=False), 9.2, 0.12)
    place(mix, temple_bell(520, 5.0), 9.45, 0.36)
    place(mix, om_choir(3.2), 9.3, 0.22)
    place(mix, shankh(233, 2.6), 10.1, 0.26)
    place(mix, temple_bell(780, 3.5), 11.1, 0.16, pan=0.3)

    mix[:, 0] = reverb(mix[:, 0], wet=0.30)
    mix[:, 1] = reverb(mix[:, 1], wet=0.30)
    mix = mix[: int(dur * SR)]
    fade = np.clip((dur - t_axis(dur)) / 0.8, 0, 1)
    mix *= fade[:, None]
    mix /= max(1.0, np.abs(mix).max() / 0.89)
    wavfile.write(out_path, SR, (mix * 32767).astype(np.int16))


if __name__ == "__main__":
    main(sys.argv[1], float(sys.argv[2]))
