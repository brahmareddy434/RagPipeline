"""Claims contracts independent of HTTP, storage and model providers."""
from datetime import date
from enum import Enum
from pydantic import BaseModel, ConfigDict, Field

class ClaimStatus(str,Enum):
    received="received"
    awaiting_documents="awaiting_documents"
    under_review="under_review"
    closed="closed"

class ClaimRecord(BaseModel):
    model_config=ConfigDict(extra="forbid")
    claim_id:str=Field(pattern=r"^CLM-\d{4}-\d{5}$")
    status:ClaimStatus
    date_of_loss:date
    policy_type:str
    deductible:float=Field(ge=0,allow_inf_nan=False)
    notes:list[str]
    required_clauses:list[str]

class ClaimSummary(BaseModel):
    model_config=ConfigDict(extra="forbid")
    claim_id:str=Field(pattern=r"^CLM-\d{4}-\d{5}$")
    date_of_loss:date
    deductible:float=Field(ge=0,allow_inf_nan=False)
    denied:bool=False
    denial_clause:str|None=None
    summary:str=Field(min_length=1,max_length=3000)
