import json
import re
from app.config.paths import PROJECT_ROOT
from app.domain.claims import ClaimRecord
from app.domain.tools import ToolFailure

class FictionalClaims:
    """Read-only training repository. Never substitutes for a tenant claims platform."""
    def __init__(self):
        self.records={r.claim_id:r for r in (ClaimRecord.model_validate(v) for v in json.loads((PROJECT_ROOT/"course/insurance/triage-claims.json").read_text())["claims"])}
        self.clauses={}
        for paragraph in (PROJECT_ROOT/"course/insurance/claims-policy-2026.txt").read_text().split("\n\n"):
            match=re.match(r"([A-Z]+(?:-[A-Z]+)*-\d+)\.",paragraph)
            if match:self.clauses[match.group(1)]=paragraph.strip()
    def get(self,claim_id):
        if claim_id not in self.records:raise ToolFailure("Unknown fictional claim ID. Choose a listed fixture; do not invent a record.")
        return self.records[claim_id].model_copy(deep=True)
    def clause(self,clause_id):
        if clause_id not in self.clauses:raise ToolFailure("Unknown policy clause. Use an exact clause ID from the notes or schedule.")
        return self.clauses[clause_id]
