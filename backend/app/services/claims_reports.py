"""Read only the explicitly reviewed fictional benchmark artifacts."""
import json
import re
from app.config.paths import PROJECT_ROOT

ROOT=PROJECT_ROOT/"docs/demos/evidence/claims-race"

def benchmark_reports():
    reports={}
    for directory in ROOT.iterdir():
        if not directory.is_dir() or not re.fullmatch(r"(?:baseline|mitigation)(?:-r\d+)?",directory.name):continue
        path=directory/"summary.json"
        if path.is_file():reports[directory.name]=json.loads(path.read_text(encoding="utf-8"))
    comparisons=sorted((ROOT/name for name in reports if name.startswith("mitigation")),key=lambda p:p.name)
    comparison=next((p/"comparison.json" for p in reversed(comparisons) if (p/"comparison.json").is_file()),None)
    return {"reports":reports,"comparison":json.loads(comparison.read_text(encoding="utf-8")) if comparison else None,
            "notice":"Reviewed fictional local-model benchmark. Outcome checks are deterministic proxies; human acceptance remains separate."}

def benchmark_case(phase,approach,case_id):
    if not re.fullmatch(r"(?:baseline|mitigation)(?:-r\d+)?",phase) or approach not in {"agent","workflow"} or case_id not in {f"C{i:02}" for i in range(1,11)}:
        raise ValueError("Unknown benchmark case.")
    path=ROOT/phase/f"{approach}-{case_id}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.is_file() else None
