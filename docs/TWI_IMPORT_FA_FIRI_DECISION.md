# Decision record: Provisional Twi-first imports with `fa ... firi ...`

**2026-11-20 | Owner-supported provisional direction, not yet linguistically approved for stable Kasa**

## Proposed language design

A Kasa import introduces a named catalog module with an optional alias and an optional explicit source. The first reserved source name is `stdlib`, representing the **locally pinned** Kasa standard-library catalog.

```kasa
# Short form; alias defaults to the module identifier.
fa math
ka math.kasa_sum([1, 2, 3])

# Explicit origin and optional alias.
fa math firi stdlib: m
ka m.kasa_sum([10, 20, 30])

fa collections firi stdlib: c
ka c.kasa_contains([1, 2, 3], 2)
```

`fa math: m` is also accepted as the source-default shorthand. Experimental `@math:m` remains accepted as a migration/compatibility bridge but **should not be taught as the preferred Twi syntax**.

### Why this phrase, rather than the English word `import`?

- `fa`: attested in Akan as *take / bring*, appropriate as an approachable metaphor for reusing a module.
- `firi`: attested Asante Twi form with meaning *come from / originate from*. Harvard ELIAS explicitly lists `fi(ri)` in its sound/lexical teaching material.
- `fi`: attested Akuapem/dialectal form. We are **not** yet adding a dialect-specific alias into executable grammar; first establish acceptance and spelling conventions.

Primary sources consulted 2026-11-20:
- Akan Dictionary, [fa — take/bring](https://www.akandictionary.com/2021/04/10/fa/).
- Akan Dictionary, [firi — come from](https://www.akandictionary.com/2021/10/16/firi/).
- Harvard ELIAS, [Akan Sounds](https://elias.fas.harvard.edu/languages/twi/beginning/1/akan-sounds), `fi(ri)` / `fa`.
- Christaller, [Grammar of Asante and Fante (Akuapem reference)](https://upload.wikimedia.org/wikipedia/commons/d/dc/A_Grammar_of_the_Asante_and_Fante_Language_Called_Tshi_Chwee%2C_Twi_Based_on_the_Akuapem_Dialect_..._%28IA_agrammarasantea00chrigoog%29.pdf), discusses `fi/firi` with a *from* relation.

**Language limitation:** These sources establish individual words and some usage, **not** that `fa math firi stdlib` is a naturally idiomatic Twi computing instruction. The project-owner's direction authorizes prototyping, not a claim of grammatical validation by fluent Asante/Akuapem speakers or educators. The independent human reviews mandated in `docs/LANGUAGE_RESEARCH_POLICY.md` are still missing. Status is **provisional_owner_direction / needs_review**, not `accepted`.

## Implementation and bounded semantics

- Python and JavaScript experimental parsers recognize contextual `fa` and `firi` only when experimental modules are enabled, **without modifying `KEYWORDS`** or the legacy token inventory. Normal language mode does not accept module imports.
- Only `firi stdlib` is currently a valid explicit origin; `firi files`, URLs, package registries, and other origins are rejected at syntax check. No filesystem or network capability is granted.
- `fa math` and `fa math firi stdlib` bind module alias `math`. `fa math firi stdlib: m` binds alias `m`.
- The already validated catalog, public exports, duplicate-alias handling and namespace isolation continue to apply.
- Dot syntax means access to a known exported function through its module alias; it is **not** unrestricted Python-style attribute access.
- The source token `stdlib` is a fixed internal identifier, not presented as a Twi word. Later source naming and package semantics require separate decisions.

## Before promoting to official stable syntax

1. Obtain documented written example feedback from at least two fluent Twi reviewers (Asante and Akuapem where possible) and one computing educator.
2. Investigate the grammar of `fa [thing] firi [source]` and whether `fa ... firi ...` should instead use another natural construction; verify pronunciation, spelling, keyboard practicality and meaning in real instructional sentences.
3. Decide if `fi` should be accepted as a dialect variant, with explicit grammar and test policy.
4. Expand cross-runtime fixtures, then implement C++ and KBC1 before declaring consistent Kasa syntax.
5. Announce a versioned change and plan for eventual removal of legacy `@module:alias`.

## Developer acceptance gate

```bash
git -c http.proxy=http://192.168.49.1:8282 pull --ff-only
python -m pytest -q tests/test_experimental_module_source.py tests/test_playground_module_ui.py
node --check playground/kasa-runtime.js
node tests/test_js_experimental_modules.js
node tests/test_js_playground_module_ui.js
node tests/test_js_worker_modules.js
python scripts/run_kasa_modules_experimental.py stdlib/demos/group0_source_import_experiment.kasa
bash scripts/mac_dev.sh quick
```

These tests are **not yet rerun on Mac** for this commit.


## Punctuation decision — keep `:` for module aliases (owner direction, 2026-11-20)

**Chosen for the provisional module grammar:** `fa math: m` and `fa math firi stdlib: m`. The colon is **an alias separator only in an import declaration**, not a general assignment operator, type annotation, dictionary entry, or object-field definition.

Reasoning:

- A colon is compact, neutral across Twi dialects and easier to type than introducing an unreviewed new language keyword for English `as`.
- It does **not** prevent future dictionaries/maps (`{key: value}`), type annotations (`ma x: Type`) or slices (`items[1:4]`); those would have different surrounding tokens and parser productions, if separately approved.
- **Potential ambiguity** must be controlled by grammar context. The import production ends at NEWLINE; after a single colon it accepts exactly one alias `NAME`. A second colon or a missing alias raises a syntax error. A colon embedded inside a quoted string remains text.
- The existing stable tokenizer does not globally recognize `:`. Only the opt-in module mode currently tokenizes it. Future uses would require explicit lexer/parser changes and conformance tests; they do not happen automatically.
- Do **not** adopt `:` for other semantics merely for consistency. Reserve judgment on type annotations, map literals, slices, named arguments or labels until those concepts are designed.
- The contextual word `fa` itself is a more substantial compatibility risk than the colon: in experimental mode, a statement beginning with `fa` is parsed as an import declaration. Stable Kasa remains unchanged, but a future formal import grammar must explicitly address ordinary variables/functions named `fa` and contextual ambiguity.

**Decision status:** Provisional syntax accepted for continued Kasa development by the owner; **no human linguistic certification** and **no stable release designation**. The current manifest-based exports/private-by-default model is retained. Research candidates for unresolved concepts remain open, and no speculative export/type/package keywords are introduced.

**Regression gate:** `tests/test_experimental_module_source.py` and `tests/test_js_experimental_modules.js` cover optional aliases, source-qualified aliases, empty/double colon rejection and quoted-text safety. Test cases have been committed; Mac execution of these new tests is pending.
