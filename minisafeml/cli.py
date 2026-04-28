import sys
from pathlib import Path

from textx import TextXSyntaxError, TextXSemanticError

from .metamodel import build_metamodel
from .analysis.checker import check_model
from .analysis.risk_tree import classify_risk
from .reports.traceability import print_traceability_table


def print_model(model) -> None:
    print(f"System: {model.system}")
    print()

    for decl in model.declarations:
        cls = decl.__class__.__name__
        name = getattr(decl, "name", "<no-id>")
        print(f"{cls}: {name}")

        if cls == "ScopeDecl":
            print(f"  task: {decl.task}")
            print(f"  platform: {decl.platform}")
            print(f"  environment: {decl.environment}")
            print(f"  stakeholder: {decl.stakeholder}")

        elif cls == "HazardDecl":
            print(f"  description: {decl.description}")

        elif cls == "HarmDecl":
            print(f"  description: {decl.description}")

        elif cls == "ContextDecl":
            print(f"  description: {decl.description}")
            print(f"  forHazard: {decl.hazard.name}")
            print(f"  causesHarm: {decl.harm.name}")

        elif cls == "RiskDecl":
            computed = classify_risk(decl.severity, decl.frequency, decl.possibility)
            print(f"  context: {decl.context.name}")
            print(f"  severity: {decl.severity}")
            print(f"  frequency: {decl.frequency}")
            print(f"  possibility: {decl.possibility}")
            print(f"  class: {decl.riskClass}")
            print(f"  computedClass: {computed}")
            print(f"  acceptable: {decl.acceptable}")

        elif cls == "MeasureDecl":
            print(f"  kind: {decl.kind}")
            print(f"  description: {decl.description}")
            print(f"  mitigates: {decl.context.name}")
            print(f"  reducesTo: {decl.reducedClass}")

        elif cls == "RequirementDecl":
            print(f"  description: {decl.description}")
            if decl.source:
                print(f"  derivedFrom: {decl.source.name}")

        print()


def print_check_results(messages) -> None:
    if not messages:
        print("Model checks: no issues found.")
        print()
        return

    print("Model checks:")
    for entry in messages:
        print(f"  [{entry['level']}] {entry['message']}")
    print()


def print_verbose_analysis(model) -> None:
    print("Verbose analysis")
    print("================")
    print()

    risks = [d for d in model.declarations if d.__class__.__name__ == "RiskDecl"]
    measures = [d for d in model.declarations if d.__class__.__name__ == "MeasureDecl"]
    requirements = [d for d in model.declarations if d.__class__.__name__ == "RequirementDecl"]

    for risk in risks:
        computed = classify_risk(risk.severity, risk.frequency, risk.possibility)
        print(f"Risk {risk.name}")
        print(f"  Context:      {risk.context.name}")
        print(f"  S/F/P:        {risk.severity}/{risk.frequency}/{risk.possibility}")
        print(f"  Declared:     {risk.riskClass}")
        print(f"  Computed:     {computed}")
        print(f"  Acceptable:   {risk.acceptable}")

        matching_measures = [m for m in measures if m.context.name == risk.context.name]
        if matching_measures:
            print("  Measures:")
            for m in matching_measures:
                matching_requirements = [
                    r for r in requirements
                    if getattr(getattr(r, "source", None), "name", None) == m.name
                ]
                print(f"    - {m.name} ({m.kind}) reducesTo={m.reducedClass}")
                if matching_requirements:
                    for r in matching_requirements:
                        print(f"      -> requirement {r.name}")
                else:
                    print("      -> no derived requirement")
        else:
            print("  Measures:     none")

        print()


def parse_args(argv):
    verbose = False
    trace_table = False
    args = argv[1:]

    while args and args[0].startswith("--"):
        if args[0] == "--verbose":
            verbose = True
        elif args[0] == "--trace-table":
            trace_table = True
        else:
            return None, None, None
        args = args[1:]

    if len(args) != 1:
        return None, None, None

    return verbose, trace_table, Path(args[0])


def main() -> int:
    verbose, trace_table, model_path = parse_args(sys.argv)

    if model_path is None:
        print("Usage: python -m minisafeml.cli [--verbose] [--trace-table] <model-file>")
        return 1

    if not model_path.exists():
        print(f"Error: file not found: {model_path}")
        return 1

    try:
        mm = build_metamodel()
        model = mm.model_from_file(str(model_path))
    except TextXSyntaxError as e:
        print("Syntax error while parsing MiniSafeML model.")
        print(f"Line {e.line}, column {e.col}: {e.message}")
        return 2
    except TextXSemanticError as e:
        print("Semantic error while resolving MiniSafeML model.")
        print(f"Line {e.line}, column {e.col}: {e.message}")
        return 3
    except Exception as e:
        print("Unexpected error.")
        print(type(e).__name__, str(e))
        return 99

    print("MiniSafeML model parsed successfully.")
    print()

    messages = check_model(model)
    print_check_results(messages)

    if verbose:
        print_model(model)
        print_verbose_analysis(model)

    if trace_table:
        print_traceability_table(model)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())