"""Install requirements-optional.txt before these genuine library integrations."""
import argparse
import asyncio
import json
import os
from pydantic import BaseModel
from app.config import get_settings


class Person(BaseModel):
    name: str
    age: int


def instructor_demo():
    import instructor
    from openai import OpenAI
    s=get_settings()
    client=instructor.from_openai(OpenAI(base_url=s.ollama_base_url+"/v1",api_key="ollama"),mode=instructor.Mode.JSON)
    return client.chat.completions.create(model=s.ollama_chat_model,response_model=Person,
        messages=[{"role":"user","content":"Maya is 12 years old. Extract name and age."}],max_retries=2).model_dump()


def cross_encoder_demo():
    from app.retrieval import cross_encoder
    s=get_settings()
    candidates=["Employees receive 20 days of annual leave.","Bicycles have two wheels."]
    scores=cross_encoder(s.reranker_model).predict([("What is the vacation allowance?",c) for c in candidates])
    return [{"text":c,"score":float(score)} for c,score in zip(candidates,scores)]


async def cohere_demo():
    import httpx
    key=os.environ.get("COHERE_API_KEY")
    if not key:
        raise ValueError("Set COHERE_API_KEY in your environment. This optional call uses a paid external service.")
    async with httpx.AsyncClient(timeout=60) as client:
        response=await client.post("https://api.cohere.com/v2/rerank",headers={"Authorization":"Bearer "+key},
            json={"model":os.environ.get("COHERE_RERANK_MODEL","rerank-v3.5"),"query":"annual leave",
                  "documents":["Employees receive 20 leave days.","The office opens at nine."],"top_n":2})
        response.raise_for_status()
        return response.json()


async def ragas_demo():
    from openai import AsyncOpenAI
    from ragas.llms import llm_factory
    from ragas.metrics.collections import Faithfulness
    s=get_settings()
    client=AsyncOpenAI(base_url=s.ollama_base_url+"/v1",api_key="ollama")
    try:
        llm=llm_factory(s.ollama_chat_model,client=client)
        metric=Faithfulness(llm=llm)
        result=await metric.ascore(user_input="How many leave days?",response="Employees receive 20 leave days.",
                                  retrieved_contexts=["Employees receive 20 leave days."])
        return {"ragas_faithfulness":result.value}
    finally: await client.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("task",choices=["instructor","cross_encoder","cohere","ragas"])
    args=parser.parse_args()
    result=instructor_demo() if args.task=="instructor" else cross_encoder_demo() if args.task=="cross_encoder" else asyncio.run(cohere_demo() if args.task=="cohere" else ragas_demo())
    print(json.dumps(result,indent=2))
