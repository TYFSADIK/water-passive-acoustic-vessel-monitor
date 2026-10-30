import unittest

import numpy as np

from hydro.ais import Decoder, checksum_ok, ship_class
from hydro.dsp import broadband_detector, demon, shaft_and_blades, synthetic_vessel
from hydro.labels import cpa_events, label_detections


class TestHydro(unittest.TestCase):
    def test_demon_rpm_blades(self):
        for rpm, blades in ((900, 3), (240, 4)):
            f, s = demon(synthetic_vessel(rpm=rpm, blades=blades, seconds=30), 48000)
            est = shaft_and_blades(f, s)
            self.assertEqual(est["blades"], blades)
            self.assertAlmostEqual(est["rpm"], rpm, delta=rpm * 0.05)

    def test_broadband_detects_pass(self):
        fs = 8000
        rng = np.random.default_rng(0)
        x = rng.normal(0, 0.1, fs * 200)
        x[fs * 150:fs * 170] += rng.normal(0, 1.0, fs * 20)
        t, lv, det = broadband_detector(x, fs, band=(200, 3000), floor_s=60)
        self.assertTrue(det[150:170].all())
        self.assertFalse(det[:140].any())

    def test_ais_position(self):
        m = Decoder().feed("!AIVDM,1,1,,B,15M67FC000G?ufbE`FepT@3n00Sa,0*5C")
        self.assertEqual(m.mmsi, 366053209)
        self.assertAlmostEqual(m.lat, 37.8, delta=0.1)
        self.assertFalse(checksum_ok("!AIVDM,1,1,,B,15M67FC000G?ufbE`FepT@3n00Sa,0*00"))
        self.assertEqual(ship_class(71), "cargo")

    def test_labelling(self):
        cp = cpa_events({1: [(0, 44.0, -63.0), (100, 44.001, -63.0)]}, (44.001, -63.0))
        out = label_detections([{"t": 90}, {"t": 9999}], cp, {1: "tanker"})
        self.assertEqual([o["label"] for o in out], ["tanker", "unlabelled"])


if __name__ == "__main__":
    unittest.main()
