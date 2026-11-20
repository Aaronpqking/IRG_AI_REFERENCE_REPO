from __future__ import annotations

import json
import re
from dataclasses import dataclass
from dataclasses import replace
from pathlib import Path
from typing import Any

from src.models import Chunk, chunk_from_record
from src.technical_text import extract_document_model_numbers


@dataclass(frozen=True)
class CorpusExpansionConfig:
    max_selected_documents: int = 3
    max_selected_anchors: int = 5
    max_neighbors_per_anchor: int = 4
    max_page_distance: int = 1
    max_chunks_per_document: int = 8
    max_pdf_context_chars: int = 12000


@dataclass(frozen=True)
class CorpusExpansionResult:
    chunks: tuple[Chunk, ...]
    diagnostics: dict[str, Any]


class CorpusNeighborIndex:
    def __init__(self, chunks: tuple[Chunk, ...]) -> None:
        grouped: dict[str, list[Chunk]] = {}
        for chunk in chunks:
            grouped.setdefault(_document_key(chunk), []).append(chunk)
        self.document_model_numbers: dict[str, tuple[str, ...]] = {}
        self.document_catalog_path_aliases: dict[str, tuple[str, ...]] = {}
        self.document_configurations: dict[str, tuple[str, ...]] = {}
        self.document_configuration_exclusions: dict[
            str, tuple[str, ...]
        ] = {}
        self.document_configuration_coverage_complete: dict[str, bool] = {}
        self.document_corpus_taxonomy_validated: dict[str, bool] = {}
        for key, document_chunks in grouped.items():
            declared = tuple(
                dict.fromkeys(
                    model
                    for chunk in document_chunks
                    for model in chunk.document_model_numbers
                    if model
                )
            )
            self.document_model_numbers[key] = (
                declared
                or extract_document_model_numbers(document_chunks)
            )
            self.document_catalog_path_aliases[key] = tuple(
                dict.fromkeys(
                    alias
                    for chunk in document_chunks
                    for alias in (
                        chunk.relative_path,
                        *chunk.catalog_path_aliases,
                    )
                    if alias
                )
            )
            self.document_configurations[key] = tuple(
                dict.fromkeys(
                    value
                    for chunk in document_chunks
                    for value in chunk.document_configurations
                    if value
                )
            )
            self.document_configuration_exclusions[key] = tuple(
                dict.fromkeys(
                    value
                    for chunk in document_chunks
                    for value in chunk.document_configuration_exclusions
                    if value
                )
            )
            self.document_configuration_coverage_complete[key] = any(
                chunk.document_configuration_coverage_complete
                for chunk in document_chunks
            )
            self.document_corpus_taxonomy_validated[key] = any(
                chunk.corpus_taxonomy_validated
                for chunk in document_chunks
            )
        self.chunks = tuple(
            replace(
                chunk,
                document_model_numbers=self.document_model_numbers.get(
                    _document_key(chunk),
                    (),
                ),
                catalog_path_aliases=(
                    self.document_catalog_path_aliases.get(
                        _document_key(chunk),
                        (),
                    )
                ),
                document_configurations=(
                    self.document_configurations.get(
                        _document_key(chunk),
                        (),
                    )
                ),
                document_configuration_exclusions=(
                    self.document_configuration_exclusions.get(
                        _document_key(chunk),
                        (),
                    )
                ),
                document_configuration_coverage_complete=(
                    self.document_configuration_coverage_complete.get(
                        _document_key(chunk),
                        False,
                    )
                ),
                corpus_taxonomy_validated=(
                    self.document_corpus_taxonomy_validated.get(
                        _document_key(chunk),
                        False,
                    )
                ),
            )
            if (
                self.document_model_numbers.get(_document_key(chunk))
                and chunk.document_model_numbers
                != self.document_model_numbers[_document_key(chunk)]
            )
            or (
                chunk.catalog_path_aliases
                != self.document_catalog_path_aliases.get(
                    _document_key(chunk),
                    (),
                )
            )
            or (
                chunk.document_configurations
                != self.document_configurations.get(
                    _document_key(chunk),
                    (),
                )
            )
            or (
                chunk.document_configuration_exclusions
                != self.document_configuration_exclusions.get(
                    _document_key(chunk),
                    (),
                )
            )
            or (
                chunk.document_configuration_coverage_complete
                != self.document_configuration_coverage_complete.get(
                    _document_key(chunk),
                    False,
                )
            )
            or (
                chunk.corpus_taxonomy_validated
                != self.document_corpus_taxonomy_validated.get(
                    _document_key(chunk),
                    False,
                )
            )
            else chunk
            for chunk in chunks
        )
        self.by_chunk_id = {
            chunk.chunk_id: chunk for chunk in self.chunks
        }
        self.by_document_index: dict[tuple[str, int], Chunk] = {}
        self.by_document_page: dict[tuple[str, int], list[Chunk]] = {}
        self.by_document: dict[str, list[Chunk]] = {}
        for chunk in self.chunks:
            key = _document_key(chunk)
            self.by_document.setdefault(key, []).append(chunk)
            self.by_document_index[(key, chunk.chunk_index)] = chunk
            for page in range(chunk.page_start, chunk.page_end + 1):
                self.by_document_page.setdefault((key, page), []).append(chunk)
        for key, values in self.by_document.items():
            values.sort(key=_chunk_order)
        for key, values in self.by_document_page.items():
            values.sort(key=_chunk_order)

    @classmethod
    def empty(cls) -> "CorpusNeighborIndex":
        return cls(())

    @classmethod
    def from_jsonl(cls, path: str | Path) -> "CorpusNeighborIndex":
        source = Path(path)
        if not source.exists():
            return cls.empty()
        chunks = []
        for line in source.read_text(encoding="utf-8").splitlines():
            if line.strip():
                chunks.append(chunk_from_record(json.loads(line)))
        return cls(tuple(chunks))

    def expand(
        self,
        selected: tuple[Chunk, ...],
        config: CorpusExpansionConfig | None = None,
    ) -> CorpusExpansionResult:
        cfg = config or CorpusExpansionConfig()
        selected_docs = _first_documents(selected, cfg.max_selected_documents)
        anchors = tuple(
            chunk for chunk in selected
            if _document_key(chunk) in selected_docs
        )[: cfg.max_selected_anchors]
        selected_ids = {chunk.chunk_id for chunk in selected}
        expanded: dict[str, Chunk] = {}
        reasons: dict[str, list[str]] = {}
        per_doc_counts: dict[str, int] = {}
        total_chars = 0
        truncated = False

        def add(chunk: Chunk, reason: str) -> bool:
            nonlocal total_chars, truncated
            doc_key = _document_key(chunk)
            if per_doc_counts.get(doc_key, 0) >= cfg.max_chunks_per_document:
                return False
            if chunk.chunk_id not in expanded:
                next_chars = total_chars + len(chunk.text or "")
                if cfg.max_pdf_context_chars > 0 and next_chars > cfg.max_pdf_context_chars:
                    truncated = True
                    return False
                expanded[chunk.chunk_id] = chunk
                per_doc_counts[doc_key] = per_doc_counts.get(doc_key, 0) + 1
                total_chars = next_chars
            reasons.setdefault(chunk.chunk_id, [])
            if reason not in reasons[chunk.chunk_id]:
                reasons[chunk.chunk_id].append(reason)
            return True

        for anchor in anchors:
            indexed_anchor = self.by_chunk_id.get(anchor.chunk_id, anchor)
            add(indexed_anchor, "selected_anchor")
            neighbor_count = 0
            for candidate, reason in self._expansion_candidates(indexed_anchor, cfg):
                if candidate.chunk_id in selected_ids:
                    reason = f"{reason}; retrieval_candidate"
                if add(candidate, reason):
                    neighbor_count += 1
                if neighbor_count >= cfg.max_neighbors_per_anchor:
                    break

        ordered = tuple(sorted(expanded.values(), key=_chunk_order))
        return CorpusExpansionResult(
            chunks=ordered,
            diagnostics={
                "index_chunk_count": len(self.chunks),
                "selected_anchor_chunk_ids": [chunk.chunk_id for chunk in anchors],
                "expanded_chunk_ids": [chunk.chunk_id for chunk in ordered],
                "expansion_reasons": reasons,
                "config": cfg.__dict__,
                "truncated": truncated,
                "total_characters": sum(len(chunk.text or "") for chunk in ordered),
            },
        )

    def with_document_identity(self, chunk: Chunk) -> Chunk:
        indexed = self.by_chunk_id.get(chunk.chunk_id)
        document_models = (
            indexed.document_model_numbers
            if indexed is not None
            else self.document_model_numbers.get(_document_key(chunk), ())
        )
        key = _document_key(chunk)
        aliases = (
            indexed.catalog_path_aliases
            if indexed is not None
            else self.document_catalog_path_aliases.get(key, ())
        )
        configurations = (
            indexed.document_configurations
            if indexed is not None
            else self.document_configurations.get(key, ())
        )
        exclusions = (
            indexed.document_configuration_exclusions
            if indexed is not None
            else self.document_configuration_exclusions.get(key, ())
        )
        coverage_complete = (
            indexed.document_configuration_coverage_complete
            if indexed is not None
            else self.document_configuration_coverage_complete.get(
                key,
                False,
            )
        )
        taxonomy_validated = (
            indexed.corpus_taxonomy_validated
            if indexed is not None
            else self.document_corpus_taxonomy_validated.get(
                key,
                False,
            )
        )
        if (
            chunk.document_model_numbers == document_models
            and chunk.catalog_path_aliases == aliases
            and chunk.document_configurations == configurations
            and chunk.document_configuration_exclusions == exclusions
            and (
                chunk.document_configuration_coverage_complete
                == coverage_complete
            )
            and chunk.corpus_taxonomy_validated == taxonomy_validated
        ):
            return chunk
        return replace(
            chunk,
            document_model_numbers=document_models,
            catalog_path_aliases=aliases,
            document_configurations=configurations,
            document_configuration_exclusions=exclusions,
            document_configuration_coverage_complete=coverage_complete,
            corpus_taxonomy_validated=taxonomy_validated,
        )

    def _expansion_candidates(
        self,
        anchor: Chunk,
        cfg: CorpusExpansionConfig,
    ) -> tuple[tuple[Chunk, str], ...]:
        key = _document_key(anchor)
        candidates: list[tuple[Chunk, str]] = []
        for offset, reason in ((-1, "previous_chunk"), (1, "next_chunk")):
            found = self.by_document_index.get((key, anchor.chunk_index + offset))
            if found:
                candidates.append((found, reason))
        for page in range(anchor.page_start - cfg.max_page_distance, anchor.page_end + cfg.max_page_distance + 1):
            for chunk in self.by_document_page.get((key, page), ()):
                if chunk.chunk_id == anchor.chunk_id:
                    continue
                reason = _context_reason(anchor, chunk)
                if reason:
                    candidates.append((chunk, reason))
        return tuple(_dedupe_candidates(candidates))


def _context_reason(anchor: Chunk, chunk: Chunk) -> str | None:
    lower = f"{anchor.text}\n{chunk.text}".casefold()
    if chunk.has_warning or "warning" in chunk.text.casefold():
        return "nearby_warning"
    if chunk.has_caution or "caution" in chunk.text.casefold():
        return "nearby_caution"
    if chunk.has_table or _looks_like_table_header(chunk.text):
        return "table_context"
    if _looks_like_heading(chunk):
        return "same_page_heading"
    if chunk.has_figure_reference or re.search(r"\b(?:see|refer to)\s+figure\b", chunk.text, re.I):
        return "figure_reference_context"
    if "continued" in lower or "shown below" in lower or "shown above" in lower:
        return "page_continuation"
    if anchor.section_path and chunk.section_path == anchor.section_path:
        return "same_section_context"
    return None


def _looks_like_heading(chunk: Chunk) -> bool:
    text = re.sub(r"\s+", " ", chunk.text or "").strip()
    if not text or len(text) > 120:
        return False
    letters = [char for char in text if char.isalpha()]
    return bool(letters) and sum(1 for char in letters if char.isupper()) / len(letters) > 0.65


def _looks_like_table_header(text: str) -> bool:
    return bool(re.search(r"\b(?:table|chart|dimensions?|clearances?|units?|notes?)\b", text, re.I))


def _first_documents(chunks: tuple[Chunk, ...], limit: int) -> tuple[str, ...]:
    seen = set()
    result = []
    for chunk in chunks:
        key = _document_key(chunk)
        if key in seen:
            continue
        seen.add(key)
        result.append(key)
        if len(result) >= limit:
            break
    return tuple(result)


def _dedupe_candidates(candidates: list[tuple[Chunk, str]]) -> list[tuple[Chunk, str]]:
    seen = set()
    result = []
    for chunk, reason in sorted(candidates, key=lambda item: _chunk_order(item[0])):
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        result.append((chunk, reason))
    return result


def _document_key(chunk: Chunk) -> str:
    return chunk.document_id or chunk.relative_path or chunk.filename or "unknown"


def _chunk_order(chunk: Chunk) -> tuple[str, int, int, str]:
    return (_document_key(chunk), chunk.page_start, chunk.chunk_index, chunk.chunk_id)
