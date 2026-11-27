
import json
import sys
from pathlib import Path

# Get project root directory
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"

# Configure Python import paths BEFORE evaluation imports
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

# Import evaluation metrics
from evaluation.metrics.classification_metrics import accuracy

# Dataset and output paths
DATA = ROOT / "evaluation" / "datasets" / "agent_tool_test_cases.json"
OUT = ROOT / "evaluation_results" / "agent_tool_evaluation.json"


def main():

    # Load test cases
    cases = json.loads(DATA.read_text(encoding="utf-8"))

    # Keep only cases with actual observed tool names
    valid_cases = [
        case for case in cases
        if case.get("observed_tool", "").strip()
    ]

    if not valid_cases:
        raise SystemExit(
            "No observed tool calls found. "
            "Fill observed_tool in agent_tool_test_cases.json."
        )

    # Extract expected and observed tools
    expected = [
        case["expected_tool"]
        for case in valid_cases
    ]

    observed = [
        case["observed_tool"]
        for case in valid_cases
    ]

    # Calculate accuracy
    score = accuracy(expected, observed)

    correct = sum(
        actual == target
        for target, actual in zip(expected, observed)
    )

    # Build evaluation report
    report = {
        "module": "10.5 agent tool selection",
        "evaluated_cases": len(valid_cases),
        "tool_selection_accuracy": round(score, 4),
        "correct": correct,
        "incorrect": len(valid_cases) - correct,
        "results": [
            {
                "case_id": case["case_id"],
                "expected_tool": case["expected_tool"],
                "observed_tool": case["observed_tool"],
                "correct": (
                    case["expected_tool"] == case["observed_tool"]
                )
            }
            for case in valid_cases
        ]
    }

    # Save report
    OUT.parent.mkdir(parents=True, exist_ok=True)

    OUT.write_text(
        json.dumps(report, indent=4),
        encoding="utf-8"
    )

    print(json.dumps(report, indent=4))
    print(f"\nEvaluation report saved: {OUT}")


if __name__ == "__main__":
    main()
