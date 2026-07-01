"""
Assessment comparison helper — formats catalog data for side-by-side comparison.
"""
from backend.services.catalog import get_by_name


def _field_type(item: dict) -> str:
    return ", ".join(item.get("test_type_labels", []))


def _field_duration(item: dict) -> str:
    return str(item.get("duration", "N/A"))


def _field_levels(item: dict) -> str:
    return ", ".join(item.get("job_levels", []))


def _field_remote(item: dict) -> str:
    return str(item.get("remote_testing", "N/A"))


def _field_adaptive(item: dict) -> str:
    return str(item.get("adaptive_irt", "N/A"))


def _field_languages(item: dict) -> str:
    return ", ".join(item.get("languages", []))


def _field_description(item: dict) -> str:
    return (item.get("description", "") or "")[:200]


_FIELDS: list[tuple[str, callable]] = [
    ("Type", _field_type),
    ("Duration", _field_duration),
    ("Levels", _field_levels),
    ("Remote", _field_remote),
    ("Adaptive", _field_adaptive),
    ("Languages", _field_languages),
    ("Description", _field_description),
]


def compare(names: list[str]) -> str:
    """
    Given a list of assessment names, return a formatted comparison string
    drawn purely from catalog data (no LLM inference).
    """
    items = [item for name in names if (item := get_by_name(name))]

    if not items:
        return ""

    lines = ["Comparison of assessments:"]
    for item in items:
        lines.append(f"\n{item['name']} ({item['url']})")
        for label, fn in _FIELDS:
            lines.append(f"  {label}: {fn(item)}")

    return "\n".join(lines)
