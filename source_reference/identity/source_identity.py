from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import json
from pathlib import Path
from typing import Any, Iterable

from src.models import Chunk
from src.product_taxonomy import DEFAULT_PRODUCT_TAXONOMY


SOURCE_IDENTITY_APPROVED = "SOURCE_IDENTITY_APPROVED"
SOURCE_IDENTITY_UNKNOWN = "SOURCE_IDENTITY_UNKNOWN"


@dataclass(frozen=True)
class ApprovedSource:
    relative_path: str
    document_id: str | None = None


@dataclass(frozen=True)
class SourceResolution:
    canonical_path: str | None
    document_id: str | None
    source_namespace: str | None
    status: str
    method: str | None = None


class ApprovedSourceRegistry:
    """Manifest-backed source resolver with explicit namespace aliases."""

    def __init__(
        self,
        sources: Iterable[ApprovedSource | dict[str, Any]] = (),
        *,
        namespace_aliases: Iterable[str] = (),
    ) -> None:
        by_path: dict[str, ApprovedSource] = {}
        by_document_id: dict[str, ApprovedSource] = {}
        for source in sources:
            if isinstance(source, dict):
                if source.get("approved") is False:
                    continue
                relative_path = _clean(source.get("relative_path"))
                document_id = _clean(source.get("document_id"))
                item = ApprovedSource(relative_path or "", document_id)
            else:
                item = source
            path = _normalize_path(item.relative_path)
            if not path:
                continue
            normalized = ApprovedSource(path, _clean(item.document_id))
            by_path[path] = normalized
            if normalized.document_id:
                by_document_id[normalized.document_id] = normalized
        self._by_path = by_path
        self._by_document_id = by_document_id
        self._namespace_aliases = frozenset(
            _normalize_path(value)
            for value in namespace_aliases
            if _normalize_path(value)
        )

    @property
    def approved_paths(self) -> tuple[str, ...]:
        return tuple(sorted(self._by_path))

    def resolve(
        self,
        value: str | None,
        *,
        document_id: str | None = None,
    ) -> SourceResolution:
        path = _normalize_path(value)
        cleaned_document_id = _clean(document_id)
        if cleaned_document_id and cleaned_document_id in self._by_document_id:
            source = self._by_document_id[cleaned_document_id]
            return SourceResolution(
                canonical_path=source.relative_path,
                document_id=source.document_id,
                source_namespace=_namespace_from_path(source.relative_path),
                status=SOURCE_IDENTITY_APPROVED,
                method="approved_manifest_document_id",
            )
        if path in self._by_path:
            source = self._by_path[path]
            return SourceResolution(
                canonical_path=source.relative_path,
                document_id=source.document_id or cleaned_document_id,
                source_namespace=_namespace_from_path(source.relative_path),
                status=SOURCE_IDENTITY_APPROVED,
                method="approved_manifest_path",
            )
        root, separator, remainder = path.partition("/")
        if separator and root in self._namespace_aliases and remainder in self._by_path:
            source = self._by_path[remainder]
            return SourceResolution(
                canonical_path=source.relative_path,
                document_id=source.document_id or cleaned_document_id,
                source_namespace=_namespace_from_path(source.relative_path),
                status=SOURCE_IDENTITY_APPROVED,
                method="approved_namespace_alias",
            )
        return SourceResolution(
            canonical_path=path or None,
            document_id=cleaned_document_id,
            source_namespace=_namespace_from_path(path),
            status=SOURCE_IDENTITY_UNKNOWN,
            method=None,
        )


@dataclass(frozen=True)
class SourceIdentity:
    document_id: str | None = None
    source_namespace: str | None = None
    canonical_path: str | None = None
    filename: str | None = None
    page_start: int | None = None
    page_end: int | None = None
    resolution_status: str = SOURCE_IDENTITY_UNKNOWN
    resolution_method: str | None = None


@dataclass(frozen=True)
class SourceMatch:
    matched: bool
    method: str | None = None
    accepted_note: str | None = None
    reason_codes: tuple[str, ...] = ()


@lru_cache(maxsize=1)
def default_source_registry() -> ApprovedSourceRegistry:
    project_root = Path(__file__).resolve().parents[1]
    approved_path = project_root / "data" / "approved_pdfs.jsonl"
    manifest_path = project_root / "data" / "manifest.json"
    rows: list[dict[str, Any]] = []
    if approved_path.exists():
        for line in approved_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                rows.append(json.loads(line))
    elif manifest_path.exists():
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        rows.extend(payload.get("documents") or ())
    return ApprovedSourceRegistry(
        rows,
        namespace_aliases=DEFAULT_PRODUCT_TAXONOMY.corpus_namespaces,
    )


def identity_from_chunk(
    chunk: Chunk,
    *,
    registry: ApprovedSourceRegistry | None = None,
) -> SourceIdentity:
    return _identity(
        chunk.relative_path or chunk.source_path or chunk.filename,
        document_id=chunk.document_id,
        filename=chunk.filename,
        page_start=chunk.page_start,
        page_end=chunk.page_end,
        registry=registry,
    )


def identity_from_source(
    source: str | dict[str, Any] | SourceIdentity | None,
    *,
    registry: ApprovedSourceRegistry | None = None,
) -> SourceIdentity:
    if isinstance(source, SourceIdentity):
        return source
    if isinstance(source, dict):
        path = _clean(source.get("relative_path")) or _clean(source.get("filename"))
        return _identity(
            path,
            document_id=_clean(source.get("document_id")),
            filename=_clean(source.get("filename")),
            page_start=_optional_int(
                source.get("page_start")
                if source.get("page_start") is not None
                else source.get("page")
            ),
            page_end=_optional_int(
                source.get("page_end")
                if source.get("page_end") is not None
                else source.get("page_start")
            ),
            registry=registry,
        )
    text = _clean(source)
    return _identity(
        text,
        filename=text.rsplit("/", 1)[-1] if text else None,
        registry=registry,
    )


def canonical_corpus_path(
    value: str | None,
    *,
    registry: ApprovedSourceRegistry | None = None,
) -> str | None:
    return (registry or default_source_registry()).resolve(value).canonical_path


def sources_match(
    expected: str | dict[str, Any] | SourceIdentity | None,
    actual: str | dict[str, Any] | SourceIdentity | None,
    *,
    accepted_sources: tuple[str, ...] = (),
    registry: ApprovedSourceRegistry | None = None,
) -> SourceMatch:
    active_registry = registry or default_source_registry()
    expected_identity = identity_from_source(expected, registry=active_registry)
    actual_identity = identity_from_source(actual, registry=active_registry)
    direct = _single_source_match(expected_identity, actual_identity)
    if direct.matched:
        return direct
    for accepted in accepted_sources:
        accepted_identity = identity_from_source(accepted, registry=active_registry)
        accepted_match = _single_source_match(accepted_identity, actual_identity)
        if accepted_match.matched:
            return SourceMatch(
                True,
                f"accepted_source:{accepted_match.method}",
                reason_codes=accepted_match.reason_codes,
            )
    return SourceMatch(
        False,
        reason_codes=tuple(
            dict.fromkeys(
                status
                for status in (
                    expected_identity.resolution_status,
                    actual_identity.resolution_status,
                )
                if status == SOURCE_IDENTITY_UNKNOWN
            )
        ),
    )


def page_matches(
    expected_page: int,
    actual: SourceIdentity,
    *,
    accepted_pages: tuple[int, ...] = (),
) -> bool:
    pages = {expected_page, *accepted_pages}
    if actual.page_start is None:
        return False
    page_end = actual.page_end if actual.page_end is not None else actual.page_start
    return any(actual.page_start <= page <= page_end for page in pages)


def _identity(
    path: str | None,
    *,
    document_id: str | None = None,
    filename: str | None = None,
    page_start: int | None = None,
    page_end: int | None = None,
    registry: ApprovedSourceRegistry | None = None,
) -> SourceIdentity:
    resolution = (registry or default_source_registry()).resolve(
        path,
        document_id=document_id,
    )
    return SourceIdentity(
        document_id=resolution.document_id or document_id,
        source_namespace=resolution.source_namespace,
        canonical_path=resolution.canonical_path,
        filename=filename,
        page_start=page_start,
        page_end=page_end,
        resolution_status=resolution.status,
        resolution_method=resolution.method,
    )


def _single_source_match(expected: SourceIdentity, actual: SourceIdentity) -> SourceMatch:
    reason_codes = tuple(
        dict.fromkeys(
            status
            for status in (
                expected.resolution_status,
                actual.resolution_status,
            )
            if status == SOURCE_IDENTITY_UNKNOWN
        )
    )
    if expected.document_id and actual.document_id and expected.document_id == actual.document_id:
        return SourceMatch(True, "document_id", reason_codes=reason_codes)
    if (
        expected.canonical_path
        and actual.canonical_path
        and expected.canonical_path == actual.canonical_path
    ):
        method = (
            "canonical_path"
            if not reason_codes
            else "canonical_path_unresolved"
        )
        return SourceMatch(True, method, reason_codes=reason_codes)
    return SourceMatch(False, reason_codes=reason_codes)


def _namespace_from_path(value: str | None) -> str | None:
    text = _normalize_path(value)
    return text.split("/", 1)[0] if text else None


def _normalize_path(value: str | None) -> str:
    text = str(value or "").replace("\\", "/").casefold().strip()
    while "//" in text:
        text = text.replace("//", "/")
    return text.strip("/")


def _clean(value: Any) -> str | None:
    if value in (None, ""):
        return None
    return str(value).strip()


def _optional_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
