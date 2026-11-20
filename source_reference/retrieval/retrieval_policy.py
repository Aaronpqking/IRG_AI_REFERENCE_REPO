import re
from collections.abc import Iterable

from src.models import Chunk
from src.technical_tokens import (
    extract_technical_tokens,
    normalize_technical_token,
)


_QUERY_INSTALL_TERMS = {
    "install", "installation", "mount", "mounting", "warning", "caution",
    "connect", "connection", "wiring", "wire", "clearance",
}
_QUERY_PART_TERMS = {
    "part", "parts", "replacement", "sku", "kit", "item", "accessory",
    "accessories",
}
_QUERY_DIMENSION_TERMS = {
    "dimension", "dimensions", "spec", "specs", "specification",
    "specifications", "cutout", "width", "height", "depth", "measurement",
    "measurements", "size", "sizes", "cut-out", "cfm", "airflow", "rating",
}
_QUERY_COMPATIBILITY_TERMS = {
    "fit", "fits", "fitment", "compatible", "compatibility", "works",
}
_QUERY_COVER_TERMS = {"cover", "covers"}
_CATALOG_TERMS = {"catalog", "current", "latest", "newest"}
_SOURCE_STOP_TERMS = {
    "and", "are", "brand", "brands", "document", "file", "for", "from",
    "general", "guide", "manual", "model", "models", "page", "pdf",
    "product", "products", "series", "source", "the", "this", "with",
}


def chunk_year(chunk: Chunk) -> int | None:
    value = str(chunk.year or "")
    if not re.fullmatch(r"(?:19|20)\d{2}", value):
        match = re.search(r"/((?:19|20)\d{2})/", chunk.relative_path or "")
        value = match.group(1) if match else ""
    return int(value) if value else None


def year_score(
    chunk: Chunk,
    query_year: int | None,
    strong_match: bool,
    prefer_latest: bool = False,
) -> float:
    year = chunk_year(chunk)
    if year is None:
        return 0.0
    if query_year is not None:
        return 2.0 if year == query_year else -8.0
    if not strong_match:
        return 0.0
    weight = 0.12 if prefer_latest else 0.08
    cap = 3.5 if prefer_latest else 2.5
    return min(cap, max(0.0, (year - 2000) * weight))


def infer_document_type(chunk: Chunk) -> str:
    source = _source_text(chunk).casefold()
    path = (chunk.relative_path or "").replace("\\", "/").casefold()
    content_type = (chunk.content_type or "").casefold()
    chunk_kind = (chunk.chunk_kind or "").casefold()
    if "catalog" in source:
        return "catalog"
    if re.search(r"(?:^|[/_\-\s])qsg(?:$|[/_\-\s])", path) or "quick start" in source:
        return "quick_start"
    if re.search(r"(?:^|/)spec(?:ification)?(?:/|$)", path):
        return "specification"
    if re.search(r"(?:^|/)om(?:/|$)", path):
        return "owner_manual"
    if "spec" in source or content_type == "spec_table" or chunk.has_dimensions:
        return "specification"
    if (
        re.search(r"(?:^|[/_\-\s])om(?:$|[/_\-\s])", path)
        or "owner" in source
        or "manual" in source
    ):
        return "owner_manual"
    if content_type == "part_table" or chunk.has_parts_list:
        return "parts"
    return "unknown"


def path_quality_score(
    chunk: Chunk,
    query_tokens: list[str],
    prefer_catalog: bool,
    question_terms: list[str] | None = None,
    query_year: int | None = None,
) -> float:
    terms = question_terms or []
    filename = (chunk.filename or "").rsplit(".", 1)[0]
    path = (chunk.relative_path or "").replace("\\", "/").casefold()
    product_tokens = {
        normalize_technical_token(item)
        for item in extract_technical_tokens(str(chunk.product or ""))
    }
    filename_tokens = {
        normalize_technical_token(item)
        for item in extract_technical_tokens(filename)
    }
    anomaly = (
        product_tokens
        and filename_tokens
        and product_tokens.isdisjoint(filename_tokens)
    )
    if anomaly:
        return -2.0
    score = 0.0
    document_type = infer_document_type(chunk)
    if prefer_catalog:
        score += 5.0 if document_type == "catalog" else -0.5
    else:
        score += _document_type_score(document_type, terms)
    normalized_path = normalize_technical_token(path)
    if query_tokens and any(token in normalized_path for token in query_tokens):
        score += 3.0 if "/om/" in path else 2.0
    elif prefer_catalog and document_type == "catalog" and _tokens_in_source_text(chunk, query_tokens):
        score += 12.0
    elif document_type == "catalog" and query_tokens:
        score -= 1.0
    score += scope_consistency_score(
        chunk,
        query_tokens=query_tokens,
        question_terms=terms,
        query_year=query_year,
    )
    return score


def scope_consistency_score(
    chunk: Chunk,
    query_tokens: list[str],
    question_terms: list[str],
    query_year: int | None = None,
) -> float:
    source = _source_text(chunk)
    source_identity = _source_identity_text(chunk)
    normalized_source = normalize_technical_token(source)
    normalized_identity = normalize_technical_token(source_identity)
    score = 0.0

    if query_tokens:
        identity_matches = [
            token for token in query_tokens if token and token in normalized_identity
        ]
        source_matches = [
            token for token in query_tokens if token and token in normalized_source
        ]
        if identity_matches:
            score += 5.0 + (2.0 * len(identity_matches))
        elif source_matches:
            score += 0.0
        else:
            score -= 7.0

    source_terms = _scope_terms(source_identity)
    overlap = [term for term in question_terms if term in source_terms]
    score += min(4.0, len(overlap) * 0.8)

    query_numbers = _scope_numbers(" ".join(question_terms))
    if query_year is not None:
        query_numbers.discard(str(query_year))
    identity_numbers = _scope_numbers(source_identity)
    if query_numbers:
        number_overlap = query_numbers & identity_numbers
        score += 2.0 * len(number_overlap)
        if not number_overlap and identity_numbers:
            score -= 2.0

    return score


def _document_type_score(document_type: str, question_terms: list[str]) -> float:
    terms = set(question_terms)
    if terms & _CATALOG_TERMS:
        return 4.0 if document_type == "catalog" else 0.0
    if terms & _QUERY_COVER_TERMS and terms & _QUERY_COMPATIBILITY_TERMS:
        if document_type == "catalog":
            return 4.5
        if document_type in {"specification", "quick_start"}:
            return -2.0
        if document_type == "owner_manual":
            return 0.25
    if terms & _QUERY_INSTALL_TERMS:
        if document_type == "owner_manual":
            return 3.0
        if document_type in {"quick_start", "catalog"}:
            return -2.0
        if document_type == "specification":
            return -1.0
    if terms & _QUERY_PART_TERMS:
        if document_type in {"owner_manual", "parts"}:
            return 3.0
        if document_type == "catalog":
            return -1.0
    if terms & _QUERY_DIMENSION_TERMS:
        explicit_spec = bool(terms & {"spec", "specs", "specification", "specifications"})
        if document_type == "specification":
            return 2.0 if explicit_spec else 1.0
        if document_type == "owner_manual":
            return 2.0 if not explicit_spec else 1.0
        if document_type == "catalog":
            return -0.5
    if document_type == "owner_manual":
        return 0.75
    if document_type == "catalog":
        return -0.75
    return 0.0


def _source_text(chunk: Chunk) -> str:
    return " ".join(_source_values(chunk, include_text=True))


def _source_identity_text(chunk: Chunk) -> str:
    return " ".join(_source_values(chunk, include_text=False))


def _source_values(chunk: Chunk, include_text: bool) -> Iterable[str]:
    values: list[str] = [
        chunk.filename or "",
        chunk.relative_path or "",
        chunk.manufacturer or "",
        chunk.brand or "",
        chunk.series or "",
        chunk.product or "",
        chunk.content_type or "",
        chunk.chunk_kind or "",
        chunk.section_title or "",
        chunk.section_path or "",
        " ".join(chunk.technical_tokens_normalized or ()),
        " ".join(chunk.model_numbers or ()),
        " ".join(chunk.part_numbers or ()),
    ]
    if include_text:
        values.append((chunk.text or "")[:2000])
    return (value for value in values if value)


def _tokens_in_source_text(chunk: Chunk, query_tokens: list[str]) -> bool:
    if not query_tokens:
        return False
    normalized = normalize_technical_token((chunk.text or "")[:2000])
    return any(token and token in normalized for token in query_tokens)


def _scope_terms(text: str) -> set[str]:
    found: set[str] = set()
    for term in re.findall(r"[a-z0-9][a-z0-9\-_]{2,}", text.casefold()):
        cleaned = term.strip("-_")
        if cleaned and cleaned not in _SOURCE_STOP_TERMS:
            found.add(cleaned)
            normalized = re.sub(r"[-_]+", "", cleaned)
            if normalized:
                found.add(normalized)
    return found


def _scope_numbers(text: str) -> set[str]:
    return {
        value
        for value in re.findall(r"(?<!\d)\d{2,4}(?!\d)", text)
        if not re.fullmatch(r"(?:19|20)\d{2}", value)
    }
