"""Optional implementation demonstrations after the theory-only Week 1."""
import argparse
import asyncio
import json
import math
from collections import Counter
import numpy as np
from app.config.settings import get_settings
from app.infrastructure.ollama import OllamaClient, call_metrics


def sampling():
    logits=np.array([3.,2.,1.,0.])
    result={}
    for temperature in (.2,1.,2.):
        p=np.exp((logits-logits.max())/temperature);p=p/p.sum()
        result[str(temperature)]=dict(zip(["cat","dog","bird","car"],p.tolist()))
    return {"illustrative_logits":logits.tolist(),"temperature_probabilities":result,
            "greedy":"cat","note":"Invented four-token distribution, not model output. top-k keeps k candidates; top-p keeps a probability prefix."}


def cost(input_tokens,output_tokens,input_rate,output_rate):
    if min(input_tokens,output_tokens,input_rate,output_rate)<0:
        raise ValueError("Counts and prices cannot be negative")
    return (input_tokens*input_rate+output_tokens*output_rate)/1_000_000


async def live(task):
    settings=get_settings()
    client=OllamaClient(settings.ollama_base_url,settings.ollama_chat_model,settings.ollama_embed_model)
    try:
        if task=="embeddings":
            texts=["Annual leave allowance","How much vacation do I receive?","A bicycle has two wheels."]
            vectors=np.asarray(await client.embed(texts));vectors/=np.maximum(np.linalg.norm(vectors,axis=1,keepdims=True),1e-12)
            return {"texts":texts,"dimensions":vectors.shape[1],"cosine_similarity":(vectors@vectors.T).tolist()}
        outputs=[]
        for temperature in (0,0,.8,.8):
            metrics=[];token=call_metrics.set(metrics)
            try:
                answer=await client.chat([{"role":"user","content":"Name a fictional bakery in three words."}],temperature,top_p=.9,top_k=40,num_predict=60)
                outputs.append({"temperature":temperature,"answer":answer,"actual_ollama_counts":metrics})
            finally: call_metrics.reset(token)
        return outputs
    finally: await client.close()


if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("task",choices=["sampling","cost","embeddings","temperature"])
    args=parser.parse_args()
    result=sampling() if args.task=="sampling" else {"hypothetical_USD":cost(2000,500,1,4),"rates_are_examples_not_vendor_prices":True} if args.task=="cost" else asyncio.run(live(args.task))
    print(json.dumps(result,indent=2))
