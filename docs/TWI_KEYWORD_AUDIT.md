# Kasa Twi keyword audit — reference-linked working draft

**Audit date:** 2026-11-17 · **Scope:** 17 existing lexer keywords, 1 contextual conditional particle, 4 existing built-ins. The expanded evidence includes an NY State education glossary (2018), U.S. Foreign Service Institute course (1963), and University of Ghana linguists' published work (2019).

**Important:** Every word below is **already implemented** and its status is **legacy_review_pending**. The references support the *stated lexical or grammatical claim*, not approval of a programming language keyword. Missing links mean **additional primary-source research is required**; none of the words has been approved by native-speaker/educator review. See the [research and approval policy](./LANGUAGE_RESEARCH_POLICY.md) and [machine-readable evidence register](./keyword_evidence.json).

## Existing tokens and evidence

| Token | Kasa meaning | Published references | Outstanding concern |
| --- | --- | --- | --- |
| `ka` | Print | [LEARN_SAY](https://learnakandictionary.com/english-twi/say/) | The ordinary verb 'say' supports a spoken-output metaphor, but not necessarily written output. |
| `ma` | Assign | [HARVARD_SOUNDS](https://elias.fas.harvard.edu/languages/twi/beginning/1/akan-sounds) | Attested as give in Harvard's phonology lesson; variable assignment is a programming analogy. |
| `sɛ` | If | [HARVARD_GRAMMAR](https://elias.unix.fas.harvard.edu/languages/twi/beginning/1/akan-family-system), [LEARN_A](https://learnakandictionary.com/twi-english/a/), [LEARN_CONJ](https://learnakan.com/akan-asante-twi-conjunctions/) | 'Sɛ ... a' conditional construction is attested; particle a is handled contextually. |
| `anyɛ_saa_a` | Else | [OTHERWISE](https://bubblegum.la/grammar/twi/otherwise-s-ny-saa-a-9622bf9c) | Closest attested phrasing is 'otherwise' rather than an isolated else keyword. |
| `mpɛn` | Repeat count | [LEARN_WRITING](https://learnakan.com/twi-writing-mistakes/), [UG_NUMERAL_STUDY](https://njas.fi/njas/article/view/427) | LearnAkan uses mpɛn for frequency ('times'); linguistic research on Akan frequentative/multiplicative numerals provides context, but direct spelling, Asante/Akuapem variants, and the meaning of a programming loop counter still need speaker review. |
| `bere_a` | While | [LEARN_WHEN](https://learnakandictionary.com/english-twi/when/), [LEARN_CONJ](https://learnakan.com/akan-asante-twi-conjunctions/) | LearnAkan describes 'berɛ a' as 'when/while'; spelling 'bere' without ɛ needs review. |
| `dwumadie` | Function definition | [AKAN_DWUMADIE](https://www.akandictionary.com/2022/10/10/dwumadie/), [LEARN_GRAMMAR](https://learnakan.com/twi-grammar-terms/), [NYS_TWI_MATH](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf) | Akan dictionary supports dwumadie for work/task/function; NYS mathematics glossary translates function as akontaabu abusuabɔ (dwumadi/nhyiam), including the spelling dwumadi. Do not assume mathematical function and executable function are identical. |
| `sanma` | Return from function | **No direct entry recorded — research required** | Compound form and semantics lack verified lexical evidence; urgent review. |
| `awiei` | Block end | [AKAN_AWIEI](https://www.akandictionary.com/2021/10/09/awiei/), [LEARN_FINISH](https://learnakandictionary.com/english-twi/finish/), [NYS_TWI_MATH](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf) | Exact awiei spelling appears both in Akan dictionary for end and in NYS school mathematics glossary ('conclusion', 'closure'); alternative awieeɛ spelling in LearnAkan merits dialect/orthography review. |
| `nokware` | Boolean true | [LEARN_TRUTH](https://learnakandictionary.com/english-twi/truth/) | Truth is attested; Boolean literal mapping is technical analogy. |
| `atoro` | Boolean false | [LEARN_LIE](https://learnakandictionary.com/english-twi/lie/) | Check differences between atoro and ntorɔ/atorɔ spellings and sense of lie vs falsehood. |
| `hwee` | No value / null | [AKAN_HWEE](https://www.akandictionary.com/2021/04/14/hwee/) | Dictionary attests nothing/null-like meaning, but lexical nothing is not identical to typed null. |
| `ne` | Logical AND | [LEARN_AND](https://learnakandictionary.com/english-twi/and/), [LEARN_CONJ](https://learnakan.com/akan-asante-twi-conjunctions/) | Attested conjunction links words/phrases; Boolean logical usage requires review. |
| `anaa` | Logical OR | [AKAN_ANAA](https://www.akandictionary.com/2022/10/17/anaa/), [LEARN_CONJ](https://learnakan.com/akan-asante-twi-conjunctions/) | Attested conjunction or. |
| `ɛnyɛ` | Logical NOT | [GRAMMAR_NEG](https://learnakandictionary.com/learn-twi-with-public-inscriptions-aboter%C9%9B-y%C9%9B/) | Attested negation of yɛ ('is not'), not necessarily a general Boolean negation operator. |
| `gyae` | Break loop | [AKAN_GYAE](https://www.akandictionary.com/2021/04/22/gyae/) | Attested stop, halt, abandon; mapping to loop break is plausible. |
| `toa_so` | Continue loop | [LEARN_CONTINUE](https://learnakandictionary.com/english-twi/continue/) | Attested as 'carry on'; native written form normally contains a space. |
| `a` | Contextual conditional marker | [LEARN_A](https://learnakandictionary.com/twi-english/a/), [HARVARD_GRAMMAR](https://elias.unix.fas.harvard.edu/languages/twi/beginning/1/akan-family-system) | Used after a sɛ conditional clause; not globally reserved in Kasa. |
| `bisa` | Read input | [LEARN_ASK](https://learnakandictionary.com/english-twi/ask/), [AKAN_BISA](https://www.akandictionary.com/2021/05/08/bisa/) | Attested as ask in two independent dictionaries. Programmer use for interactive input is an adaptation. |
| `tentɛn` | Length built-in | [LEARN_WRITING](https://learnakan.com/twi-writing-mistakes/), [FSI_TENTEN](https://fsi-languages.yojik.eu/languages/FSI/Twi/Basic/FSI%20-%20Twi%20Basic%20Course%20-%20Student%20Text.pdf) | References attest related spelling 'tenten' meaning long/length, not the exact implemented 'tentɛn'. These are comparison references, not direct support for this exact word; high-priority spelling and function-semantics review. |
| `nɔma` | Number conversion | [GITHUB_NUM](https://github.com/aberba/twi-synonyms), [NYS_TWI_MATH](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf), [LEARN_FIGURE](https://learnakandictionary.com/english-twi/figure/) | NYS State Education Department mathematical glossary uses nɔma as 'number'; LearnAkan also attests the noun. Existing Kasa function converts text to a number, which differs from the noun meaning. Further review needed. |
| `nsɛm` | Text conversion | [NYS_TWI_MATH](https://www.rcsdk12.org/cms/lib/NY01001156/Centricity/Domain/4194/hs_integrated_algebra_twi-14p.pdf), [JWAL_NSEM](https://journalofwestafricanlanguages.org/downloads/send/4-volume0201/43-some-twi-phrase-structure-rules) | NYS maths glossary and linguistic usage include nsɛm for 'statements/matters'; this is NOT independent evidence that nsɛm means an arbitrary string or text conversion. High-priority terminology review. |

## Evidence-quality notes

1. **Attested word ≠ approved programming concept.** For example, evidence that `dwumadie` means “exercise/task/function” cannot alone settle its meaning as a callable program function.
2. **Morphology matters.** Akan `sɛ ... a` is a documented conditional construction, not merely two English-to-Twi dictionary equivalents.
3. **Preserve spelling variants until reviewed.** An Akan dictionary directly lists `awiei`, while LearnAkan uses `awieeɛ` in a related “ending” entry; both are evidence, not a reason to break users' files.
4. **Boolean operations are technical analogies.** `ne` for Boolean AND, `ɛnyɛ` for Boolean NOT, and `atoro` for False require explicit teaching and native-speaker judgment.
5. **No new word may be adopted solely from this list.** Native-speaker consultation and technical test coverage are mandatory before acceptance.
6. **Potential loanwords and compound forms** such as `nɔma`, `sanma`, and `tentɛn` require careful semantic review. `nɔma` is documented as the mathematical noun **number**, but `sanma` remains unverified as a compound, and sources for `tentɛn` attest **tenten** rather than its exact spelling. Their use in the current implementation is grandfathered, not linguistically endorsed.

## Source provenance

The reference IDs in the table resolve to exact URLs in `keyword_evidence.json`, including source titles, publishers, types, and the access date. The project uses primary academic/educational sources where available (especially Harvard ELIAS and Bureau of Ghana Languages references), alongside identifiable language-education dictionaries. Independently authored sources are preferred; repeated references from one publisher do **not** count as independent confirmation.

For the Bureau of Ghana Languages' 1995 *Akan Orthography: Spelling Rules*, only a **bibliographic record** was reviewed in this audit, not the full text. Future contributors must consult the spelling rules directly before treating them as evidence for an exact candidate spelling.

## Next linguistic research priorities

Investigate, in this order: `sanma`, `tentɛn`, `nsɛm`, `mpɛn`, `nɔma`, `atoro`, `ɛnyɛ`, `bere_a` and `anyɛ_saa_a`. For each, record two independent sources, actual sentence examples, dialect differences, Twi teaching suitability, alternative spellings, source publication metadata, and the human review decision. In particular, distinguish evidence for a **related form** (e.g. `tenten`) from direct evidence for the implemented token (`tentɛn`).

No human reviewers have yet been commissioned or recorded.
