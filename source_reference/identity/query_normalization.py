from __future__ import annotations

from dataclasses import dataclass
import re
import unicodedata


_SPACE_BEFORE_PUNCTUATION = re.compile(r"\s+([?.!,;:])")


@dataclass(frozen=True)
class NormalizedQuestion:
    original_question: str
    canonical_question: str
    normalization_changed_input: bool


def normalize_question(raw_question: str | None) -> NormalizedQuestion:
    original = raw_question or ""
    collapsed = " ".join(unicodedata.normalize("NFKC", original).split())
    punctuation_normalized = _SPACE_BEFORE_PUNCTUATION.sub(r"\1", collapsed)
    canonical = punctuation_normalized.casefold()
    return NormalizedQuestion(
        original_question=original,
        canonical_question=canonical,
        normalization_changed_input=canonical != original,
    )
