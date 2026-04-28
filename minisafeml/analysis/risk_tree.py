RISK_TREE = {
    ("S1", "F1", "P1"): "negligible",
    ("S1", "F1", "P2"): "low",
    ("S1", "F2", "P1"): "medium",
    ("S1", "F2", "P2"): "high",
    ("S2", "F1", "P1"): "medium",
    ("S2", "F1", "P2"): "high",
    ("S2", "F2", "P1"): "high",
    ("S2", "F2", "P2"): "very_high",
}

RISK_ORDER = {
    "negligible": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "very_high": 4,
}


def as_text(value) -> str:
    return str(value).strip()


def classify_risk(severity, frequency, possibility) -> str:
    key = (as_text(severity), as_text(frequency), as_text(possibility))
    return RISK_TREE[key]


def is_lower_risk(new_class: str, old_class: str) -> bool:
    return RISK_ORDER[new_class] < RISK_ORDER[old_class]