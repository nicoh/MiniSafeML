import unittest

from minisafeml.analysis.risk_tree import classify_risk, is_lower_risk


class RiskTreeTests(unittest.TestCase):
    def test_classify_risk_uses_expected_matrix(self):
        self.assertEqual(classify_risk("S1", "F2", "P1"), "medium")
        self.assertEqual(classify_risk("S2", "F2", "P2"), "very_high")

    def test_is_lower_risk_compares_risk_order(self):
        self.assertTrue(is_lower_risk("low", "medium"))
        self.assertFalse(is_lower_risk("high", "high"))


if __name__ == "__main__":
    unittest.main()
