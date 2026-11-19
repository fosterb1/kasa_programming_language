"""Experimental, opt-in beginner diagnostic notes for Kasa's Python playground.

The Twi labels are editorial *drafts*, not linguistically approved translations.
Keep original Kasa error category, message and source coordinates unchanged.
No evaluation, network access, dynamically loaded text or source rewriting.
"""
from __future__ import annotations

from .core import KasaError

# Wording must be reviewed with Asante and Akuapem speakers and educators.
# Labels use Kasa's existing Twi vocabulary where possible; English guidance
# describes the underlying computing problem without pretending translation.
_LESSONS = {
    "NameError": ("edin", "Check the name's spelling. Declare a value with 'ma' before using it."),
    "SyntaxError": ("nhyehyɛe", "Check the line structure, brackets, and required 'awiei' block endings."),
    "TypeError": ("nɔma / nsɛm", "Check whether the operation expects a number, text, list, or Boolean."),
    "ZeroDivisionError": ("akyɛmu", "A number cannot be divided by zero. Check the divisor first."),
    "IndexError": ("dinom", "Check the list index: indexes begin at zero and must stay within the list."),
    "ResourceError": ("anohyeto", "The program reached a safety limit. Check for an endless loop or oversized value."),
    "InputError": ("bisa", "Provide a line of input when the program calls 'bisa()'."),
}


def learning_hint(error: KasaError, *, language: str = "tw") -> dict[str, str] | None:
    """Return a draft teaching card; never replace the underlying diagnostic.

    Only the exact KasaError category is considered, not untrusted substrings
    in the error message. Unknown types are left unchanged.
    """
    if language != "tw":
        return None
    lesson = _LESSONS.get(error.category)
    if lesson is None:
        return None
    label, guidance = lesson
    return {
        "status": "draft_needs_human_review",
        "language": "tw",
        "concept_label": label,
        "technical_code": error.category,
        "guidance_en": guidance,
    }
