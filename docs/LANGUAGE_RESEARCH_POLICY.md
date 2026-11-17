# Kasa linguistic evidence and keyword approval policy

**Status:** mandatory contributor policy for *new* Kasa language tokens (draft policy, pending project-owner approval)  
**Created:** 2026-11-17 · **Target language:** Twi varieties of Akan, initially Asante/Akuapem  
**Evidence register:** [keyword_evidence.json](./keyword_evidence.json)

## Purpose

Kasa must not select syntax merely by translating an English programming word or trusting an AI-generated suggestion. Lexical attestation, appropriate meaning **in context**, spelling, reading ease, dialect usage, and technical correctness are separate questions. An attested Twi word is **not automatically** the best programming keyword.

This is a **baseline audit**, not a claim that Kasa's existing vocabulary has passed linguistic review. The 17 existing lexer keywords, four built-ins and the contextual conditional particle `a` are preserved for compatibility. Every one is recorded as `legacy_review_pending` until a qualified review takes place. No native-speaker approvals have been solicited or claimed in this change.

## Requirements before adding ANY new Twi syntax or built-in name

1. **Define the intended programming concept.** Specify grammar and runtime behavior before choosing a translation; provide at least two beginner examples and one invalid/edge example.
2. **Verify lexical meaning independently.** Record **at least two independent** relevant references, including **at least one academic, official educational, lexicographic, or identifiable linguist-authored source**. Record URLs, source type, access date, and the *precise* claim each reference supports. Multiple pages from the same author/site are useful but do not constitute independent verification.
3. **Review actual written grammar.** A word's meaning alone is not sufficient. Check part of speech, natural sentence usage, tone-sensitive ambiguity, dialect variants, morphology, and whether a compound needs spaces or underscores for the lexer. Distinguish an ordinary word from a technical neologism.
4. **Check standard spelling.** Use Akan orthography resources, current teaching materials and real use in Asante/Akuapem. Preserve meaningful characters (`ɛ`, `ɔ`), use UTF-8, and check Unicode normalization in the runtime. Never silently drop diacritics or choose ASCII substitutes.
5. **Obtain documented human review.** Seek feedback from **at least two fluent Twi reviewers**, preferably representing Asante and Akuapem, plus **one educator** familiar with teaching beginner computing. Record their consented names/roles or reviewer IDs, dialects, review date, disagreements, and any unresolved concerns. This is a project policy target, not a claim they are already engaged.
6. **Evaluate classroom usability.** Check whether beginners understand the word without an English translation; whether it collides with common variable names; whether it is readily typed on typical Ghanaian keyboard layouts; and whether it carries potentially misleading meanings.
7. **Record a decision.** An accepted term must have a linked decision, evidence entries, completed reviews, and tests in **Python, JavaScript, C++ native**, and the cross-runtime conformance suite as appropriate. Significant grammar or rename changes require an RFC and backwards-compatibility plan.
8. **Document dissent and change control.** If reputable sources conflict, do not manufacture certainty. Mark the candidate `needs_review` and keep it out of released syntax. A future review may retain an existing spelling as an intentional compatibility choice even if another orthography is more common.

## Approval semantics

- `legacy_review_pending`: already implemented before this policy; **not** endorsed linguistically; preserve for now.
- `proposed`: a proposal only; **must not** be implemented as a reserved word or built-in.
- `needs_review`: competing sources or insufficient evidence; **must not** be newly implemented.
- `accepted`: at least two independent sources, documented human review and a decision. Eligible for implementation.
- `rejected` / `deprecated`: must not be introduced as new syntax; deprecation requires compatibility strategy.

The automated test `tests/test_keyword_research.py` checks that **every current Python language keyword, built-in and contextual particle has a research entry**; any new keyword/built-in beyond the frozen pre-policy baseline must be accepted with documentary and reviewer metadata. The test is a **change-control guard**, not a substitute for actual linguistic expertise, independent source inspection or compiler conformance tests.

## Foundational sources and evidence hierarchy

**Authoritative orthography, education, linguistics** (use directly for form and grammar, not as implied approval of technical keywords):

- [Bureau of Ghana Languages / Akan Language Committee, *Akan Orthography: Spelling Rules* (1995), bibliographic record](https://books.google.com/books/about/Akan_Orthography.html?id=lP6BAT0s25sC). A bibliographic record confirms this resource exists; **its full rules were not inspected** in this audit.
- [Harvard ELIAS, *Akan Sounds*](https://elias.fas.harvard.edu/languages/twi/beginning/1/akan-sounds) — vowel system, orthography and tone considerations.
- [Harvard ELIAS, Twi grammar material](https://elias.unix.fas.harvard.edu/languages/twi/beginning/1/akan-family-system) — supports `sɛ ... a` conditional grammar.
- [Schachter and Fromkin (1968), *A Phonology of Akan: Akuapem, Asante, Fante* (ERIC bibliographic record)](https://eric.ed.gov/?id=ED022189) — dialect-sensitive phonology background; not a dictionary entry for any specific Kasa keyword.
- [LearnAkan, *Akan (Asante Twi) Conjunctions*](https://learnakan.com/akan-asante-twi-conjunctions/) — examples for `anaa`, `sɛ ... a`, `berɛ ... a`, and other grammar.

**Lexicographic/reference evidence** (term-by-term, see the structured register): LearnAkan Dictionary and Akan (Twi) Dictionary entry pages; these are helpful, but an entry does not alone settle technical suitability or cross-dialect variation.

## Important current findings (not final approvals)

- `bisa`: strong support for **ask** in at least two dictionaries, so its use for asking for input is plausible. A human reviewer must still consider the exact `bisa(...)` prompt wording and classroom examples.
- `sɛ` with contextual `a`: unusually close to the attested Akan conditional structure. This is **better evidence than a dictionary lookup for a lone word**.
- `ka`: documented as **say**; printing text is a reasonable computing analogy, but the programming mapping is an editorial choice.
- `anyɛ_saa_a`: its natural-language sense is closer to **otherwise** than to a standalone English `else`; review the pedagogical explanation.
- `dwumadie`: sources attest **exercise/task/function** (and educational `exercise`); the [NYS mathematics glossary](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf) includes related form `dwumadi` in explaining mathematical functions (pp. 2–3). This is useful technical-context evidence, but not proof that a callable program function should use the precise spelling `dwumadie`.
- `awiei`: an [Akan dictionary](https://www.akandictionary.com/2021/10/09/awiei/) directly attests this exact spelling for **end**; the [NYS mathematics glossary](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf) also uses `Awiei` for **conclusion/closure**. LearnAkan also records `awieeɛ`. The spelling thus warrants a *variant review*, not a claim that `awiei` is invented.
- `ne`: attested as **and** for words/phrases, whereas `na` can connect clauses/sentences. Using `ne` for Boolean AND is a design adaptation, not ordinary Twi syntax.
- `ɛnyɛ`: attested as **it is not / not be**, which is not identical to a general-purpose Boolean NOT; revisit.
- `atoro`: compare the variants `ntorɔ`/`atorɔ` in the word for a lie, and examine whether **false Boolean** is a natural enough technical analogy.
- `hwee`: lexical **nothing** is supported, but teaching it as a `null`-like value must be explicitly explained.
- `sanma` remains unverified as a single compound in the consulted sources. Published linguistic study provides relevant background for frequentative numerals, while [LearnAkan's writing guide](https://learnakan.com/twi-writing-mistakes/) includes the spelling `mpɛn` in frequency contexts. [New York State's glossary](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf) contains `nsɛm` for matters/statements, which does **not** necessarily mean generic computer text. `tentɛn` must be examined critically: the [U.S. Foreign Service Institute's Twi Basic Course](https://fsi-languages.yojik.eu/languages/FSI/Twi/Basic/FSI%20-%20Twi%20Basic%20Course%20-%20Student%20Text.pdf) (1963, Unit 13, pp. 123–124) uses related form `tenten` for long/tall, **not** the exact spelling currently in Kasa.
- `nɔma`: **number** is attested in the [New York State Education Department's Twi mathematics glossary](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf) (2018, pp. 3–4), as well as [LearnAkan Dictionary](https://learnakandictionary.com/english-twi/figure/). This is stronger evidence for the word, but **does not settle** whether it is an appropriate name for *convert to number*.

## Contributor change procedure

1. Propose a term in an RFC or issue; do not change a runtime.
2. Add a new entry to `keyword_evidence.json` as `proposed`, with source-specific notes and contradictions.
3. Collect and record human review; change to `accepted` only once every criterion is met.
4. Implement consistently in Python, browser JS and C++ native; update normative grammar, user guides and conformance fixtures.
5. Run local tests (including malformed input / Unicode), CI, and a classroom readability check before merge.
6. Include a table in the PR explaining any rejected alternatives and why the chosen token is clearer.

**Last evidence retrieval:** 2026-11-17. Links may change, so maintain original bibliographic details, URLs, authors and access dates. Never describe internet search snippets, AI translations or a dictionary gloss as equivalent to native-speaker approval.
