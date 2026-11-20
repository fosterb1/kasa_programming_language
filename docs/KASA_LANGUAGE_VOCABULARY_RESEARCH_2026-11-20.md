# Kasa Language Design Research — Vocabulary and Grammar Candidate Matrix (2026-11-20)

**Status: researched provisional recommendations, NOT linguistic acceptance or stable syntax approval.**
**Scope:** Kasa's existing basic language, modules/import/exports/packages, and long-term feature vocabulary.
**Owner direction:** Prefer original Twi-first syntax, permit revision when needed; discontinue Netlify and keep browser packaging hosting-neutral.

## 1. Research method and limits

This audit cross-checks Kasa's actual `src/kasa/core.py`, `docs/keyword_evidence.json`, `docs/LANGUAGE_RESEARCH_POLICY.md`, and `docs/TWI_IMPORT_FA_FIRI_DECISION.md` against dictionaries, orthographic bibliographies, linguistic resources, and computing curricula. Each entry below separates (a) attested ordinary-language meaning, (b) proposed programming metaphor, and (c) Kasa implementation status.

**Evidence tiers:**
- **L** = lexical sense seen in at least one relevant dictionary; it does **not** mean the exact Kasa programming use is established.
- **L+** = more than one independent relevant source or a linguist/official academic source offers supporting context; *still* does not certify idiomatic programming grammar.
- **E** = engineering design judgment, not an independently validated Twi translation.
- **R** = requires native-speaker/educator review or clearer attestation.
- **I** = actually implemented somewhere (specify experimental vs stable), not a linguistic endorsement.

The language policy calls for two independent sources, human reviews (preferably Asante and Akuapem + an educator), grammar testing, and cross-runtime conformance before promotion to `accepted`. **None of the new proposed terms meets that full threshold.** Source URLs were inspected/retrieved for this report on 2026-11-20; pay attention to lexicographic glosses and historical spelling limits. Publisher links and bibliographic records alone do not prove rules on pages we could not inspect.

### Sources worth preserving

1. Bureau of Ghana Languages, *Akan Orthography: Spelling Rules* (1995), **bibliographic record, not full text inspected**: https://books.google.com/books/about/Akan_Orthography.html?id=lP6BAT0s25sC
2. University of Ghana, *Akan Terminology: English-Akan Linguistics and Media Glossary* (academic repository record): https://ugspace.ug.edu.gh/items/e888f3a9-a878-4e9a-85ea-9fdee1764027/full
3. Harvard ELIAS, *Akan Sounds*: https://elias.fas.harvard.edu/languages/twi/beginning/1/akan-sounds
4. Akan (Twi) Dictionary, *fa* (take/bring): https://www.akandictionary.com/2021/04/10/fa/
5. Akan (Twi) Dictionary, *firi* (come from): https://www.akandictionary.com/2021/10/16/firi/
6. Akan (Twi) Dictionary, *fi* (depart from): https://www.akandictionary.com/2021/05/08/fi/
7. LearnAkan Dictionary, *share* → `kyɛ`: https://learnakandictionary.com/english-twi/share/
8. Akan (Twi) Dictionary, *kye* (share/distribute among several senses): https://www.akandictionary.com/2021/08/24/kye-2/
9. LearnAkan Dictionary, *show* → `kyerɛ`: https://learnakandictionary.com/english-twi/show/
10. LearnAkan Dictionary, *collect* → `boaboa ano`: https://learnakandictionary.com/english-twi/collect/
11. LearnAkan Dictionary, *party* → `ekuo` (group): https://learnakandictionary.com/english-twi/party/
12. LearnAkan Dictionary, *secret* → `ahintasɛm`: https://learnakandictionary.com/english-twi/secret/
13. Akan (Twi) Dictionary, *te* / *sie* (hide): https://www.akandictionary.com/2021/12/20/te-2/
14. LearnAkan Dictionary, *error* → `mfomsoɔ`: https://learnakandictionary.com/english-twi/error/
15. LearnAkan, *Bɔ Mmɔden vs. Sɔ Hwɛ* (distinguishes different English 'try' senses): https://learnakandictionary.com/b%C9%94-mm%C9%94den-vs-s%C9%94-hw%C9%9B/
16. LearnAkan Dictionary, *license* → `ma kwan` (permit): https://learnakandictionary.com/english-twi/license/
17. LearnAkan Dictionary, *search* → `hwehwɛ`: https://learnakandictionary.com/english-twi/search/
18. LearnAkan Dictionary, *identify* → `da adi` (reveal) and `kyerɛ`: https://learnakandictionary.com/english-twi/identify/
19. Yale University Library, Twi dictionary research guide: https://guides.library.yale.edu/c.php?g=1530945&p=11469706
20. Published research, *Developing a Twi (Asante) Dictionary from Akan Interlinear Glossed Texts*: https://arne.chark.eu/anthology/2020.sltu-1.41/
21. Ghana computing curriculum, official resources entry (computing programming context, **not a Twi programming syntax authority**): https://curriculumresources.edu.gh/wp-content/uploads/2025/12/Computing-Combined-Y2-corrected.pdf
22. LearnAkan, *Agya Nan vs. Agyanan*: https://learnakandictionary.com/agya-nan-vs-agyanan/ — illustrates why spacing, tone, and compound morphology must be reviewed rather than guessed.

Sources 1, 2, 3, 19, 20 offer relevant orthography/lexicography methodology and reference background, **not direct endorsements** of the proposed software vocabulary. Distinct dictionary pages from one publisher are **not** independent sources by themselves.

## 2. Module feature decision table

| Feature | Suggested surface | Linguistic evidence | Engineering/compatibility decision |
|---|---|---|---|
| Import/use existing module | `fa module` | L+: `fa` take/bring; full programming phrase unreviewed | I (Python/JS **opt-in experimental only**); retain as default shorthand |
| Named source | `fa module firi stdlib` | L+: `firi` come from; Asante spelling commonly contrasted with `fi`; phrase idiomaticity unverified | I experimental; allow **only pinned stdlib**; no network or filesystem |
| Akuapem variant | `fi` | L; supported depart-from form; dialect variation needs review | **Do not enable yet**; ask reviewers whether `fi` is natural/should be alias |
| Alias | `fa math firi stdlib: m` | E: colon is notation, not a translation | I experimental; no dedicated `as` keyword |
| Public export | propose `kyɛ` (share), or `kyerɛ` (show), after review | `kyɛ` L+ share/distribute, `kyerɛ` L show | **No new syntax now**; manifest explicit exports continue to define public API |
| Private | omit export by default | E; `sie` / `ahintasɛm` involve hide/secret but neither proves program-member privacy | **No new keyword now**; private-by-default already works in experimental namespace |
| Module member | `m.kasa_sum(...)` | E: established programming punctuation | I experimental; must be explicit exported member, not arbitrary object/property lookup |
| Module | a named source file/catalog entry; human explanation may say `adwuma-kuo` only if later reviewed | `ekuo` = group (L), but 'software module' is not shown attested | **No new keyword**; call it a module in developer docs until reviewed |
| Package / grouping | `ekuo` conceptual candidate; `boaboa ano` means gather | L, but a package is more specific than any group | **Do not create a package keyword**; define metadata and packaging semantics first |
| Dependencies | declared catalog dependencies | E: runtime/compiler dependency graph terminology not established lexically | Metadata first; cycle detection and deterministic resolution, no keyword |
| Public visibility / exposing | `kyerɛ` or `da adi` as future candidate | L for show/reveal | Avoid ambiguous overlap with `ka` print; review with real example |
| Local source paths | proposed future `fa ... firi "path"` | E; quoted paths are technical | **Not implemented; security design required**; reject current external source |
| Versioned third-party packages | none | no relevant established term found | Defer; trust/signing, registry and compatibility require design first |

### Preferred minimal grammar, existing experimental interpreter only

```text
fa math
fa math: m
fa math firi stdlib
fa math firi stdlib: m
ka m.kasa_sum([10,20,30])
```

These examples are executable **only when the experimental module option is enabled** on the Python or JS prototype. The legacy `@math:m` remains accepted for migration, but is not preferred to teach. `stdlib` remains an internal ID, not claimed to be Twi. No new global reserved words.

### Rejected/paused alternatives

- `fri`: owner proposed the sound/phrase, but `firi` is the attested written form selected in the prototype. Continue verifying spellings/dialect usage rather than treating phonetic typing as a standardized word.
- `kyɛ` immediately as reserved `export`: an attested everyday sense of 'share' does not decide whether the word should alter source-level visibility or package publication; risk of collisions and cross-runtime inconsistency.
- `kyerɛ` immediately as reserved export: 'show' may suggest console output or displaying data and conflict conceptually with existing `ka`.
- `sie` as a `private` keyword: could imply saving/storing or hiding something, not necessarily module encapsulation; technical metaphor not validated.
- `modul`, `package`, `alias` as unreviewed English loanwords in syntax: weak Twi-first rationale.
- Translation for every concept: more reserved words means more collisions and learning burden without adding necessary expressiveness.

## 3. Current stable Kasa words: retain, audit, do not silently rename

The real Python keyword table currently contains **17** globally reserved words:
`ka` (print), `ma` (assign), `sɛ` (if), `anyɛ_saa_a` (else), `mpɛn` (repeat), `bere_a` (while), `dwumadie` (function), `sanma` (return), `awiei` (end), `nokware` (true), `atoro` (false), `hwee` (none), `ne` (and), `anaa` (or), `ɛnyɛ` (not), `gyae` (break), and `toa_so` (continue). Four built-ins: `bisa` (input), `tentɛn` (length), `nɔma` (convert to number), `nsɛm` (convert to text). Contextual particle `a` is used in `sɛ ... a`.

**Important linguistic risk flags identified earlier in `docs/LANGUAGE_RESEARCH_POLICY.md`:**
- `sanma` as a single compound is not securely verified.
- `dwumadie` has task/function/exercise-related senses, but precise programming usage and spelling may differ across contexts.
- `ne` is not necessarily the ordinary clause-level equivalent of boolean AND.
- `ɛnyɛ` may be a copular negation, not arbitrary logical NOT.
- `atoro` has possible `atorɔ/ntorɔ` variants, and false as a software boolean is a metaphor.
- `tentɛn` reflects long/tall; function name for *sequence length* is a technical adaptation.
- `hwee` meaning nothing is not a full definition of null/none semantics.
- `nɔma` as a number noun is not automatically a strong name for numeric conversion.
- `anyɛ_saa_a` may describe 'otherwise', distinct from simple English 'else'.

The pre-policy inventory marks all 17 keywords and four built-ins as **legacy_review_pending**, not certified linguistic translations. **Do not break programs by renaming any** without a separate compatibility RFC and user migration period.

## 4. Future feature candidate register (not syntax commitments)

| Domain / desired meaning | Attested candidate or engineering placeholder | Evidence | Implementation verdict |
|---|---|---|---|
| Error / mistake | `mfomsoɔ` | L, LearnAkan 'error' | Suitable for diagnostics/glossary first; avoid conflating a value/error message with exception object |
| Attempt / try | `sɔ hwɛ` | L: LearnAkan grammatical discussion distinguishes trying from effort `bɔ mmɔden` | Research possible `sɔ_hwɛ` only after specifying try-block semantics; spacing/underscore unapproved |
| Raise / throw exception | `to` (throw) literal candidate | L for physical 'throw', not program exceptions | **No commitment**; metaphor may be misleading |
| Catch / handle exception | unresolved | R; *catch* has many physical/metaphorical meanings | **No commitment**; design exception flow before wording |
| Permission / grant capability | `ma kwan` | L, LearnAkan license/excuse | Potential documentation phrase; do not equate with runtime authorization until security spec exists |
| Secret / private data | `ahintasɛm`, `sie` | L, LearnAkan secret, Akan hide | Useful educational vocabulary, not necessarily a visibility keyword |
| Search | `hwehwɛ` | L | Candidate for library function names rather than global keyword |
| Gather / aggregate | `boaboa ano` | L | Consider `boaboa_ano` for user-facing standard-library APIs after validation |
| Group / collection | `ekuo` | L | Could inform course explanations, but not a definitive type/namespace label |
| Display / reveal | `kyerɛ`, `da adi` | L | Consider as UI/explanation wording; potential ambiguity with `ka` |
| Classes / objects / interfaces | **unresolved** | No reliable software-semantic Twi attestation established in this round | Do not invent single-word translations; first design the type/object model |
| Async / await / promise | **unresolved** | No reliable equivalent verified | Design scheduling/task semantics first, research terminology with educators |
| Files / read/write / streams | **unresolved** | No technical semantic evidence verified this round | Do not add file capabilities from language-vocabulary research |
| Generics / type annotations | **unresolved** | No validated technical equivalent in consulted sources | Postpone to type-system RFC |
| Package publication | `kyɛ` conceptually attractive, but not a verified 'publish' synonym | L+ for share, not software release | Separate exporting symbols from publishing a distributable package |

### Design rule

Where punctuation or metadata can express semantics clearly, prefer those over a new reserved keyword. Introduce a new Twi spelling *only after the semantic contract is fixed*. Never infer language quality solely from the English gloss or conflate an ordinary word with a technical neologism.

## 5. Proposed language decision/implementation order

**D0 — Immediately provisional, already being implemented experimentally**
- Import `fa ... firi stdlib`, aliases `:`, exported-member access `.`.
- Reuse the pinned catalog, private-by-default visibility and manifest-based exports. Preserve default stable interpreter compatibility.
- Keep `firi` contextual only in module declarations.

**D1 — Review next, before adding any export keyword**
- `kyɛ` vs `kyerɛ` vs no keyword for public exports.
- Question: does 'share with other modules' sound natural as an imperative command? Show exactly one public function and one helper that must stay private.
- Decision can be **no new keyword**; existing explicit exports in manifest already express safe boundaries.

**D2 — Structural packages**
- Define directory/package manifest naming, unique identifiers, local path boundary, relative imports, cycles, versioning and no untrusted capabilities.
- Only then consider `ekuo` as an instructional term.

**D3 — Developer diagnostics and libraries**
- Investigate `mfomsoɔ`, `sɔ hwɛ`, `boaboa ano`, `hwehwɛ` through classroom examples.
- Prefer names in glossary or standard library before global language tokens.

**D4 — Later language RFCs**
- Error handling, file API, type system, classes/objects, interfaces, async/await, networking. Each needs an independent semantic + linguistic RFC, and performance/capability review.

## 6. Human-review question set (not yet performed)

1. Which naturally explains 'bring the math library into this program': `fa math`, `fa math firi stdlib`, another form, or a sentence with explicit direction/recipient?
2. Is `firi` appropriate in Asante? Would an Akuapem learner naturally write `fi`? Should both variants parse?
3. Does `kyɛ` signal 'make a function public to another module' or 'split/give away'? Does `kyerɛ` mean reveal without sharing?
4. Do `fa`, `firi`, `kyɛ` conflict with names pupils commonly give variables/functions? Could `fa` remain contextual?
5. Should package metadata be named in English for interoperability while teaching a Twi conceptual term?
6. Which spellings and tone/spacing conventions are best for code, especially on low-cost Ghanaian phones/keyboards?
7. Which example best explains it to beginners: market receipts, school fees or mobile-money accounting?
8. Can reviewers explain the phrase back without an English gloss? Record errors and alternatives.

**Approval gate:** at least two fluent Asante/Akuapem reviewers and one computing educator, source-specific linguistic evidence, code exercises, Python/JavaScript/C++ compatibility and written decision. No review participation has been claimed.

## 7. Research conclusions

1. **Proceed with the *existing experimental* `fa ... firi stdlib`**, keeping stable syntax unchanged.
2. **Do not yet implement `kyɛ` as an export keyword**; this is the clearest next linguistic + semantic decision.
3. Keep private-by-default + explicit manifest exports, aliases through punctuation and named members via dot.
4. Use `ekuo`, `boaboa ano`, `mfomsoɔ`, `sɔ hwɛ` as *documented candidates* with individual evidence—not guaranteed translations for computing constructs.
5. Do not translate classes, async, interfaces, packages or exceptions into guessed Twi tokens until each feature's technical semantics are specified and terminology reviewed.
6. Move toward a **versioned language RFC**, independent tests, cross-runtime behavior corpus and backward compatibility policy before calling the import grammar official.
