"""Field capture: hydrophone via USB audio (e.g. Aquarian H2a into a 24-bit interface) to FLAC chunks with UTC names.

    python -m hydro.capture --device 1 --fs 48000 --out data/raw/
Requires: sounddevice, soundfile. Keep raw audio OUT of git (data/raw is ignored).
"""
import argparse
import datetime as dt
import os


def main():
    import sounddevice as sd
    import soundfile as sf
    ap = argparse.ArgumentParser()
    ap.add_argument("--device", type=int, default=None)
    ap.add_argument("--fs", type=int, default=48000)
    ap.add_argument("--chunk-s", type=int, default=300)
    ap.add_argument("--out", default="data/raw")
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    while True:
        start = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        rec = sd.rec(a.chunk_s * a.fs, samplerate=a.fs, channels=1, dtype="int32", device=a.device)
        sd.wait()
        sf.write(os.path.join(a.out, f"hyd_{start}.flac"), rec, a.fs, subtype="PCM_24")


if __name__ == "__main__":
    main()
