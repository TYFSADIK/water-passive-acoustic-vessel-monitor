# Water: Passive Acoustic Vessel Monitor

Private research repo. A dock-mounted hydrophone node that detects and classifies passing vessels from underwater sound, using an RTL-SDR AIS receiver as ground truth. Solar powered.

Full write-up: [`docs/project-page.md`](docs/project-page.md)

## What's here

| File | Purpose |
|---|---|
| `hydro/dsp.py` | Broadband detector (running-median floor), LOFAR spectrogram, and **DEMON** envelope spectrum with a harmonic sieve to get **shaft RPM and blade count** |
| `hydro/ais.py` | AIS `!AIVDM` decoder (types 1–3 position, type 5 static with multi-fragment reassembly), NMEA checksum, ship-type classes, UDP listener for rtl-ais or AIS-catcher |
| `hydro/labels.py` | AIS as the labelling machine: closest-approach events, then labelled acoustic detections. Boats without AIS stay `unlabelled` |
| `hydro/capture.py` | 24-bit FLAC capture in UTC-named chunks |

## Quickstart

```bash
pip install numpy
python demo.py && python -m unittest -v
```

## Next steps
- [ ] T2 tank test: play known tones and modulated noise, and check the DEMON lines
- [ ] Run `rtl_ais -n` (or AIS-catcher) on the roof antenna and feed `ais.listen()` into a track store
- [ ] T4 field season: log broadband detections, label them with `labels.py`, and record range at first detection vs vessel class
- [ ] Classifier on [DEMON lines, RPM, blades, broadband level, LOFAR tonals]: gradient boosting first, then a small CNN on log-mel spectrograms once you have a few hundred labelled passes
- [ ] T5 sync-loss test: GPS PPS + chrony on the Pi, since a timing offset between audio and AIS corrupts the labels
