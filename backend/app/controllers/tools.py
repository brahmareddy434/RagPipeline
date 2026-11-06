from fastapi import Request
from app.schemas import ParallelToolRequest, ToolRequest

from fastapi import APIRouter
from app.controllers.dependencies import container

router = APIRouter()

@router.post("/tools/run")
async def run_tool(body: ToolRequest, request: Request):
    return await container(request).tools.run(body.question)


@router.post("/tools/parallel")
async def parallel_tools(body: ParallelToolRequest, request: Request):
    return {"results": await container(request).tools.parallel(body.questions)}
