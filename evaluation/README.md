# Phase 10 — Evaluation & Performance Testing

This package evaluates the existing job-matching project. It does not modify your
backend application code or its retrieval/ranking weights.

## Included modules

| Module | Script | Measures |
|---|---|---|
| 10.1 Retrieval | `evaluate_retrieval.py` | Precision@K, Recall@K, MRR |
| 10.2 Ranking | `evaluate_ranking.py` | NDCG@K, MRR using the actual `rank_jobs()` |
| 10.3 Resume parsing | `evaluate_resume_parser.py` | Field-level extraction accuracy |
| 10.4 Skill gaps | `evaluate_skill_gaps.py` | Missing-skill Jaccard agreement |
| 10.5 Agent tool selection | `evaluate_agent.py` | Expected vs observed tool accuracy |
| 10.6 Performance | `evaluate_performance.py` | Retrieval latency mean/min/max/p95 |

## Important before running

Evaluation requires ground truth. Most included datasets are starter templates, not real labels or evidence of system accuracy. The ranking dataset is prefilled with the eight job records from your uploaded `jobs.json` and illustrative human-assigned relevance grades for a sample AI/ML candidate. Review and adjust those grades to match your intended candidate/query before treating the ranking metrics as final. Replace placeholder IDs, expected resume values, and observed tool names with values checked against your real system and human judgments.

The resume parser and agent tool selection tests are data-driven: run your real parser /
agent, then record the actual outputs in the `predicted` / `observed_tool` fields.
This avoids assuming undocumented signatures or inventing test outcomes.

## Install / run (Windows PowerShell)

From the project root:

```powershell
cd E:\ai-job-matching-agent
.\venv312\Scripts\Activate.ps1
```

Ensure your normal backend dependencies are installed in `venv312`, including FAISS,
NumPy, SQLAlchemy, Sentence Transformers, and Pydantic as required by your project.

Build or refresh your FAISS index using your existing API endpoint / existing indexing
workflow before running retrieval or performance tests.

Run individual modules:

```powershell
python evaluation/evaluate_retrieval.py --k 5
python evaluation/evaluate_ranking.py
python evaluation/evaluate_resume_parser.py
python evaluation/evaluate_skill_gaps.py
python evaluation/evaluate_agent.py
python evaluation/evaluate_performance.py --iterations 5
```

Run all modules:

```powershell
python evaluation/run_all_evaluations.py
```

Some scripts intentionally stop until their dataset has been labelled. This is expected.
Start with retrieval and ranking, then populate the remaining test observations.

## Output

JSON reports are written to `evaluation_results/`. Do not commit private resumes,
personal data, `.env`, database files, FAISS indexes, or checkpoint databases.

## Metric definitions

- Precision@K = relevant retrieved jobs in top K / K.
- Recall@K = relevant retrieved jobs in top K / all labelled relevant jobs.
- MRR = average reciprocal rank of the first relevant result.
- NDCG@K = discounted gain of ranking / ideal discounted gain, using human relevance grades.
- Resume field accuracy = normalized field comparisons against reviewed expected values.
- Skill-gap Jaccard = intersection / union of expected and actual missing-skill sets.
- Tool-selection accuracy = correct observed tool calls / labelled tool-selection cases.
- Latency = wall-clock time around the FAISS retrieval function only; it excludes full LLM and HTTP latency.
