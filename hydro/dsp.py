"""Hydrophone DSP: broadband detection, LOFAR lines, and DEMON propeller analysis.

DEMON (Detection of Envelope Modulation On Noise): propeller cavitation is
broadband noise amplitude-modulated at the shaft rate and blade rate. Band-pass
the cavitation band, take the envelope, and its spectrum shows lines at
shaft_hz and blades * shaft_hz. That gives RPM and blade count, which are strong
class cues (a 3-blade outboard at 1500 RPM vs a 5-blade freighter at 90 RPM).
"""
import numpy as np


def stft_power(x, fs, nfft=4096, hop=2048):
    win = np.hanning(nfft)
    frames = [x[i:i + nfft] * win for i in range(0, len(x) - nfft, hop)]
    P = np.abs(np.fft.rfft(np.array(frames), axis=1)) ** 2
    return P, np.fft.rfftfreq(nfft, 1 / fs), np.arange(len(frames)) * hop / fs


def bandpass_fft(x, fs, lo, hi):
    X = np.fft.rfft(x)
    f = np.fft.rfftfreq(len(x), 1 / fs)
    X[(f < lo) | (f > hi)] = 0
    return np.fft.irfft(X, n=len(x))


def broadband_detector(x, fs, band=(200, 8000), win_s=1.0, floor_s=120.0, k_db=6.0):
    """Energy per window vs a slow running-median noise floor. Returns (times, level_db, detect_mask)."""
    y = bandpass_fft(x, fs, *band)
    n = int(win_s * fs)
    lv = np.array([10 * np.log10(np.mean(y[i:i + n] ** 2) + 1e-20) for i in range(0, len(y) - n + 1, n)])
    m = max(3, int(floor_s / win_s))
    floor = np.array([np.median(lv[max(0, i - m):i + 1]) for i in range(len(lv))])
    return np.arange(len(lv)) * win_s, lv, lv > floor + k_db


def demon(x, fs, band=(2000, 10000), env_fs=500, max_hz=60):
    """Return (freqs, envelope spectrum normalised) up to max_hz."""
    y = bandpass_fft(x, fs, *band)
    env = np.abs(y)                                       # rectified envelope (no scipy needed)
    step = int(fs // env_fs)
    env = env[: len(env) // step * step].reshape(-1, step).mean(1)
    env -= env.mean()
    S = np.abs(np.fft.rfft(env * np.hanning(len(env))))
    f = np.fft.rfftfreq(len(env), 1 / env_fs)
    sel = (f > 0.5) & (f <= max_hz)
    return f[sel], S[sel] / (S[sel].max() + 1e-12)


def shaft_and_blades(freqs, spec, max_blades=7, min_rel=0.12):
    """Find the shaft rate f0 and blade count from DEMON lines (harmonic sieve).

    Blade rate is usually the strongest line; shaft rate = blade rate / blades.
    Lower-order harmonics alone are ambiguous (a 4-blade prop's 2x shaft line looks
    like the shaft of a 2-blade prop), so prefer the LARGEST blade count whose
    fundamental (shaft) line is present and whose harmonics are mostly supported.
    """
    def level(h):
        return spec[np.argmin(np.abs(freqs - h))]

    peak_f = freqs[np.argmax(spec)]
    best = {"shaft_hz": peak_f, "rpm": peak_f * 60, "blades": 1, "blade_rate_hz": peak_f, "support": 0.0}
    for blades in range(2, max_blades + 1):
        f0 = peak_f / blades
        if f0 < freqs[0]:
            break
        support = np.mean([level(k * f0) > min_rel for k in range(1, blades)])
        if level(f0) > min_rel and support >= 0.5:
            best = {"shaft_hz": f0, "rpm": f0 * 60, "blades": blades, "blade_rate_hz": peak_f, "support": float(support)}
    return best


def synthetic_vessel(fs=48000, seconds=20, rpm=900, blades=3, snr_db=0, rng=None):
    rng = rng or np.random.default_rng(0)
    t = np.arange(int(fs * seconds)) / fs
    f0 = rpm / 60
    mod = 1 + 0.6 * np.cos(2 * np.pi * blades * f0 * t) + 0.25 * np.cos(2 * np.pi * f0 * t) + 0.15 * np.cos(2 * np.pi * 2 * f0 * t)
    cav = rng.normal(size=t.size) * mod
    tonal = 0.3 * np.sin(2 * np.pi * 60 * t)              # machinery/generator line
    sea = rng.normal(size=t.size) * 10 ** (-snr_db / 20)
    return cav + tonal + sea
