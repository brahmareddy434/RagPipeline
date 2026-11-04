import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx


CASES = [
    ("leave", "How many paid leave days does an employee receive each year?", "leave-policy.txt", True),
    ("leave", "What is the annual paid leave allowance?", "leave-policy.txt", True),
    ("leave", "How much PTO do employees receive annually?", "Employee-Handbook.pdf", True),
    ("leave", "What is the deadline for submitting planned leave?", "leave-policy.txt", True),
    ("leave", "How many working days before planned leave should I apply?", "leave-policy.txt", True),
    ("leave", "Can emergency leave be requested on the same day?", "leave-policy.txt", True),
    ("leave", "Who must be informed when emergency leave is needed?", "leave-policy.txt", True),
    ("leave", "Can unused leave be carried into the next year?", "leave-policy.txt", True),
    ("leave", "What is the maximum number of leave days that can be carried forward?", "leave-policy.txt", True),
    ("leave", "How many paid sick leave days are provided each year?", "leave-policy.txt", True),
    ("leave", "What happens to accrued PTO when an employee leaves?", "Employee-Handbook.pdf", True),
    ("conduct", "What behavior counts as workplace harassment?", "Employee-Handbook.pdf", True),
    ("conduct", "Who can an employee contact about harassment?", "Employee-Handbook.pdf", True),
    ("conduct", "What should I do if my manager is involved in a harassment claim?", "Employee-Handbook.pdf", True),
    ("conduct", "Are supervisors allowed to date their direct reports?", "Employee-Handbook.pdf", True),
    ("conduct", "What does the handbook say about dating colleagues?", "Employee-Handbook.pdf", True),
    ("conduct", "What is the dress code at the company?", "Employee-Handbook.pdf", True),
    ("conduct", "Are workout clothes acceptable at work?", "Employee-Handbook.pdf", True),
    ("conduct", "Is smoking allowed anywhere in the workplace?", "Employee-Handbook.pdf", True),
    ("conduct", "Where are designated smoking areas?", "Employee-Handbook.pdf", True),
    ("conduct", "What happens if smoking causes a fire or sets off an alarm?", "Employee-Handbook.pdf", True),
    ("safety", "What should I do if I witness severe physical violence?", "Employee-Handbook.pdf", True),
    ("safety", "Who should receive a report about workplace violence?", "Employee-Handbook.pdf", True),
    ("safety", "What should employees do to prevent workplace injuries?", "Employee-Handbook.pdf", True),
    ("safety", "What are the emergency management provisions?", "Employee-Handbook.pdf", True),
    ("safety", "Can employees use a phone while driving a company vehicle?", "Employee-Handbook.pdf", True),
    ("safety", "What should I do after an accident in a company car?", "Employee-Handbook.pdf", True),
    ("security", "How should confidential documents be disposed of?", "Employee-Handbook.pdf", True),
    ("security", "Who may receive confidential company information?", "Employee-Handbook.pdf", True),
    ("security", "What should I do with a suspicious phishing email?", "Employee-Handbook.pdf", True),
    ("security", "What are the rules for using corporate email personally?", "Employee-Handbook.pdf", True),
    ("security", "Can I use the company internet for personal activities?", "Employee-Handbook.pdf", True),
    ("visitors", "What approval is needed before inviting an office visitor?", "Employee-Handbook.pdf", True),
    ("visitors", "What identification process applies to visitors?", "Employee-Handbook.pdf", True),
    ("visitors", "Where must visitors stay while they are in the building?", "Employee-Handbook.pdf", True),
    ("visitors", "What should I do when a delivery arrives for me?", "Employee-Handbook.pdf", True),
    ("work", "How is overtime pay handled for non-exempt employees?", "Employee-Handbook.pdf", True),
    ("work", "What is the maximum overtime limit in the handbook?", "Employee-Handbook.pdf", True),
    ("work", "How much notice is needed for remote working?", "Employee-Handbook.pdf", True),
    ("work", "How long may an office-based employee work remotely?", "Employee-Handbook.pdf", True),
    ("work", "Can an employee work from home during an emergency?", "Employee-Handbook.pdf", True),
    ("expenses", "Which expenses can employees submit for reimbursement?", "Employee-Handbook.pdf", True),
    ("expenses", "How long do employees have to submit an expense?", "Employee-Handbook.pdf", True),
    ("expenses", "When are approved expenses reimbursed?", "Employee-Handbook.pdf", True),
    ("expenses", "What records should employees keep for reimbursable expenses?", "Employee-Handbook.pdf", True),
    ("out_of_scope", "Does the company pay for gym memberships?", None, False),
    ("out_of_scope", "What is the office parking fee?", None, False),
    ("out_of_scope", "What is the employee dental insurance premium?", None, False),
    ("out_of_scope", "Who is the current chief executive officer?", None, False),
    ("out_of_scope", "What is the company's policy on commuter rail subsidies?", None, False),
]

TEMPERATURES = (0.0, 0.1, 0.3, 0.7, 1.0, 1.5)


def collect(base_url: str = "http://127.0.0.1:8000", destination: Path | None = None) -> list[dict]:
    run_id = str(uuid.uuid4())
    collected_at = datetime.now(timezone.utc).isoformat()
    traces = []
    timeout = httpx.Timeout(connect=10.0, read=300.0, write=10.0, pool=10.0)

    with httpx.Client(timeout=timeout) as client:
        for sequence, (category, question, expected_source, answerable) in enumerate(CASES, 1):
            temperature = TEMPERATURES[(sequence - 1) % len(TEMPERATURES)]
            trace_id = str(uuid.uuid4())
            request_id = str(uuid.uuid4())
            started = time.perf_counter()
            trace = {
                "trace_id": trace_id,
                "run_id": run_id,
                "sequence": sequence,
                "collected_at": collected_at,
                "category": category,
                "question": question,
                "expected_source": expected_source,
                "expected_answerable": answerable,
                "endpoint": "/ask",
                "request_id": request_id,
                "request": {"question": question, "temperature": temperature},
                "temperature": temperature,
                "status": "request_failed",
            }
            try:
                response = client.post(
                    f"{base_url}/ask",
                    json=trace["request"],
                    headers={"X-Trace-ID": trace_id, "X-Request-ID": request_id},
                )
                response.raise_for_status()
                payload = response.json()
                trace.update(
                    {
                        "status": "completed",
                        "http_status": response.status_code,
                        "answer": payload["answer"],
                        "confidence": payload["confidence"],
                        "citations": payload.get("citations", []),
                        "retrieved": [
                            {
                                "chunk_id": item["id"],
                                "source": item["source"],
                                "page": item.get("page"),
                                "rank": item["rank"],
                                "score": item["score"],
                                "retrieval_method": item["retrieval_method"],
                                "text": item["text"],
                            }
                            for item in payload.get("retrieved", [])
                        ],
                    }
                )
            except (httpx.HTTPError, KeyError, ValueError) as error:
                trace.update({"http_status": getattr(getattr(error, "response", None), "status_code", None), "error": str(error)})
            trace["latency_ms"] = round((time.perf_counter() - started) * 1000, 2)
            traces.append(trace)
            if destination:
                destination.write_text(json.dumps(traces, indent=2), encoding="utf-8")
            print(f"{sequence:02d}/50 {trace_id} {trace['status']} temp={temperature}", flush=True)
    return traces


if __name__ == "__main__":
    destination = Path(__file__).with_name("week5_traces.json")
    traces = collect(destination=destination)
    print(f"Wrote {len(traces)} traces to {destination}")
