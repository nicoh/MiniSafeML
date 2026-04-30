import unittest
from unittest.mock import patch

from minisafeml.metamodel import build_metamodel
from minisafeml.reports import traceability


def parse_model(source: str):
    return build_metamodel().model_from_str(source)


class TraceabilityTests(unittest.TestCase):
    def test_risk_style_falls_back_to_white_for_unknown_class(self):
        self.assertEqual(traceability.risk_style("unexpected"), "white")

    def test_styled_value_wraps_rich_markup(self):
        self.assertEqual(traceability.styled_value("medium", "yellow"), "[yellow]medium[/yellow]")

    def test_print_traceability_table_renders_expected_row_values(self):
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
                severity S1
                frequency F2
                possibility P1
                class high
                acceptable false
            }
            protective measure M1 {
                description "measure"
                mitigates C1
                reducesTo low
            }
            requirement REQ1 {
                description "requirement"
                derivedFrom M1
            }
            """
        )

        with patch.object(traceability.console, "print") as console_print:
            traceability.print_traceability_table(model)

        table = console_print.call_args.args[0]
        cells = table.columns

        self.assertEqual(cells[0]._cells, ["C1"])
        self.assertEqual(cells[1]._cells, ["H1"])
        self.assertEqual(cells[2]._cells, ["HM1"])
        self.assertEqual(cells[3]._cells, ["R1"])
        self.assertEqual(cells[7]._cells, ["[yellow]medium[/yellow]"])
        self.assertEqual(cells[8]._cells, ["[bold yellow]high (!)[/bold yellow]"])
        self.assertEqual(cells[9]._cells, ["[red]false[/red]"])
        self.assertEqual(cells[10]._cells, ["M1"])
        self.assertEqual(cells[11]._cells, ["[green]low[/green]"])
        self.assertEqual(cells[12]._cells, ["REQ1"])


if __name__ == "__main__":
    unittest.main()
