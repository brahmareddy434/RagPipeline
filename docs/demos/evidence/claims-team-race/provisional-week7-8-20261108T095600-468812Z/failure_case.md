Injected in-process HTTP 500 from coverage/exclusions worker on C01 (CLM-2026-10001).
Observed: stop_reason=worker_error; abstained=True; answer=Could not complete the exclusions review (HTTP 500). Claim coverage remains undetermined; adjuster review is required.
Behavior: no retry; safe abstention/partial response; no unsupported coverage assertion.
Recorded worker failure: [{'worker': 'coverage/exclusions', 'status_code': 500, 'injection': 'in-process Week 10 fault fixture'}]
Failure-call token accounting: manager_planning=132 tokens
Coverage worker hand-off: 0 provider tokens (injected 500 before worker model call).
