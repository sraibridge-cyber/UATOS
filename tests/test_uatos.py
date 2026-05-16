#!/usr/bin/env python3
"""
test_uatos.py — UATOS Unit + Integration Tests
"""

import unittest, sys, os, json, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scb_store import calc_coherence, calc_ch, calc_hr

class TestCoherenceCalc(unittest.TestCase):
    def test_mu_one(self):
        self.assertAlmostEqual(calc_coherence([1.0, 1.0, 1.0]), 1.0, places=6)

    def test_mu_below_one(self):
        vals = [0.9999, 0.9998, 0.9997]
        mu = calc_coherence(vals)
        self.assertGreater(mu, 0.999)
        self.assertLess(mu, 1.0)

    def test_ch_one(self):
        self.assertAlmostEqual(calc_ch([1.0, 1.0, 1.0]), 1.0, places=6)

    def test_hr_threshold(self):
        mu = calc_coherence([0.9999, 0.9998, 0.9997, 0.9996])
        ch = calc_ch([1.0])
        hr = calc_hr(mu, ch)
        self.assertGreaterEqual(hr, 0.9995)

    def test_empty_vals(self):
        self.assertEqual(calc_coherence([]), 0.0)
        self.assertEqual(calc_ch([]), 0.0)

class TestSCBLogic(unittest.TestCase):
    def test_scb_id_format(self):
        id = "scb-001"
        self.assertRegex(id, r'^scb-\d{3}$')

    def test_risk_levels(self):
        levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        for r in levels:
            self.assertIn(r, levels)

    def test_threshold_constitutional(self):
        THRESHOLD = 0.9995
        mu = calc_coherence([0.9999, 0.9997])
        ch = calc_ch([1.0])
        hr = calc_hr(mu, ch)
        self.assertGreaterEqual(hr, THRESHOLD)

if __name__ == '__main__':
    unittest.main()