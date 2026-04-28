from .risk_tree import classify_risk, is_lower_risk


def msg(level: str, text: str) -> dict:
    return {"level": level, "message": text}


def as_text(value) -> str | None:
    if value is None:
        return None
    return str(value).strip()


def check_unique_names(model):
    seen = {}
    messages = []

    for decl in model.declarations:
        name = getattr(decl, "name", None)
        if not name:
            continue

        if name in seen:
            messages.append(
                msg(
                    "ERROR",
                    f"Duplicate ID '{name}' found in "
                    f"{decl.__class__.__name__} and {seen[name].__class__.__name__}."
                )
            )
        else:
            seen[name] = decl

    return messages


def get_decls(model, cls_name: str):
    return [d for d in model.declarations if d.__class__.__name__ == cls_name]


def get_risks(model):
    return get_decls(model, "RiskDecl")


def get_measures(model):
    return get_decls(model, "MeasureDecl")


def get_requirements(model):
    return get_decls(model, "RequirementDecl")


def measures_for_context(model, context_name: str):
    result = []
    for m in get_measures(model):
        m_context = getattr(getattr(m, "context", None), "name", None)
        if m_context == context_name:
            result.append(m)
    return result


def requirements_for_measure(model, measure_name: str):
    result = []
    for r in get_requirements(model):
        source_name = getattr(getattr(r, "source", None), "name", None)
        if source_name == measure_name:
            result.append(r)
    return result


def check_risk_class_consistency(model):
    messages = []

    for risk in get_risks(model):
        computed = classify_risk(risk.severity, risk.frequency, risk.possibility)
        declared = as_text(getattr(risk, "riskClass", None))

        if declared is None:
            messages.append(
                msg(
                    "WARN",
                    f"Risk '{risk.name}' for context '{risk.context.name}' has no declared risk class. "
                    f"Computed class would be '{computed}'."
                )
            )
            continue

        if declared != computed:
            messages.append(
                msg(
                    "WARN",
                    f"Risk '{risk.name}' for context '{risk.context.name}' declares class "
                    f"'{declared}', but computed class from "
                    f"({as_text(risk.severity)}, {as_text(risk.frequency)}, {as_text(risk.possibility)}) "
                    f"is '{computed}'."
                )
            )

    return messages


def check_risk_acceptability_consistency(model):
    messages = []

    # Lecture-level convention, not a universal law.
    # low/negligible typically acceptable, medium/high/very_high typically not.
    for risk in get_risks(model):
        declared = as_text(getattr(risk, "riskClass", None))
        acceptable = as_text(getattr(risk, "acceptable", None))

        if declared is None or acceptable is None:
            continue

        if declared in {"negligible", "low"} and acceptable == "false":
            messages.append(
                msg(
                    "INFO",
                    f"Risk '{risk.name}' is classified as '{declared}' but marked unacceptable. "
                    f"This may be intentional, but it is worth checking."
                )
            )

        if declared in {"medium", "high", "very_high"} and acceptable == "true":
            messages.append(
                msg(
                    "WARN",
                    f"Risk '{risk.name}' is classified as '{declared}' but marked acceptable. "
                    f"This is unusual and should be justified."
                )
            )

    return messages


def check_nonacceptable_risks_have_measures(model):
    messages = []

    for risk in get_risks(model):
        acceptable = as_text(getattr(risk, "acceptable", None))

        if acceptable == "false":
            measures = measures_for_context(model, risk.context.name)
            if not measures:
                messages.append(
                    msg(
                        "ERROR",
                        f"Risk '{risk.name}' for context '{risk.context.name}' is not acceptable, "
                        f"but no measure mitigates that context."
                    )
                )

    return messages


def check_measure_reduction_consistency(model):
    messages = []
    risks_by_context = {risk.context.name: risk for risk in get_risks(model)}

    for measure in get_measures(model):
        reduced = as_text(getattr(measure, "reducedClass", None))

        if reduced is None:
            messages.append(
                msg(
                    "INFO",
                    f"Measure '{measure.name}' mitigates context '{measure.context.name}' "
                    f"but does not declare a residual risk class via reducesTo."
                )
            )
            continue

        risk = risks_by_context.get(measure.context.name)
        if risk is None:
            messages.append(
                msg(
                    "WARN",
                    f"Measure '{measure.name}' mitigates context '{measure.context.name}', "
                    f"but no risk is defined for that context."
                )
            )
            continue

        original_declared = as_text(getattr(risk, "riskClass", None))
        if original_declared is not None:
            original_class = original_declared
        else:
            original_class = classify_risk(risk.severity, risk.frequency, risk.possibility)

        if not is_lower_risk(reduced, original_class):
            messages.append(
                msg(
                    "WARN",
                    f"Measure '{measure.name}' claims residual class '{reduced}' for context "
                    f"'{measure.context.name}', but the original class is '{original_class}', "
                    f"so no reduction is visible."
                )
            )

    return messages


def check_measures_have_requirements(model):
    messages = []

    for measure in get_measures(model):
        reqs = requirements_for_measure(model, measure.name)
        if not reqs:
            messages.append(
                msg(
                    "WARN",
                    f"Measure '{measure.name}' has no derived requirement."
                )
            )

    return messages


def check_model(model):
    messages = []
    messages.extend(check_unique_names(model))
    messages.extend(check_risk_class_consistency(model))
    messages.extend(check_risk_acceptability_consistency(model))
    messages.extend(check_nonacceptable_risks_have_measures(model))
    messages.extend(check_measure_reduction_consistency(model))
    messages.extend(check_measures_have_requirements(model))
    return messages