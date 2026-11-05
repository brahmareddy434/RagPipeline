from fastapi import APIRouter
from app.services.claims_evaluation import evaluate

router=APIRouter()

@router.get("/claims/evaluation")
async def evaluation():
    """Deterministic report over public fictional fixtures; never returns private labels."""
    return evaluate()
