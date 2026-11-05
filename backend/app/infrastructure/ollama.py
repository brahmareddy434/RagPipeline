import asyncio
import json
import math
from collections import OrderedDict
from contextvars import ContextVar
from typing import TypeVar
import httpx
from pydantic import BaseModel, ValidationError

T = TypeVar("T", bound=BaseModel)
call_metrics: ContextVar[list | None] = ContextVar("call_metrics", default=None)


class OllamaUnavailable(RuntimeError):
    pass


class OllamaClient:
    def __init__(self, base_url: str, chat_model: str, embed_model: str, timeout: float = 300.0):
        self.base_url = base_url.rstrip("/")
        self.chat_model, self.embed_model = chat_model, embed_model
        self.http = httpx.AsyncClient(timeout=httpx.Timeout(timeout, connect=5.0))
        self._semaphore = asyncio.Semaphore(2)
        # Query embeddings repeat constantly across evals, agent steps and the race.
        # Cache single-text embeds only; batched document embeds are one-off ingest work.
        self._embed_cache: OrderedDict[tuple[str, str], list[float]] = OrderedDict()
        self._embed_cache_limit = 512
        self.embed_cache_hits = 0

    async def close(self):
        await self.http.aclose()

    async def _request(self, path, payload=None):
        try:
            async with self._semaphore:
                response = await (self.http.get(self.base_url + path) if payload is None else self.http.post(self.base_url + path, json=payload))
            response.raise_for_status()
            data = response.json()
            if not isinstance(data, dict):
                raise ValueError("Expected JSON object")
            metrics = call_metrics.get()
            if metrics is not None:
                metrics.append({"endpoint": path, "model": (payload or {}).get("model"),
                                "request": payload, "response": data,
                                **{k: data.get(k) for k in ("prompt_eval_count", "eval_count", "total_duration", "load_duration")}})
            return data
        except (httpx.HTTPError, ValueError) as exc:
            raise OllamaUnavailable(f"Ollama request failed at {path}: {type(exc).__name__}. Check service and model availability.") from exc

    async def health(self):
        return await self._request("/api/tags")

    async def chat(self, messages, temperature=.1, **options):
        data = await self._request("/api/chat", {"model": self.chat_model, "messages": messages, "stream": False,
                                                "options": {"temperature": temperature, "num_predict": 700, **options}})
        try:
            content = data["message"]["content"]
            if not isinstance(content, str) or not content.strip():
                raise ValueError("Empty content")
            return content
        except (KeyError, TypeError, ValueError) as exc:
            raise OllamaUnavailable("Chat returned missing or empty content.") from exc

    async def structured(self, messages, schema: type[T], retries=2, temperature=0) -> T:
        conversation = [dict(m) for m in messages]
        last_error = None
        for attempt in range(retries + 1):
            data = await self._request("/api/chat", {"model": self.chat_model, "messages": conversation,
                "format": schema.model_json_schema(), "stream": False,
                **({"think": False} if "qwen3" in self.chat_model else {}),
                "options": {"temperature": temperature, "num_predict": 1200, "seed": 42}})
            try:
                raw = data["message"]["content"]
                return schema.model_validate_json(raw)
            except (KeyError, TypeError, ValidationError) as exc:
                last_error = exc
                details = "; ".join(error["msg"] for error in exc.errors(include_input=False)) if isinstance(exc, ValidationError) else "Missing response content"
                conversation.append({"role": "user", "content": "The response did not match the schema. Return valid JSON only. Correct these errors: " + details[:1000]})
        raise OllamaUnavailable("The model could not produce valid structured output after bounded retries.") from last_error

    async def embed(self, texts):
        if not texts:
            return []
        key = (self.embed_model, texts[0]) if len(texts) == 1 else None
        if key is not None and key in self._embed_cache:
            self._embed_cache.move_to_end(key)
            self.embed_cache_hits += 1
            return [list(self._embed_cache[key])]
        data = await self._request("/api/embed", {"model": self.embed_model, "input": texts, "truncate": False})
        rows = data.get("embeddings")
        if (not isinstance(rows, list) or len(rows) != len(texts) or not rows or
            any(not isinstance(row, list) or not row for row in rows)):
            raise OllamaUnavailable("Embedding count or shape is invalid.")
        dimension = len(rows[0])
        if any(len(row) != dimension or any(not isinstance(x, (float, int)) or not math.isfinite(x) for x in row) for row in rows):
            raise OllamaUnavailable("Embedding dimensions or values are invalid.")
        if key is not None:
            self._embed_cache[key] = list(rows[0])
            if len(self._embed_cache) > self._embed_cache_limit:
                self._embed_cache.popitem(last=False)
        return rows
