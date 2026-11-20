from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.bootstrap.settings import (
    RuntimeSettings,
    required_online_collection,
    resolved_path,
)
from src.chat_service import ChatService
from src.conversation_history import BoundedConversation
from src.models import Answer, Chunk, RetrievedChunk, RetrievalResult
from src.ports import (
    ChatModelPort,
    ControlledRetrievalPort,
    ConversationStorePort,
    EmbeddingPort,
    VectorStorePort,
)
from src.prompt_loader import (
    ANSWER_GENERATION_PROMPT_FAMILY,
    RESPONSE_PACKET_PROMPT_FAMILY,
    TURN_ANALYSIS_PROMPT_FAMILY,
    LoadedPrompt,
    load_configured_prompt,
)
from src.runtime_env import load_project_env


@dataclass(frozen=True)
class RuntimeComponents:
    store: ConversationStorePort
    embedding: EmbeddingPort
    vector_store: VectorStorePort
    chat_model: ChatModelPort
    controlled_retrieval: ControlledRetrievalPort | None
    manifest: dict[str, object]


class SmokeEmbedding:
    def embed_query(self, text: str) -> list[float]:
        return [0.1, 0.2]


class SmokeVectorStore:
    def search(self, query_vector: list[float], limit: int) -> RetrievalResult:
        chunk = Chunk(
            "offline-smoke-chunk",
            "Offline smoke technical context for a configured product.",
            1,
            1,
            filename="offline_smoke_manual.pdf",
            document_id="offline-smoke-doc",
            relative_path="offline/offline_smoke_manual.pdf",
            technical_tokens_normalized=("SMK100",),
        )
        return RetrievalResult("offline", (RetrievedChunk(chunk, 0.9, 1),))


class SmokeChat:
    provider = "offline_smoke"
    model = "offline-smoke-chat"

    def __init__(self, answer_prompt: LoadedPrompt | None = None) -> None:
        self.answer_prompt = answer_prompt or load_configured_prompt(
            ANSWER_GENERATION_PROMPT_FAMILY
        )

    def answer(
        self,
        question: str,
        context: tuple[Chunk, ...],
        *,
        conversation: BoundedConversation | None = None,
    ) -> Answer:
        from src.unified_answer_context import estimate_tokens, serialize_model_context

        chunk = next(
            (
                item
                for item in context
                if item.chunk_id != "runtime-response-packet"
                and (item.relative_path or item.filename)
            ),
            context[-1],
        )
        serialized = serialize_model_context(
            question,
            context,
            conversation=conversation,
        )
        metadata = {
            "provider": self.provider,
            "requested_model": self.model,
            "response_model": self.model,
            "total_tokens": 0,
            "system_prompt": self.answer_prompt.text,
            "input": serialized,
            "input_characters": len(serialized),
            "estimated_input_tokens": estimate_tokens(serialized),
            "ordered_context_chunk_ids": [item.chunk_id for item in context],
            "prompt_artifacts": {
                ANSWER_GENERATION_PROMPT_FAMILY: (
                    self.answer_prompt.identity()
                ),
            },
        }
        source = chunk.relative_path or chunk.filename
        return Answer(
            question=question,
            answer=f"Offline smoke answer. [source: {source}, page {chunk.page_start}]",
            metadata=metadata,
        )


def build_legacy_controlled_retrieval(
    embedding: EmbeddingPort,
    vector_store: VectorStorePort,
    settings: RuntimeSettings | None = None,
    active_prompts: Mapping[str, LoadedPrompt] | None = None,
) -> ControlledRetrievalPort | None:
    settings = settings or RuntimeSettings.from_environment(Path.cwd())
    prompts = dict(active_prompts or settings.active_prompts())
    if not settings.product_discovery_enabled:
        return None
    from src.adapters.product_mysql import (
        ProductDiscoveryConfig,
        ProductMySQLDiscoveryAdapter,
    )
    from src.corpus_neighbors import CorpusNeighborIndex
    from src.hybrid_retrieval import (
        HybridPdfEvidenceAdapter,
        LocalChunkLexicalRetriever,
    )
    from src.local_corpus_readiness import (
        load_required_local_corpus,
        ready_diagnostics,
        require_lexical_index_ready,
        require_neighbor_index_ready,
        reuse_loaded_local_corpus,
    )
    from src.multi_source_retrieval import ControlledDiscoveryRetrievalService

    chunks_path = settings.hybrid_chunks_path
    config = settings.hybrid_retrieval_config
    lexical_corpus = load_required_local_corpus(
        chunks_path,
        project_root=settings.project_root,
        dependency="local_lexical_corpus",
        expected_sha256=settings.hybrid_chunks_sha256,
    )
    if settings.context_chunks_path == chunks_path:
        context_corpus = reuse_loaded_local_corpus(
            lexical_corpus,
            dependency="local_context_corpus",
            expected_sha256=settings.context_chunks_sha256,
        )
    else:
        context_corpus = load_required_local_corpus(
            settings.context_chunks_path,
            project_root=settings.project_root,
            dependency="local_context_corpus",
            expected_sha256=settings.context_chunks_sha256,
        )
    lexical_retriever = LocalChunkLexicalRetriever(
        lexical_corpus.chunks,
        lexical_candidate_limit=config.lexical_query_candidate_limit,
    )
    lexical_readiness = require_lexical_index_ready(
        lexical_retriever,
        lexical_corpus,
    )
    neighbor_index = CorpusNeighborIndex(context_corpus.chunks)
    neighbor_readiness = require_neighbor_index_ready(
        neighbor_index,
        context_corpus,
    )
    pdf_evidence = HybridPdfEvidenceAdapter(
        embedding,
        vector_store,
        lexical_retriever,
        config,
    )
    retriever_type = "hybrid"
    product_adapter = ProductMySQLDiscoveryAdapter(
        ProductDiscoveryConfig(
            **vars(settings.require_product_database())
        )
    )
    service = ControlledDiscoveryRetrievalService(
        product_adapter,
        pdf_evidence,
        corpus_neighbors=neighbor_index,
        expansion_config=settings.corpus_expansion_config,
        product_context_max_chars=settings.product_context_max_chars,
        grounding_validation_mode=settings.grounding_validation_mode,
        pdf_configuration_applicability_mode=(
            settings.pdf_configuration_applicability_mode
        ),
        collection_identity=settings.qdrant_collection,
        response_packet_prompt=prompts[RESPONSE_PACKET_PROMPT_FAMILY],
        product_configuration=product_adapter,
    )
    service.retriever_type = retriever_type
    service.readiness = ready_diagnostics(
        lexical_corpus,
        lexical_readiness,
        context_corpus,
        neighbor_readiness,
    )
    return service


def build_controlled_retrieval(
    embedding: EmbeddingPort,
    vector_store: VectorStorePort,
    settings: RuntimeSettings | None = None,
    active_prompts: Mapping[str, LoadedPrompt] | None = None,
) -> ControlledRetrievalPort:
    """Build the authoritative V1.9.39 canonical direct-RAG retriever.

    ``vector_store`` and ``active_prompts`` remain in the composition boundary
    for API compatibility.  The frozen Path A retrieval implementation uses
    the governed local structural view index and the supplied embedding port;
    it does not query or mutate the configured Qdrant collection.
    """

    del vector_store, active_prompts
    settings = settings or RuntimeSettings.from_environment(Path.cwd())
    from src.docling_structural.canonical_direct_rag_v1_9_39 import (
        CanonicalDirectRagRetrievalService,
        build_canonical_direct_rag_composition,
    )

    composition = build_canonical_direct_rag_composition(
        settings.project_root
    )
    return CanonicalDirectRagRetrievalService(
        embedding=embedding,
        composition=composition,
    )


def _build_store(
    root: Path,
    store_name: str,
    local_store: str | Path | None,
    settings: RuntimeSettings,
) -> ConversationStorePort:
    if store_name == "mysql":
        from src.adapters.conversation_store_mysql import ConversationStoreMySQL

        return ConversationStoreMySQL(
            connection_config=settings.require_conversation_database()
        )
    if local_store is None:
        raise RuntimeError("--local-store is required for json store")
    from src.adapters.conversation_store_json import JsonConversationStore

    return JsonConversationStore(resolved_path(root, local_store))


def _online_components(
    collection: str | None,
    settings: RuntimeSettings | None = None,
    active_prompts: Mapping[str, LoadedPrompt] | None = None,
) -> tuple[EmbeddingPort, VectorStorePort, ChatModelPort, str]:
    from src.adapters.chat_openai import OpenAIChatAdapter
    from src.adapters.embeddings_openai import OpenAIEmbeddingAdapter
    from src.adapters.vector_qdrant import QdrantVectorStoreAdapter

    settings = settings or RuntimeSettings.from_environment(
        Path.cwd(),
        collection=collection,
    )
    settings.require_online()
    prompts = dict(active_prompts or settings.active_prompts())
    collection_name = settings.qdrant_collection
    embedding = OpenAIEmbeddingAdapter(
        api_key=settings.openai_api_key,
        model=settings.embedding_model,
        dimensions=settings.embedding_dimensions,
        batch_size=settings.embedding_batch_size,
    )
    vector_store = QdrantVectorStoreAdapter(
        url=settings.qdrant_url,
        api_key=settings.qdrant_api_key,
        collection_name=collection_name,
        vector_name=settings.qdrant_vector_name,
        distance=settings.qdrant_distance,
        timeout_seconds=settings.qdrant_timeout_seconds,
    )
    return (
        embedding,
        vector_store,
        OpenAIChatAdapter(
            api_key=settings.openai_api_key,
            model=settings.chat_model,
            answer_prompt=prompts[ANSWER_GENERATION_PROMPT_FAMILY],
            configured_prompt_artifacts={
                ANSWER_GENERATION_PROMPT_FAMILY: prompts[
                    ANSWER_GENERATION_PROMPT_FAMILY
                ].identity()
            },
            enabled_prompt_families={ANSWER_GENERATION_PROMPT_FAMILY},
        ),
        collection_name,
    )


def build_online_adapters(
    project_root: str | Path | None,
    collection: str | None = None,
) -> tuple[EmbeddingPort, VectorStorePort, ChatModelPort]:
    load_project_env(project_root)
    settings = RuntimeSettings.from_environment(
        project_root,
        collection=collection,
    )
    prompts = settings.active_prompts()
    embedding, vector_store, chat_model, _ = _online_components(
        collection,
        settings,
    )
    required_online_collection(collection)
    return embedding, vector_store, chat_model


def build_runtime_components(
    *,
    project_root: str | Path | None,
    store_name: str,
    local_store: str | Path | None,
    mode: str,
    collection: str | None = None,
    ensure_schema: bool = False,
) -> RuntimeComponents:
    root = Path(project_root or Path.cwd()).resolve()
    load_project_env(root)
    settings = RuntimeSettings.from_environment(root, collection=collection)
    prompts = settings.active_prompts()
    manifest = settings.manifest(prompts)
    manifest.update({"runtime_mode": mode, "store": store_name})
    if mode == "offline_smoke":
        embedding: EmbeddingPort = SmokeEmbedding()
        vector_store: VectorStorePort = SmokeVectorStore()
        chat_model: ChatModelPort = SmokeChat(
            prompts[ANSWER_GENERATION_PROMPT_FAMILY]
        )
        controlled = None
        manifest.update(
            {
                "retriever_type": "offline_smoke",
                "hybrid_retrieval_readiness": {
                    "status": "NOT_REQUIRED",
                    "reason_code": "LOCAL_CORPUS_NOT_REQUIRED",
                },
                "qdrant_collection": None,
                "chat_model": SmokeChat.model,
            }
        )
    elif mode == "online":
        embedding, vector_store, chat_model, collection_name = _online_components(
            collection,
            settings,
        )
        collection_name = required_online_collection(collection)
        controlled = build_controlled_retrieval(
            embedding,
            vector_store,
            settings,
        )
        manifest.update(
            {
                "retriever_type": getattr(
                    controlled, "retriever_type", "standard_pdf"
                )
                if controlled
                else "standard_pdf",
                "qdrant_collection": collection_name,
                "chat_model": getattr(chat_model, "model", manifest.get("chat_model")),
                "hybrid_retrieval_readiness": getattr(
                    controlled,
                    "readiness",
                    {
                        "status": "NOT_REQUIRED",
                        "reason_code": "LOCAL_CORPUS_NOT_REQUIRED",
                    },
                ),
            }
        )
    else:
        raise RuntimeError("mode must be offline_smoke or online")
    store = _build_store(root, store_name, local_store, settings)
    if ensure_schema or store_name == "json":
        store.ensure_schema()
    manifest["turn_runtime_metadata"] = {
        "status": "optional_lazy_check",
        "required_for_core_chat": False,
    }
    return RuntimeComponents(
        store, embedding, vector_store, chat_model, controlled, manifest
    )


def build_chat_service(components: RuntimeComponents) -> ChatService:
    return ChatService(
        components.store,
        components.embedding,
        components.vector_store,
        components.chat_model,
        controlled_retrieval=components.controlled_retrieval,
        grounding_validation_mode=components.manifest[
            "grounding_validation_mode"
        ],
        validation_mode=components.manifest["validation_mode"],
    )


def build_evaluation_runtime(**kwargs: Any) -> RuntimeComponents:
    return build_runtime_components(**kwargs)
