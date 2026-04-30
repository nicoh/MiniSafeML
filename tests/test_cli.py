import contextlib
from io import StringIO
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

from minisafeml import cli


ROOT = Path(__file__).resolve().parents[1]


def run_main(argv):
    stdout = StringIO()
    with patch.object(sys, "argv", argv):
        with contextlib.redirect_stdout(stdout):
            exit_code = cli.main()
    return exit_code, stdout.getvalue()


class CliTests(unittest.TestCase):
    def test_parse_args_accepts_flags_before_model_path(self):
        verbose, trace_table, model_path = cli.parse_args(
            ["minisafeml", "--verbose", "--trace-table", "model.msml"]
        )

        self.assertTrue(verbose)
        self.assertTrue(trace_table)
        self.assertEqual(model_path, Path("model.msml"))

    def test_parse_args_rejects_unknown_option(self):
        self.assertEqual(cli.parse_args(["minisafeml", "--unknown", "model.msml"]), (None, None, None))

    def test_main_prints_usage_for_missing_arguments(self):
        exit_code, output = run_main(["minisafeml"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Usage: python -m minisafeml.cli", output)

    def test_main_reports_missing_file(self):
        exit_code, output = run_main(["minisafeml", "missing.msml"])

        self.assertEqual(exit_code, 1)
        self.assertIn("Error: file not found: missing.msml", output)

    def test_main_parses_valid_model_and_runs_checks(self):
        exit_code, output = run_main(["minisafeml", str(ROOT / "examples" / "coffee_robot.msml")])

        self.assertEqual(exit_code, 0)
        self.assertIn("MiniSafeML model parsed successfully.", output)
        self.assertIn("Model checks: no issues found.", output)

    def test_main_reports_syntax_errors(self):
        with patch("minisafeml.cli.build_metamodel") as build_metamodel_mock:
            build_metamodel_mock.return_value.model_from_file.side_effect = cli.TextXSyntaxError(
                "bad syntax", line=3, col=7
            )

            exit_code, output = run_main(["minisafeml", str(ROOT / "examples" / "coffee_robot.msml")])

        self.assertEqual(exit_code, 2)
        self.assertIn("Syntax error while parsing MiniSafeML model.", output)
        self.assertIn("Line 3, column 7: bad syntax", output)

    def test_main_reports_semantic_errors(self):
        with patch("minisafeml.cli.build_metamodel") as build_metamodel_mock:
            build_metamodel_mock.return_value.model_from_file.side_effect = cli.TextXSemanticError(
                "bad reference", line=4, col=2
            )

            exit_code, output = run_main(["minisafeml", str(ROOT / "examples" / "coffee_robot.msml")])

        self.assertEqual(exit_code, 3)
        self.assertIn("Semantic error while resolving MiniSafeML model.", output)
        self.assertIn("Line 4, column 2: bad reference", output)


if __name__ == "__main__":
    unittest.main()
