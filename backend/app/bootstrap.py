from dataclasses import dataclass
from app.agents.loop import PolicyAgent
from app.agents.tools import ToolRegistry
from app.rag.chunking import TextChunker
from app.agents.memory import VectorMemory
from app.rag.loading import DocumentLoader
from app.infrastructure.ollama import OllamaClient
from app.rag.prompts import PromptBuilder
from app.rag.retrieval import HybridRetriever, KeywordRetriever
from app.services import EvaluationService, IngestionService, RagService
from app.services.tools import Calculator, OrderRepository, ToolService
from app.repositories.vector_store import VectorStore
from app.agents.workflow import FixedWorkflow


@dataclass
class Container:
    ollama: OllamaClient
    ingestion: IngestionService
    rag: RagService
    evaluation: EvaluationService
    tools: ToolService
    store: VectorStore
    agent: PolicyAgent
    workflow: FixedWorkflow
    memory: VectorMemory
    registry: ToolRegistry

    @classmethod
    def build(cls, settings):
        ollama = OllamaClient(settings.ollama_base_url, settings.ollama_chat_model, settings.ollama_embed_model,
                              settings.ollama_timeout_seconds)
        store = VectorStore(str(settings.chroma_path), settings.collection_name, ollama, settings.embedding_batch_size)
        retriever = HybridRetriever(store, KeywordRetriever(), reranker_model=settings.reranker_model)
        prompts = PromptBuilder(compact=settings.compact_prompt)
        calculator = Calculator()
        registry = ToolRegistry(retriever, calculator, k=settings.agent_search_k)
        # Agent memory is a separate collection so recalled facts can never be mistaken
        # for indexed policy text by the document endpoints.
        memory_store = VectorStore(str(settings.chroma_path), settings.memory_collection_name,
                                   ollama, settings.embedding_batch_size)
        memory = VectorMemory(memory_store)
        return cls(ollama=ollama,
            ingestion=IngestionService(DocumentLoader(), TextChunker(settings.chunk_size, settings.chunk_overlap), store, settings.max_document_chars),
            rag=RagService(retriever, ollama, prompts, settings.min_relevance,
                           settings.evidence_keep_ratio, settings.max_context_chunks),
            evaluation=EvaluationService(retriever),
            tools=ToolService(ollama, calculator, OrderRepository()), store=store,
            agent=PolicyAgent(ollama, registry, prompts, memory),
            workflow=FixedWorkflow(retriever, ollama, prompts, registry, settings.workflow_search_k),
            memory=memory, registry=registry)
