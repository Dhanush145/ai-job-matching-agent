import json, sys
from pathlib import Path
from statistics import mean

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
sys.path.insert(0,str(ROOT))

from app.services.ranking_service import rank_jobs
from evaluation.metrics.retrieval_metrics import ndcg_at_k, reciprocal_rank

DATA=ROOT/"evaluation/datasets/ranking_test_cases.json"
OUT=ROOT/"evaluation_results/ranking_evaluation.json"


def main():
    cases=json.loads(DATA.read_text(encoding="utf-8"))
    rows=[]
    for case in cases:
        jobs=case.get("jobs",[])
        grades=case.get("relevance_grades",{})
        if not jobs or any("REPLACE_" in str(x) for x in grades):
            continue
        ranked=rank_jobs(
            candidate_skills=case.get("candidate_skills",[]),
            candidate_experience=case.get("candidate_experience",0),
            candidate_locations=case.get("candidate_locations",[]),
            retrieved_jobs=jobs,
            top_k=case.get("top_k",5)
        )
        ids=[str(x["job_id"]) for x in ranked]
        binary_relevant=[job_id for job_id,grade in grades.items() if grade>0]
        rows.append({
            "case_id":case["case_id"],"ranked_job_ids":ids,
            "ndcg_at_k":round(ndcg_at_k(ids,grades,case.get("top_k",5)),4),
            "mrr":round(reciprocal_rank(ids,binary_relevant),4)
        })
    if not rows:
        raise SystemExit("No valid ranking cases. Replace sample IDs and add relevance grades.")
    report={
        "module":"10.2 hybrid ranking","evaluated_cases":len(rows),
        "mean_ndcg_at_k":round(mean(x["ndcg_at_k"] for x in rows),4),
        "mean_mrr":round(mean(x["mrr"] for x in rows),4),
        "results":rows
    }
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=4),encoding="utf-8")
    print(json.dumps(report,indent=4))
    print(f"Saved: {OUT}")


if __name__=="__main__":
    main()
