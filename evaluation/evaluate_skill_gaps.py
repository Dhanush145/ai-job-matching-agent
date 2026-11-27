import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
sys.path.insert(0,str(ROOT))

from app.services.skill_gap_service import analyze_skill_gaps
from evaluation.metrics.classification_metrics import normalize

DATA=ROOT/"evaluation/datasets/skill_gap_test_cases.json"
OUT=ROOT/"evaluation_results/skill_gap_evaluation.json"


def main():
    cases=json.loads(DATA.read_text(encoding="utf-8"))
    results=[]
    for case in cases:
        actual=analyze_skill_gaps(
            candidate_skills=case["candidate_skills"],
            jobs=case["jobs"]
        )
        actual_missing={normalize(x["skill"]) for x in actual.get("missing_skills",[]) if isinstance(x,dict)}
        expected_missing={normalize(x) for x in case.get("expected_missing_skills",[])}
        union=actual_missing|expected_missing
        jaccard=(len(actual_missing&expected_missing)/len(union)) if union else 1.0
        results.append({
            "case_id":case["case_id"],
            "expected_missing_skills":sorted(expected_missing),
            "actual_missing_skills":sorted(actual_missing),
            "missing_skill_jaccard":round(jaccard,4),
            "jobs_analyzed":actual.get("jobs_analyzed")
        })
    report={"module":"10.4 skill-gap analysis","evaluated_cases":len(results),
            "mean_missing_skill_jaccard":round(sum(x["missing_skill_jaccard"] for x in results)/len(results),4),
            "results":results}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=4),encoding="utf-8")
    print(json.dumps(report,indent=4))


if __name__=="__main__":
    main()
