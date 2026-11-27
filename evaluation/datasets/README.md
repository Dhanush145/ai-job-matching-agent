# Evaluation datasets

- `ranking_test_cases.json`: prefilled with JOB001-JOB008 from the supplied jobs dataset.
  Its relevance grades are illustrative human labels for a sample AI/ML candidate; review
  them before reporting results.
- `retrieval_test_cases.json`: label `relevant_job_ids` manually for each query.
- `resume_test_cases.json`: populate expected and predicted values from reviewed parser runs.
- `skill_gap_test_cases.json`: populate expected missing skills from a reviewed reference.
- `agent_tool_test_cases.json`: record the actual tool selected by the agent.
- `performance_test_cases.json`: configuration for latency measurements.

Do not use the system's own predictions as ground truth. Labels should be reviewed
independently to avoid circular evaluation.
