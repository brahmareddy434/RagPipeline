from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Principal(BaseModel):
    tenant: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    role: Literal["reader", "writer", "admin"] = "reader"


class Settings(BaseSettings):
    """All changeable application values, loaded from .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    app_name: str = "Local Ollama RAG Tutor"
    ollama_base_url: str = "http://localhost:11434"
    ollama_chat_model: str = "llama3.2:3b"
    ollama_embed_model: str = "nomic-embed-text:latest"
    chroma_path: Path = Path("./data/chroma")
    collection_name: str = "knowledge_base"
    trace_log_path: Path = Path("./logs/ask_traces.jsonl")
    chunk_size: int = Field(900, ge=200, le=4000)
    chunk_overlap: int = Field(150, ge=0, le=1000)
    top_k: int = Field(4, ge=1, le=20)
    min_relevance: float = Field(0.20, ge=0, le=1)
    max_upload_bytes: int = Field(10_000_000, ge=1024, le=100_000_000)
    max_document_chars: int = Field(1_000_000, ge=1000)
    embedding_batch_size: int = Field(32, ge=1, le=256)
    reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"
    # /ask precision. Retrieval returns top_k chunks even when one is relevant; keep only
    # those within this fraction of the best match, and cap how many reach the model.
    # 0 disables either filter. Measured in course/ask_experiment.py.
    evidence_keep_ratio: float = Field(0.92, ge=0, le=1)
    max_context_chunks: int = Field(3, ge=0, le=20)
    # Measured OFF: the compact prompt lost 15 assertion points (course/ask_experiment.py).
    compact_prompt: bool = False
    # CPU-only inference on a 3-4B model with a six-chunk context can exceed two minutes,
    # which showed up as httpx ReadTimeout during the Week 7 race. Configurable, not hardcoded.
    ollama_timeout_seconds: float = Field(300.0, gt=0, le=1800)
    memory_collection_name: str = "agent_memory"
    agent_search_k: int = Field(4, ge=1, le=20)
    workflow_search_k: int = Field(6, ge=1, le=20)
    access_mode: Literal["local", "authenticated"] = "local"
    # SHA-256 digests are the keys; plaintext access tokens never belong in config.
    api_token_hashes: dict[str, Principal] = Field(default_factory=dict, repr=False)
    allowed_origins: list[str] = ["http://localhost:5173", "http://127.0.0.1:5173"]
    allowed_hosts: list[str] = ["localhost", "127.0.0.1", "[::1]", "testserver"]
    requests_per_minute: int = Field(120, ge=1, le=10000)
    redact_names: list[str] = Field(default_factory=list, repr=False)

    @model_validator(mode="after")
    def valid_overlap(self):
        if self.chunk_overlap >= self.chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        if self.access_mode == "authenticated" and not self.api_token_hashes:
            raise ValueError("Authenticated mode requires API_TOKEN_HASHES with scoped token digests.")
        if any(len(k) != 64 or any(c not in "0123456789abcdef" for c in k) for k in self.api_token_hashes):
            raise ValueError("API_TOKEN_HASHES keys must be lowercase SHA-256 hex digests.")
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()
