import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[4]))
from bensz_skill_kernel.atomic_verifiers import run_atomic
json.dump(run_atomic("task-completeness", json.load(sys.stdin)), sys.stdout, ensure_ascii=False)
