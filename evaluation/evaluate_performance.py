import json, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/"backend"))
sys.path.insert(0,str(ROOT))

from app.services.retrieval_service import search_similar_jobs
from evaluation.metrics.performance_metrics import benchmark

DATA=ROOT/"evaluation/datasets/performance_test_cases.json"
OUT=ROOT/"evaluation_results/performance_evaluation.json"


def main(iterations=5):
    cases=json.loads(DATA.read_text(encoding="utf-8"))
    results=[]
    for case in cases:
        query=case["query"]
        stats=benchmark(lambda: search_similar_jobs(query=query,top_k=10),iterations=iterations,warmup=1)
        results.append({"query":query,**stats})
    report={"module":"10.6 retrieval performance","iterations_per_query":iterations,
            "results":results,
            "note":"Measures local FAISS retrieval call latency only, not full HTTP/agent/LLM response latency."}
    OUT.parent.mkdir(parents=True,exist_ok=True)
    OUT.write_text(json.dumps(report,indent=4),encoding="utf-8")
    print(json.dumps(report,indent=4))


if __name__=="__main__":
    import argparse
    p=argparse.ArgumentParser()
    p.add_argument("--iterations",type=int,default=5)
    args=p.parse_args()
    main(args.iterations)
