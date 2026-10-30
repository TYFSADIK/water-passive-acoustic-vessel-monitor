"""Run: python demo.py  -> DEMON recovers RPM and blade count; AIS decode; auto-labelling."""
from hydro.ais import Decoder
from hydro.dsp import demon, shaft_and_blades, synthetic_vessel
from hydro.labels import cpa_events, label_detections

for rpm, blades in ((900, 3), (150, 5)):
    f, s = demon(synthetic_vessel(rpm=rpm, blades=blades), 48000)
    est = shaft_and_blades(f, s)
    print(f"true {rpm} RPM / {blades} blades -> est {est['rpm']:.0f} RPM / {est['blades']} blades (blade rate {est['blade_rate_hz']:.1f} Hz)")

d = Decoder()
print(d.feed("!AIVDM,1,1,,B,15M67FC000G?ufbE`FepT@3n00Sa,0*5C"))

site = (44.65, -63.57)
tracks = {316001234: [(t, 44.64 + t * 1e-5, -63.575) for t in range(0, 2000, 60)]}
cpas = cpa_events(tracks, site)
print(label_detections([{"t": 1000}, {"t": 5000}], cpas, {316001234: "tug"}))
