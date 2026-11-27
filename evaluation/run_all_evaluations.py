import subprocess, sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=[
    "evaluation/evaluate_retrieval.py",
    "evaluation/evaluate_ranking.py",
    "evaluation/evaluate_resume_parser.py",
    "evaluation/evaluate_skill_gaps.py",
    "evaluation/evaluate_agent.py",
    "evaluation/evaluate_performance.py",
]


def main():
    failed=[]
    for script in SCRIPTS:
        print(f"\n{'='*65}\nRunning {script}\n{'='*65}")
        result=subprocess.run([sys.executable,str(ROOT/script)],cwd=ROOT)
        if result.returncode:
            failed.append(script)
    print("\nEvaluation run finished.")
    if failed:
        print("Not run successfully (often because labels/outputs still need filling):")
        for item in failed:
            print(" -",item)
        raise SystemExit(1)
    print("All evaluation modules completed.")


if __name__=="__main__":
    main()
