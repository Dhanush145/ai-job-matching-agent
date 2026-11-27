
import json
import sys
from pathlib import Path

# Project root directory
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

# Add project root and backend to Python import path
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

# Import after configuring sys.path
from evaluation.metrics.classification_metrics import field_accuracy


DATA = ROOT / "evaluation" / "datasets" / "resume_test_cases.json"
OUT = ROOT / "evaluation_results" / "resume_parser_evaluation.json"

FIELDS = (
    "name",
    "email",
    "phone",
    "skills",
    "experience_years",
    "education"
)


def main():
    cases = json.loads(DATA.read_text(encoding="utf-8"))

    valid_cases = [
        case for case in cases
        if case.get("predicted") and case.get("expected")
    ]

    if not valid_cases:
        raise SystemExit(
            "Add actual parser output to each case's predicted field first."
        )

    expected = [case["expected"] for case in valid_cases]
    predicted = [case["predicted"] for case in valid_cases]

    score = field_accuracy(expected, predicted, FIELDS)

    details = []

    for case in valid_cases:
        checks = {}

        for field in FIELDS:
            if field in case["expected"]:
                checks[field] = (
                    case["expected"].get(field)
                    == case["predicted"].get(field)
                )

        details.append({
            "case_id": case["case_id"],
            "field_checks": checks
        })

    report = {
        "module": "10.3 resume extraction",
        "evaluated_resumes": len(valid_cases),
        "field_accuracy": round(score, 4),
        "details": details,
        "note": (
            "Field-level exact/normalized comparison. "
            "Manually review list ordering and semantically equivalent values."
        )
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=4))
    print(f"\nSaved: {OUT}")


if __name__ == "__main__":
    main()
