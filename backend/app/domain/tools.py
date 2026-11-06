from dataclasses import dataclass
from pydantic import BaseModel
from app.schemas import SearchResult

class ToolFailure(ValueError):
    """Recoverable argument, record or capability failure."""

@dataclass
class Observation:
    text:str
    evidence:list[SearchResult]

@dataclass(frozen=True)
class Tool:
    name:str
    description:str
    arguments:type[BaseModel]
    terminal:bool=False

def as_evidence(source,text,chunk_id):
    return SearchResult(id=chunk_id,text=text,source=source,page=None,metadata={"origin":"tool"},score=1.,rank=1,retrieval_method="tool")
