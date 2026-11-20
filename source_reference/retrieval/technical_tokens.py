import re
from collections.abc import Mapping
from typing import Any

from src.query_identity import normalize_identifier, parse_query_identity

MODEL_TOKEN_PATTERN = (
    r"(?<![A-Z0-9])(?:"
    # Match the complete segmented form before any compact/prefix form so a
    # configuration suffix remains part of the literal identifier.
    r"[A-Z0-9]{1,12}(?:[._/-][A-Z0-9]{1,12}){1,4}"
    r"|\d{2,8}(?: [A-Z0-9]{1,8}){1,3}"
    r"|(?=[A-Z0-9]{4,18}(?![A-Z0-9]))"
    r"(?=[A-Z0-9]*[A-Z])(?=[A-Z0-9]*\d)[A-Z0-9]{4,18}"
    r")(?![A-Z0-9])"
)
MEASUREMENT_TOKEN_PATTERN = (
    r"(?<![A-Z0-9])(?:"
    r"\d+(?:\.\d+)?\s*(?:V(?:AC|DC)?|A(?:MP(?:S)?)?|HZ)"
    r"|(?:\d+-)?\d+\s*/\s*\d+\s*(?:IN\.?|\")?"
    r"|\d+(?:\.\d+)?\s*(?:IN\.?|MM|CM)"
    r")(?![A-Z0-9])"
)
TECHNICAL_TOKEN_PATTERN = re.compile(
    rf"(?:{MEASUREMENT_TOKEN_PATTERN}|{MODEL_TOKEN_PATTERN})",
    re.I,
)
MEASUREMENT_TOKEN_FULLMATCH = re.compile(MEASUREMENT_TOKEN_PATTERN, re.I)
FALSE_POSITIVE_TOKEN_WORDS = {
    "AMERICAN", "CALL", "FAX", "FEET", "IN", "INCH", "INCHES", "LIMITED",
    "ONLINE", "PRODUCT", "WARRANTY",
}
TOKEN_CONTEXT_PREFIX = re.compile(
    r"^(?:and|items?|kits?|models?|numbers?|parts?|tables?)\s+(?=\d)", re.I
)
TRAILING_CONTEXT_WORD = re.compile(
    r"(?:\s+(?:and|apply|for|from|in|kit|on|to|use|uses|with))+$", re.I
)
QUESTION_STOPWORDS = {
    "a", "about", "an", "and", "are", "between", "brand", "brands", "but",
    "catalog", "can", "compare", "difference", "differences", "do", "does",
    "for", "give", "how", "is", "it", "me", "model", "models", "of", "ok",
    "our", "product", "products", "series", "size", "sizes", "tell", "the",
    "this", "what", "whats", "with",
}
WEAK_QUERY_TERMS = {"brand", "brands", "catalog", "model"}


def normalize_technical_token(value: str) -> str:
    return normalize_identifier(value)


def _is_false_positive(token: str, normalized: str) -> bool:
    if MEASUREMENT_TOKEN_FULLMATCH.fullmatch(token):
        return False
    if "/" in token and any(char.isalpha() for char in token) and any(
        char.isdigit() for char in token
    ):
        return False
    words = set(re.findall(r"[A-Z]+", token.upper()))
    phone = bool(re.fullmatch(r"\d{3}[- ]\d{3}[- ]\d{4}", token))
    zip_code = bool(re.fullmatch(r"\d{5}(?:-\d{4})?", token))
    year = bool(re.fullmatch(r"(?:19|20)\d{2}", token))
    return (
        len(normalized) < 4
        or len(normalized) > 18
        or not any(char.isdigit() for char in normalized)
        or token.count(" ") > 2
        or bool(words & FALSE_POSITIVE_TOKEN_WORDS)
        or phone
        or zip_code
        or year
    )


def extract_technical_tokens(text: str) -> list[str]:
    tokens: list[str] = []
    seen: set[str] = set()
    for match in TECHNICAL_TOKEN_PATTERN.finditer(text or ""):
        token = " ".join(match.group(0).strip().split())
        if not MEASUREMENT_TOKEN_FULLMATCH.fullmatch(token):
            token = TOKEN_CONTEXT_PREFIX.sub("", token)
            token = TRAILING_CONTEXT_WORD.sub("", token)
        normalized = normalize_technical_token(token)
        if token not in seen and not _is_false_positive(token, normalized):
            tokens.append(token)
            seen.add(token)
    return tokens


def extract_query_tokens(question: str) -> list[str]:
    return [identifier.normalized for identifier in parse_query_identity(question).identifiers]


def extract_query_terms(question: str) -> list[str]:
    terms: list[str] = []
    seen: set[str] = set()
    lower = question.lower()
    for term in re.findall(r"[a-z0-9][a-z0-9\-]{2,}", lower):
        cleaned = term.strip("-")
        if (
            cleaned not in QUESTION_STOPWORDS
            and cleaned not in WEAK_QUERY_TERMS
            and cleaned not in seen
        ):
            terms.append(cleaned)
            seen.add(cleaned)
    for size in re.findall(r"\b(\d{2,4})\s*(?:inch|inches|in\.|\")\b", lower):
        if not re.fullmatch(r"(?:19|20)\d{2}", size) and size not in seen:
            terms.append(size)
            seen.add(size)
    _add_query_aliases(terms, seen)
    if {"accessory", "accessories", "griddle"} & set(terms):
        terms[:] = [term for term in terms if term not in {"grill", "grills"}]
        seen.difference_update({"grill", "grills"})
    return terms


def _add_query_aliases(terms: list[str], seen: set[str]) -> None:
    source = set(terms)

    def add(*aliases: str) -> None:
        for alias in aliases:
            if alias not in seen:
                terms.append(alias)
                seen.add(alias)

    if "grids" in source:
        add("grid")
    if "grid" in source:
        add("grids")
    if "flavor" in source and {"grid", "grids"} & source:
        add("vaporizer", "panel", "panels")
    if "igniter" in source:
        add("electrode", "ignition", "assembly")
    if "electrode" in source:
        add("igniter")
    if "cfm" in source:
        add("airflow", "rating")
    if "airflow" in source:
        add("cfm", "rating")
    if "cutout" in source:
        add("cut-out")
    if "cut-out" in source:
        add("cutout")
    if "fits" in source:
        add("fit", "compatible")
    if "fit" in source:
        add("fits", "compatible")


def score_keyword_match(
    text: str,
    metadata: Mapping[str, Any] | None,
    question_terms: list[str],
    query_tokens: list[str],
) -> int:
    payload = metadata or {}
    fields = (
        "filename", "relative_path", "manufacturer", "brand", "series",
        "product", "content_type", "technical_tokens_normalized",
        "model_numbers", "part_numbers",
    )
    searchable = " ".join(
        [text or "", *(str(payload.get(field, "")) for field in fields)]
    )
    normalized = normalize_technical_token(searchable)
    token_score = sum(8 for token in query_tokens if token in normalized)
    term_score = sum(
        1
        for term in question_terms
        if normalize_technical_token(term) in normalized
    )
    return token_score + term_score
