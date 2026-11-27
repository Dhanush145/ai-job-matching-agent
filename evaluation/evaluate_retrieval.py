import json, sys
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BACKEND))

from app.services.retrieval_service import search_similar_jobs
from evaluation.metrics.retrieval_metrics import precision_at_k, recall_at_k, reciprocal_rank

DATA = ROOT / "evaluation/datasets/retrieval_test_cases.json"
OUT = ROOT / "evaluation_results/retrieval_evaluation.json"


def main(k=5):
    cases = json.loads(DATA.read_text(encoding="utf-8"))
    results, skipped = [], []
    for case in cases:
        relevant = case.get("relevant_job_ids") or []
        if not relevant:
            skipped.append({"query": case.get("query"), "reason": "No human relevance labels"})
            continue
        retrieved = search_similar_jobs(case["query"], top_k=k)
        ids = [str(x["job_id"]) for x in retrieved]
        results.append({
            "query": case["query"], "retrieved_job_ids": ids,
            f"precision_at_{k}": precision_at_k(ids, relevant, k),
            f"recall_at_{k}": recall_at_k(ids, relevant, k),
            "reciprocal_rank": reciprocal_rank(ids, relevant)
        })
    if not results:
        raise SystemExit("No labelled retrieval cases. Fill relevant_job_ids in retrieval_test_cases.json first.")
    report = {
        "module":"10.1 retrieval",
        "k":k,
        "evaluated_cases":len(results),
        "skipped_cases":len(skipped),
        "metrics":{
            f"mean_precision_at_{k}":round(mean(x[f"precision_at_{k}"] for x in results),4),
            f"mean_recall_at_{k}":round(mean(x[f"recall_at_{k}"] for x in results),4),
            "mrr":round(mean(x["reciprocal_rank"] for x in results),4)
        },
        "results":results,"skipped":skipped
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=4), encoding="utf-8")
    print(json.dumps(report["metrics"], indent=4))
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--k",type=int,default=5)
    args=p.parse_args()
    main(args.k)
