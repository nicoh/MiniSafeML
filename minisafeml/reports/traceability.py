# minisafeml/reports/traceability.py
from rich.console import Console
from rich.table import Table

from ..analysis.risk_tree import classify_risk

console = Console()

RISK_STYLES = {
    "negligible": "green",
    "low": "green",
    "medium": "yellow",
    "high": "red",
    "very_high": "bold red",
}


def risk_style(risk_class: str) -> str:
    return RISK_STYLES.get(risk_class, "white")


def styled_value(value: str, style: str) -> str:
    return f"[{style}]{value}[/{style}]"


def print_traceability_table(model) -> None:
    table = Table(title="MiniSafeML Traceability Table", show_lines=True)

    table.add_column("Context", style="bold blue")
    table.add_column("Hazard", style="magenta")
    table.add_column("Harm", style="red")
    table.add_column("Risk", style="yellow")
    table.add_column("S")
    table.add_column("F")
    table.add_column("P")
    table.add_column("Computed")
    table.add_column("Declared")
    table.add_column("Acceptable")
    table.add_column("Measure", style="green")
    table.add_column("Residual")
    table.add_column("Requirement", style="cyan")

    contexts = [d for d in model.declarations if d.__class__.__name__ == "ContextDecl"]
    risks = [d for d in model.declarations if d.__class__.__name__ == "RiskDecl"]
    measures = [d for d in model.declarations if d.__class__.__name__ == "MeasureDecl"]
    requirements = [d for d in model.declarations if d.__class__.__name__ == "RequirementDecl"]

    for context in contexts:
        risk = next((r for r in risks if r.context.name == context.name), None)
        measure = next((m for m in measures if m.context.name == context.name), None)

        requirement = None
        if measure is not None:
            requirement = next(
                (
                    req for req in requirements
                    if getattr(getattr(req, "source", None), "name", None) == measure.name
                ),
                None
            )

        if risk is not None:
            s = str(risk.severity)
            f = str(risk.frequency)
            p = str(risk.possibility)
            computed = classify_risk(risk.severity, risk.frequency, risk.possibility)
            declared = str(risk.riskClass) if risk.riskClass is not None else "-"
            acceptable = str(risk.acceptable) if risk.acceptable is not None else "-"
            risk_name = risk.name

            computed_col = styled_value(computed, risk_style(computed))

            if declared != "-":
                if declared != computed:
                    declared_col = f"[bold yellow]{declared} (!)[/bold yellow]"
                else:
                    declared_col = styled_value(declared, risk_style(declared))
            else:
                declared_col = "-"

            if acceptable == "true":
                acceptable_col = "[green]true[/green]"
            elif acceptable == "false":
                acceptable_col = "[red]false[/red]"
            else:
                acceptable_col = "-"
        else:
            s = f = p = "-"
            computed = declared = acceptable = "-"
            risk_name = "-"
            computed_col = "-"
            declared_col = "-"
            acceptable_col = "-"

        if measure is not None:
            measure_name = measure.name
            residual = str(measure.reducedClass) if measure.reducedClass is not None else "-"
            if residual != "-":
                residual_col = styled_value(residual, risk_style(residual))
            else:
                residual_col = "-"
        else:
            measure_name = "-"
            residual_col = "-"

        requirement_name = requirement.name if requirement is not None else "-"

        table.add_row(
            context.name,
            context.hazard.name,
            context.harm.name,
            risk_name,
            s,
            f,
            p,
            computed_col,
            declared_col,
            acceptable_col,
            measure_name,
            residual_col,
            requirement_name,
        )

    console.print(table)