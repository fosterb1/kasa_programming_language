"""Offline vocabulary approval guard for Kasa's Twi language surface.

This file checks documentation and reviewer metadata, NOT linguistic correctness.
Existing vocabulary predates this policy and remains review-pending.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

from kasa.core import BUILTIN_NAMES, KEYWORDS

ROOT = Path(__file__).resolve().parents[1]
REGISTER = ROOT / "docs" / "keyword_evidence.json"

# Frozen baseline checked into the test itself. Do not regenerate from the register.
# Introducing new tokens requires the approval criteria below, not adding to this list.
LEGACY_KEYWORDS = {
    "ka", "ma", "sɛ", "anyɛ_saa_a", "mpɛn", "bere_a", "dwumadie",
    "sanma", "awiei", "nokware", "atoro", "hwee", "ne", "anaa",
    "ɛnyɛ", "gyae", "toa_so",
}
LEGACY_BUILTINS = {"bisa", "tentɛn", "nɔma", "nsɛm"}
LEGACY_PARTICLES = {"a"}

VALID_STATUSES = {
    "legacy_review_pending", "proposed", "needs_review",
    "accepted", "rejected", "deprecated",
}


def get_manifest() -> dict:
    return json.loads(REGISTER.read_text(encoding="utf-8"))


def test_baseline_is_not_silently_redefined() -> None:
    data = get_manifest()["frozen_legacy_baseline"]
    assert set(data["keywords"]) == LEGACY_KEYWORDS
    assert set(data["builtins"]) == LEGACY_BUILTINS
    assert set(data["contextual_particles"]) == LEGACY_PARTICLES


def test_every_implemented_python_token_has_a_research_record() -> None:
    data = get_manifest()
    entries = data["terms"]
    active = {
        *(f"keyword:{word}" for word in KEYWORDS),
        *(f"builtin:{word}" for word in BUILTIN_NAMES),
        *(f"contextual_particle:{word}" for word in LEGACY_PARTICLES),
    }
    assert active <= entries.keys(), f"Undocumented syntax: {sorted(active - entries.keys())}"

    for name in active:
        entry = entries[name]
        category, token = name.split(":", 1)
        assert entry["token"] == token
        assert entry["kind"] == category
        assert entry["status"] in VALID_STATUSES
        assert entry["role"].strip()
        assert entry["linguistic_note"].strip()
        assert isinstance(entry["reference_ids"], list)
        for ref in entry["reference_ids"]:
            source = data["source_index"][ref]
            assert source["url"].startswith("https://")
            assert source["title"].strip()
            assert source["publisher"].strip()
            assert source["accessed"].strip()


def test_new_tokens_require_evidence_and_human_approval() -> None:
    data = get_manifest()
    old = {
        *(f"keyword:{word}" for word in LEGACY_KEYWORDS),
        *(f"builtin:{word}" for word in LEGACY_BUILTINS),
        *(f"contextual_particle:{word}" for word in LEGACY_PARTICLES),
    }
    active = {
        *(f"keyword:{word}" for word in KEYWORDS),
        *(f"builtin:{word}" for word in BUILTIN_NAMES),
        *(f"contextual_particle:{word}" for word in LEGACY_PARTICLES),
    }
    for name in sorted(active - old):
        entry = data["terms"][name]
        assert entry["status"] == "accepted", f"{name} has not been approved"

        refs = [data["source_index"][sid] for sid in entry["reference_ids"]]
        assert len(refs) >= 2, f"{name}: requires two independent references"
        assert len({source["publisher"] for source in refs}) >= 2, (
            f"{name}: the sources must have different publishers"
        )
        assert any(
            source["kind"] in {"academic", "official", "lexicographic", "grammar", "pedagogy"}
            for source in refs
        ), f"{name}: needs a substantive educational/linguistic reference"

        decision = entry["decision"]
        assert isinstance(decision, dict)
        assert decision.get("accepted_at")
        assert decision.get("rationale", "").strip()
        reviewers = entry["reviewers"]
        assert isinstance(reviewers, list) and len(reviewers) >= 3
        assert all(
            reviewer.get("reviewer_id")
            and reviewer.get("reviewed_at")
            and reviewer.get("role")
            for reviewer in reviewers
        )
        fluent = {
            reviewer.get("dialect")
            for reviewer in reviewers
            if reviewer.get("role") == "fluent_speaker"
        }
        assert {"Asante", "Akuapem"} <= fluent, (
            f"{name}: requires review from Asante and Akuapem speakers"
        )
        assert any(reviewer.get("role") == "computing_educator" for reviewer in reviewers)


def test_all_three_runtimes_agree_on_documented_keywords() -> None:
    """Catch JS/C++-only keyword additions that bypass Python's audit list."""
    js = (ROOT / "playground" / "kasa-runtime.js").read_text(encoding="utf-8")
    cpp = (ROOT / "native" / "src" / "lexer.cpp").read_text(encoding="utf-8")
    vm = (ROOT / "native" / "src" / "vm.cpp").read_text(encoding="utf-8")

    js_block = re.search(r"const KEYWORDS = Object\.freeze\(\{(.*?)\}\);", js, re.S)
    native_block = re.search(
        r"static const unordered_map<string,string> words=\{(.*?)\};", cpp, re.S
    )
    assert js_block, "Cannot inspect JS keyword registry"
    assert native_block, "Cannot inspect native keyword registry"

    js_keys = {
        quoted or identifier
        for quoted, identifier in re.findall(
            r'(?:"([^"]+)"|([\w]+))\s*:\s*"[A-Z_]+"', js_block.group(1)
        )
    }
    native_keys = set(
        re.findall(r'\{\s*"([^"]+)"\s*,\s*"[A-Z_]+"\s*\}', native_block.group(1))
    )
    assert js_keys == set(KEYWORDS), f"JavaScript lexer keywords differ: {js_keys ^ set(KEYWORDS)}"
    assert native_keys == set(KEYWORDS), f"Native lexer keywords differ: {native_keys ^ set(KEYWORDS)}"

    js_builtin = re.search(r'\[([^\]]+)\]\.includes\(e\.value\)', js)
    native_builtin = re.search(
        r'for\(const char\*s:\{([^}]+)\}\)env->values\[s\]=Value\(Builtin\{s\}\)',
        vm,
    )
    assert js_builtin, "Cannot inspect JS built-in registry"
    assert native_builtin, "Cannot inspect native built-in registry"
    js_names = set(re.findall(r'"([^"]+)"', js_builtin.group(1)))
    native_names = set(re.findall(r'"([^"]+)"', native_builtin.group(1)))
    assert js_names == set(BUILTIN_NAMES)
    assert native_names == set(BUILTIN_NAMES)
