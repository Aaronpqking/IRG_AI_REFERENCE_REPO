import json
import os
from pathlib import Path

from src.chat_contracts import SubmitChatTurnRequest
from src.chat_service import ChatService
from src.bootstrap.composition import (
    build_legacy_controlled_retrieval as build_controlled_retrieval,
)
from src.hybrid_retrieval import (
    FusedCandidate,
    HybridPdfEvidenceAdapter,
    HybridRetrievalConfig,
    LocalChunkLexicalRetriever,
    RetrievalChannelCandidate,
    build_hybrid_request,
    fuse_candidates,
)
from src.models import Answer, Chunk, ConversationTurn, RetrievedChunk, RetrievalResult, SourceRef, chunk_to_record
from src.multi_source_retrieval import ControlledDiscoveryRetrievalService
from src.product_applicability import ProductApplicabilityContext
from src.product_discovery import (
    build_discovery_query,
    build_retrieval_query,
    candidate_from_row,
)
from src.requested_products import TurnAnalysis


def chunk(chunk_id="chunk-1", **overrides):
    values = {
        "chunk_id": chunk_id,
        "document_id": f"doc-{chunk_id}",
        "filename": "manual.pdf",
        "relative_path": f"manuals/{chunk_id}/manual.pdf",
        "page_start": 1,
        "page_end": 1,
        "chunk_index": 0,
        "text": "MX-100 installation clearance instructions.",
        "technical_tokens_normalized": ("MX100",),
        "model_numbers": ("MX-100",),
    }
    values.update(overrides)
    return Chunk(**values)


class Embedding:
    def embed_query(self, text):
        return [0.1]


class VectorStore:
    def __init__(self, chunks=()):
        self.chunks = tuple(chunks)
        self.limits = []

    def search(self, query_vector, limit):
        self.limits.append(limit)
        return RetrievalResult(
            "query",
            tuple(RetrievedChunk(item, score, index + 1) for index, (item, score) in enumerate(self.chunks)),
        )


class FilteredVectorStore(VectorStore):
    def __init__(self, chunks=()):
        super().__init__(chunks)
        self.filters = []

    def search_filtered(self, query_vector, *, limit, filters):
        self.filters.append(filters)
        return self.search(query_vector, limit)


def adapter(local_chunks, vector_chunks=(), config=None):
    return HybridPdfEvidenceAdapter(
        Embedding(),
        VectorStore(vector_chunks),
        LocalChunkLexicalRetriever(tuple(local_chunks)),
        config or HybridRetrievalConfig(candidate_limit=20, final_limit=5, rrf_k=10),
    )


def write_composition_corpus(path):
    path.write_text(
        json.dumps(chunk_to_record(chunk("composition"))) + "\n",
        encoding="utf-8",
    )


def context(**overrides):
    values = {
        "read_model_product_id": 1,
        "product_name": "MX Grill",
        "brand": "Brand",
        "model": "MX-100",
        "mpn": "MX-100",
        "source_filenames": ("mx100.pdf",),
        "source_paths": ("manuals/mx100/mx100.pdf",),
    }
    values.update(overrides)
    return ProductApplicabilityContext(**values)


def retrieval_query(question):
    return build_retrieval_query(question)


def test_exact_model_candidate_retrieval():
    result = adapter([chunk("exact")]).retrieve(
        retrieval_query("What clearance does MX-100 need?")
    )

    assert result.retrieval.chunks[0].chunk.chunk_id == "exact"
    assert result.retrieval.chunks[0].matched_identifiers == ("MX100",)


def test_explicit_brand_and_identifier_constrain_semantic_candidates():
    store = FilteredVectorStore()
    hybrid = HybridPdfEvidenceAdapter(
        Embedding(),
        store,
        LocalChunkLexicalRetriever(()),
    )

    hybrid.retrieve(
        retrieval_query("What fuel does the Real Fyre G31 burner system use?")
    )

    assert store.filters == [
        {
            "manufacturer": "real_fyre",
            "exact_identifiers": ("G31",),
            "identifier_variants": ("G31",),
        }
    ]


def test_explicit_manufacturer_excludes_cross_brand_candidates():
    right = chunk(
        "right",
        manufacturer="real_fyre",
        brand="real_fyre",
        relative_path="real_fyre/g31/manual.pdf",
        technical_tokens_normalized=("G31",),
        model_numbers=("G31",),
    )
    wrong = chunk(
        "wrong",
        manufacturer="fire_magic",
        brand="fire_magic",
        relative_path="fire_magic/g31/manual.pdf",
        technical_tokens_normalized=("G31",),
        model_numbers=("G31",),
    )

    result = adapter([wrong, right]).retrieve(
        retrieval_query("Real Fyre G31 burner manual")
    )

    assert [item.chunk.chunk_id for item in result.retrieval.chunks] == ["right"]


def test_exact_part_candidate_retrieval():
    part = chunk("part", text="Replacement part 3598-20 thermostat knob.", technical_tokens_normalized=("359820",), model_numbers=(), part_numbers=("3598-20",))

    result = adapter([part]).retrieve(retrieval_query("What replaces 3598-20?"))

    assert result.retrieval.chunks[0].chunk.chunk_id == "part"
    assert result.retrieval.chunks[0].matched_identifiers == ("359820",)


def test_exact_identifier_not_matched_to_longer_neighboring_identifier():
    longer = chunk("longer", technical_tokens_normalized=("MX1000",), model_numbers=("MX-1000",), text="MX-1000 clearance.")

    request = build_hybrid_request(
        retrieval_query("What clearance does MX-100 need?")
    )
    found = LocalChunkLexicalRetriever((longer,)).exact_identifier_candidates(request)

    assert found == ()


def test_lexical_clearance_query_retrieval():
    result = adapter([chunk("clearance", text="Clearance from combustible construction is listed here.", technical_tokens_normalized=(), model_numbers=())]).retrieve(retrieval_query("What clearance is required?"))

    assert result.retrieval.chunks[0].chunk.chunk_id == "clearance"
    assert "clearance" in result.retrieval.chunks[0].matched_lexical_terms


def test_lexical_warning_query_retrieval():
    result = adapter([chunk("warning", text="Warning: shut off gas before service.", has_warning=True, technical_tokens_normalized=(), model_numbers=())]).retrieve(retrieval_query("Show the installation warning."))

    assert result.retrieval.chunks[0].chunk.chunk_id == "warning"
    assert "warning" in result.retrieval.chunks[0].matched_lexical_terms


def test_vector_only_miss_recovered_by_lexical_channel():
    lexical = chunk("lexical", text="Clearance table for the product.", technical_tokens_normalized=(), model_numbers=())
    semantic = chunk("semantic", text="Unrelated text.", technical_tokens_normalized=(), model_numbers=())

    result = adapter([lexical], [(semantic, 0.99)]).retrieve(
        retrieval_query("What clearance is required?")
    )

    assert result.retrieval.chunks[0].chunk.chunk_id == "lexical"


def test_lexical_miss_recovered_by_semantic_channel():
    semantic = chunk("semantic", text="Manufacturer spacing requirements.", technical_tokens_normalized=(), model_numbers=())

    result = adapter([], [(semantic, 0.99)]).retrieve(
        retrieval_query("What clearance is required?")
    )

    assert result.retrieval.chunks[0].chunk.chunk_id == "semantic"


def test_metadata_filtered_candidate_generation():
    preferred = chunk("preferred", filename="mx100.pdf", relative_path="manuals/mx100/mx100.pdf")

    result = adapter([preferred]).retrieve(
        retrieval_query("What clearance is required?"),
        product_context=context(),
    )

    provenance = result.retrieval.chunks[0].channel_provenance
    assert any(item["channel"] == "metadata_filter" for item in provenance)


def test_rrf_deterministic_ordering():
    a = RetrievalChannelCandidate(chunk("a"), "lexical", 1, 10, 1)
    b = RetrievalChannelCandidate(chunk("b"), "semantic_vector", 1, 0.9, 0.9)

    assert [item.chunk.chunk_id for item in fuse_candidates((b, a), rrf_k=60)] == ["a", "b"]
    assert [item.chunk.chunk_id for item in fuse_candidates((a, b), rrf_k=60)] == ["a", "b"]


def test_duplicate_candidate_merge():
    same = chunk("same")
    fused = fuse_candidates(
        (
            RetrievalChannelCandidate(same, "lexical", 1, 10, 1),
            RetrievalChannelCandidate(same, "semantic_vector", 2, 0.5, 0.5),
        )
    )

    assert len(fused) == 1
    assert {item.channel_name for item in fused[0].channel_candidates} == {"lexical", "semantic_vector"}


def test_channel_provenance_preserved():
    result = adapter([chunk("same")], [(chunk("same"), 0.8)]).retrieve(
        retrieval_query("What clearance does MX-100 need?")
    )

    channels = {item["channel"] for item in result.retrieval.chunks[0].channel_provenance}
    assert {"exact_identifier", "lexical", "semantic_vector"} <= channels


def test_document_diversity_cap():
    candidates = tuple(
        RetrievalChannelCandidate(chunk(f"doc-a-{index}", relative_path="manuals/a/manual.pdf", page_start=index, page_end=index), "lexical", index, 10 - index, 1)
        for index in range(1, 6)
    )

    fused = fuse_candidates(candidates, max_per_document=2, max_per_page_neighborhood=3, limit=10)

    assert len(fused) == 2


def test_exact_match_diversity_exception():
    candidates = tuple(
        RetrievalChannelCandidate(chunk(f"doc-a-{index}", relative_path="manuals/a/manual.pdf", page_start=index, page_end=index), "exact_identifier", index, 10 - index, 1, matched_identifiers=("MX100",))
        for index in range(1, 5)
    )

    fused = fuse_candidates(candidates, max_per_document=1, max_per_page_neighborhood=1, limit=10)

    assert len(fused) == 4


class Discovery:
    def __init__(self, rows):
        self.rows = tuple(rows)

    def discover(self, question):
        query = build_discovery_query(question)
        candidates = tuple(candidate_from_row(row, query) for row in self.rows)
        return type("DiscoveryResult", (), {"query": query, "candidates": candidates, "rows_returned": len(candidates), "rows_retained": len(candidates), "duration_ms": 1, "trace_id": "trace", "connection_id": None, "trace_path": None, "server_observation": None})()


class Store:
    def __init__(self):
        self.turns = []

    def save_turn(self, conversation_id, role, content, sources=None, model_name=None, latency_ms=None, token_count=None):
        turn_id = f"turn-{len(self.turns) + 1}"
        refs = tuple(SourceRef(turn_id=turn_id, **source) for source in sources or [])
        self.turns.append(ConversationTurn(turn_id, conversation_id, role, content, refs, model_name, latency_ms, token_count))
        return turn_id

    def get_recent_turns(self, conversation_id, limit=10):
        return tuple(
            turn for turn in self.turns
            if turn.conversation_id == conversation_id
        )[-limit:]


class Chat:
    model = "chat"
    last_metadata = {"response_model": "chat", "total_tokens": 1}

    def __init__(self):
        self.calls = 0

    def answer(self, question, context, **kwargs):
        self.calls += 1
        return Answer(question, "answer")


def row(**overrides):
    base = {"product_id": 10, "product_name": "MX Grill", "brand": "Brand", "model": "MX-100", "mpn": "MX-100", "categories": "Grills", "document_path": "manuals/mx100/mx100.pdf", "score": 1.0}
    base.update(overrides)
    return base


def test_inapplicable_fused_candidate_excluded_after_eligibility():
    wrong = chunk("wrong", filename="wrong.pdf", relative_path="manuals/wrong/wrong.pdf", model_numbers=("WRONG-1",), technical_tokens_normalized=("WRONG1",), text="Wrong clearance table.")
    service = ControlledDiscoveryRetrievalService(Discovery([row()]), adapter([wrong], []))

    result = service.retrieve("What clearance does MX-100 need?")

    assert result.context_chunks
    assert result.context_chunks[0].chunk_id == "runtime-response-packet"
    assert all("Wrong clearance table" not in item.text for item in result.context_chunks)
    assert all(source["chunk_id"] != "wrong" for source in result.answer_sources)


def test_unknown_applicability_remains_diagnostic_in_observe_mode():
    unknown = chunk("unknown", filename="generic.pdf", relative_path="manuals/generic.pdf", model_numbers=(), technical_tokens_normalized=(), text="Generic clearance table.")
    service = ControlledDiscoveryRetrievalService(Discovery([row(document_path=None)]), adapter([unknown], []))

    result = service.retrieve("What clearance does MX-100 need?")

    assert result.response_class == "ANSWER_SUPPORTED"
    assert result.evidence_status != "DIRECT_EVIDENCE_SUPPORT"


def test_turn_analysis_clarification_cannot_short_circuit_retrieval():
    service = ControlledDiscoveryRetrievalService(
        Discovery([row()]),
        adapter([chunk("canonical")], []),
    )
    question = "What clearance does MX-100 need?"

    result = service.retrieve(
        question,
        turn_analysis=TurnAnalysis(
            literal_question=question,
            product_requests=(),
            clarification_question="Which product did you mean?",
        ),
    )

    assert result.context_chunks
    assert any(item.chunk_id == "canonical" for item in result.context_chunks)
    assert result.response_class != "CLARIFICATION_REQUIRED"


def test_terminal_evidence_decision_becomes_model_qualified_response():
    chat = Chat()
    service = ChatService(Store(), Embedding(), VectorStore(), chat, controlled_retrieval=ControlledDiscoveryRetrievalService(Discovery([]), adapter([chunk("related")], [])))

    response = service.submit_chat_turn(SubmitChatTurnRequest("emp", "conv", "What clearance does AOG24 need?"))

    assert chat.calls == 1
    assert response.model_name == "chat"
    assert response.execution_trace["fallback_used"] is False


def test_aog24_ambiguity_is_diagnostic_in_observe_mode():
    service = ControlledDiscoveryRetrievalService(Discovery([]), adapter([chunk("aog", filename="AOG24LN.pdf", relative_path="grills/l_series/24/builtin/2026/om/AOG24LN.pdf")], []))

    result = service.retrieve("What clearance does AOG24 need?")

    assert result.response_class == "ANSWER_SUPPORTED"
    assert result.evidence_status == "AMBIGUOUS_CANDIDATES"
    assert result.context_chunks
    assert result.context_chunks[0].chunk_id == "runtime-response-packet"


def test_api_hybrid_composition(monkeypatch, tmp_path):
    _product_db_env(monkeypatch)
    monkeypatch.setenv("PRODUCT_DISCOVERY_ENABLED", "1")
    monkeypatch.setenv("HYBRID_CHUNKS_PATH", str(tmp_path / "chunks.jsonl"))
    write_composition_corpus(tmp_path / "chunks.jsonl")
    controlled = build_controlled_retrieval(Embedding(), VectorStore())

    assert isinstance(controlled.pdf_evidence, HybridPdfEvidenceAdapter)


def test_cli_hybrid_composition(monkeypatch, tmp_path):
    from src.scripts import conversation_cli
    from src.bootstrap import composition

    _product_db_env(monkeypatch)
    monkeypatch.setenv("PRODUCT_DISCOVERY_ENABLED", "1")
    monkeypatch.setenv("HYBRID_CHUNKS_PATH", str(tmp_path / "chunks.jsonl"))
    write_composition_corpus(tmp_path / "chunks.jsonl")
    monkeypatch.setattr(
        composition,
        "_online_components",
        lambda collection, settings=None: (
            Embedding(),
            VectorStore(),
            Chat(),
            collection or "AOG-TE",
        ),
    )
    monkeypatch.setattr(
        composition,
        "build_controlled_retrieval",
        composition.build_legacy_controlled_retrieval,
    )
    args = conversation_cli.build_parser().parse_args(
        [
            "--online",
            "--collection",
            "AOG-TE",
            "--local-store",
            str(tmp_path / "store.json"),
        ]
    )

    components = conversation_cli._components(args)

    assert isinstance(components[-1].pdf_evidence, HybridPdfEvidenceAdapter)


def test_evaluator_hybrid_composition(monkeypatch, tmp_path):
    from src.scripts.run_unified_answering_eval import build_production_app
    from src.bootstrap import composition

    _product_db_env(monkeypatch)
    monkeypatch.setenv("PRODUCT_DISCOVERY_ENABLED", "1")
    monkeypatch.setenv("HYBRID_CHUNKS_PATH", str(tmp_path / "chunks.jsonl"))
    write_composition_corpus(tmp_path / "chunks.jsonl")
    monkeypatch.setattr(
        composition,
        "_online_components",
        lambda collection, settings=None: (
            Embedding(),
            VectorStore(),
            Chat(),
            collection or "AOG-TE",
        ),
    )
    monkeypatch.setattr(
        composition,
        "build_controlled_retrieval",
        composition.build_legacy_controlled_retrieval,
    )
    app = build_production_app(Path.cwd(), tmp_path, "AOG-TE", 5)

    assert isinstance(app.service.controlled_retrieval.pdf_evidence, HybridPdfEvidenceAdapter)


def test_hybrid_retrieval_is_independent_of_configuration_policy(
    monkeypatch,
    tmp_path,
):
    _product_db_env(monkeypatch)
    monkeypatch.setenv("PRODUCT_DISCOVERY_ENABLED", "1")
    monkeypatch.setenv("HYBRID_PDF_RETRIEVAL_ENABLED", "0")
    monkeypatch.setenv("HYBRID_CHUNKS_PATH", str(tmp_path / "chunks.jsonl"))
    write_composition_corpus(tmp_path / "chunks.jsonl")

    for mode in ("off", "observe", "enforce"):
        monkeypatch.setenv(
            "PDF_CONFIGURATION_APPLICABILITY_MODE",
            mode,
        )
        controlled = build_controlled_retrieval(
            Embedding(),
            VectorStore(),
        )
        assert isinstance(
            controlled.pdf_evidence,
            HybridPdfEvidenceAdapter,
        )


def _product_db_env(monkeypatch):
    monkeypatch.setenv("PRODUCT_DB_HOST", "127.0.0.1")
    monkeypatch.setenv("PRODUCT_DB_NAME", "db")
    monkeypatch.setenv("PRODUCT_DB_USER", "user")
    monkeypatch.setenv("PRODUCT_DB_PASSWORD", "password")


def test_no_qdrant_mutation_in_hybrid_module():
    text = Path("src/hybrid_retrieval.py").read_text(encoding="utf-8")

    assert "create_collection" not in text
    assert "delete_collection" not in text
    assert ".upsert(" not in text


def test_no_database_writes_in_hybrid_module():
    text = Path("src/hybrid_retrieval.py").read_text(encoding="utf-8").upper()

    assert all(term not in text for term in ("INSERT ", "UPDATE ", "DELETE ", "DROP ", "ALTER "))


def test_no_product_specific_aliases_in_hybrid_module():
    text = Path("src/hybrid_retrieval.py").read_text(encoding="utf-8").casefold()

    assert "aog24ln" not in text
    assert "aog24-ga" not in text


def test_customer_source_refs_match_admitted_evidence_only():
    good = chunk("good", filename="mx100.pdf", relative_path="manuals/mx100/mx100.pdf", text="MX-100 clearance table.", model_numbers=("MX-100",), technical_tokens_normalized=("MX100",))
    bad = chunk("bad", filename="wrong.pdf", relative_path="manuals/wrong/wrong.pdf", text="WRONG-1 clearance table.", model_numbers=("WRONG-1",), technical_tokens_normalized=("WRONG1",))
    service = ControlledDiscoveryRetrievalService(Discovery([row()]), adapter([bad, good], []))

    result = service.retrieve("What clearance does MX-100 need?")

    source_ids = {source["chunk_id"] for source in result.answer_sources}
    context_ids = {item.chunk_id for item in result.context_chunks}
    assert source_ids <= context_ids | {"product_details:10"}
    assert "bad" not in source_ids
