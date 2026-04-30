from pathlib import Path
import unittest

from minisafeml.analysis.checker import check_model
from minisafeml.metamodel import build_metamodel


ROOT = Path(__file__).resolve().parents[1]


def parse_model(source: str):
    return build_metamodel().model_from_str(source)


class CheckerTests(unittest.TestCase):
    def test_complex_example_has_no_checker_messages(self):
        model = build_metamodel().model_from_file(str(ROOT / "examples" / "coffee_robot_complex.msml"))

        self.assertEqual(check_model(model), [])

    def test_error_example_produces_expected_diagnostics(self):
        model = build_metamodel().model_from_file(str(ROOT / "examples" / "coffee_robot_error.msml"))
        messages = check_model(model)
        texts = {entry["message"] for entry in messages}

        self.assertIn(
            "Risk 'R002' for context 'C002' declares class 'medium', but computed class from "
            "(S1, F1, P2) is 'low'.",
            texts,
        )
        self.assertIn(
            "Risk 'R004' for context 'C004' declares class 'low', but computed class from "
            "(S2, F1, P1) is 'medium'.",
            texts,
        )
        self.assertIn(
            "Risk 'R002' is classified as 'medium' but marked acceptable. This is unusual and should be justified.",
            texts,
        )
        self.assertIn(
            "Risk 'R005' for context 'C005' is not acceptable, but no measure mitigates that context.",
            texts,
        )
        self.assertIn(
            "Measure 'M002' claims residual class 'very_high' for context 'C002', but the original class is "
            "'medium', so no reduction is visible.",
            texts,
        )
        self.assertIn("Measure 'M003' has no derived requirement.", texts)

    def test_duplicate_ids_are_reported(self):
        model = parse_model(
            """
            system Demo
            hazard DUP : "first"
            harm DUP : "second"
            """
        )

        messages = check_model(model)

        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]["level"], "ERROR")
        self.assertIn("Duplicate ID 'DUP'", messages[0]["message"])

    def test_missing_declared_class_and_measure_requirement_are_reported(self):
        model = parse_model(
            """
            system Demo
            hazard H1 : "hazard"
            harm HM1 : "harm"
            context C1 {
                description "context"
                forHazard H1
                causesHarm HM1
            }
            risk R1 for C1 {
                severity S2
                frequency F2
                possibility P1
                acceptable false
            }
            protective measure M1 {
                description "measure"
                mitigates C1
            }
            """
        )
        messages = check_model(model)
        texts = {entry["message"] for entry in messages}

        self.assertIn(
            "Risk 'R1' for context 'C1' has no declared risk class. Computed class would be 'high'.",
            texts,
        )
        self.assertIn(
            "Measure 'M1' mitigates context 'C1' but does not declare a residual risk class via reducesTo.",
            texts,
        )
        self.assertIn("Measure 'M1' has no derived requirement.", texts)


if __name__ == "__main__":
    unittest.main()
