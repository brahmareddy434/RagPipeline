import asyncio
from uuid import UUID
from fastapi import APIRouter, HTTPException, Query, Request
from app.controllers.dependencies import trace_logger

router=APIRouter()

@router.get("/traces")
async def list_traces(request:Request, limit:int=Query(20,ge=1,le=100)):
    records=await asyncio.to_thread(trace_logger(request).recent,limit)
    return {"traces":[{k:r.get(k) for k in ("trace_id","timestamp","endpoint","status","latency_ms")} for r in records],
            "notice":"Bounded redacted tail; identifiers are irrecoverable. Older traces may lack replay fields."}

@router.get("/traces/{trace_id}")
async def read_trace(trace_id:UUID,request:Request):
    records=await asyncio.to_thread(trace_logger(request).recent,100)
    record=next((r for r in records if r.get("trace_id")==str(trace_id)),None)
    if record is None: raise HTTPException(404,"Trace not found in this tenant's recent window.")
    return record
