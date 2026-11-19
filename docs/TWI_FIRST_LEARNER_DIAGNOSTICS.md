# Kasa learner diagnostics — Twi-first review preview (G0.3 parallel education slice)

**Status: Experimental Python-only opt-in, not an approved Twi translation or public browser feature.**
**Date: 2026-11-20**

## Principle

Kasa's educational language and Ghanaian feel must include *the whole learning loop*: syntax, error feedback, examples, instructor notes, Academy material, and public APIs. A credible Twi-first experience does not conceal technical diagnostics or invent unreviewed Twi phrases.

## What shipped in this slice

- `src/kasa/learning_diagnostics.py`: fixed category-to-teaching-card mapping. Cards include a provisional Twi concept label and an English explanation of the computing mistake. Every card carries `draft_needs_human_review`.
- `playground/runner.py`: optional keyword argument `learner_language="tw"` to attach a `learning_hint` to recognized Python Kasa runtime/parser errors. The default `learner_language="en"` response is unchanged.
- `tests/test_learning_diagnostics.py`: regression checks for default API, source coordinates, explicit draft status, unknown categories, unsupported language, success and resource failure.

This **does not** change any Kasa keyword, error code, diagnostic coordinates, browser worker / JS runtime, native compiler or KBC1. It does not translate arbitrary user code or reveal unbounded runtime details. Only recognized KasaError categories receive a hint, and an unreviewed candidate is never presented as an approved language rule.

## Local trial (from checkout root, Python environment activated)

```bash
python -m pytest -q tests/test_learning_diagnostics.py tests/test_playground.py
python - <<'PY'
import sys
sys.path.insert(0, "playground")
from runner import execute_kasa
result = execute_kasa("ka 1 / 0", learner_language="tw")
print(result["error"])
print(result.get("learning_hint"))
PY
```

## Review gate before UI release

1. Recruit consenting Asante and Akuapem Twi reviewers and an educator.
2. Review exact orthography, dialect usage, technical semantics, clarity, and inappropriate or awkward mappings. In particular, verify `edin`, `nhyehyɛe`, `akyɛmu`, `dinom`, `anohyeto` as *provisional* labels, not endorsed equivalents.
3. Add consistent Python/JS/native diagnostic categories with shared fixtures where applicable. Only then implement a real Academy/playground language preference and learner UI.
4. Prioritize Ghanaian practical scenarios such as cashbooks, MoMo reconciliations and school fees without claiming current examples are production financial software.

## Open engineering issue

Kasa language-level module import/member access remains unimplemented; the catalog-backed Python binder is internal tooling. This learner feedback work is a parallel educational addition, **not** a replacement for the Group 0 import roadmap.
