from pathlib import Path
import unittest

from minisafeml.metamodel import build_metamodel, grammar_path


ROOT = Path(__file__).resolve().parents[1]


class MetamodelTests(unittest.TestCase):
    def test_grammar_path_points_to_existing_grammar_file(self):
        path = grammar_path()

        self.assertTrue(path.exists())
        self.assertEqual(path.name, "minisafeml.tx")

    def test_build_metamodel_parses_example_model(self):
        model = build_metamodel().model_from_file(str(ROOT / "examples" / "coffee_robot.msml"))

        self.assertEqual(model.system, "CoffeeRobot")
        self.assertEqual(len(model.declarations), 7)


if __name__ == "__main__":
    unittest.main()
