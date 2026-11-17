# Kasa product focus: Twi-first practical computing

**Status:** Proposed product direction, 2026-11-17. Not a claim that Kasa has a proven market advantage.  
**Language policy:** [Research before introducing Twi keywords](./LANGUAGE_RESEARCH_POLICY.md). No new Twi syntax is proposed here.

## North star

**Help a learner move from a meaningful problem in their own language to a small working program that can run offline.** Start with Ghanaian classroom numeracy, household budgeting and small-business computations; preserve a path from beginner lessons to serious programming.

Kasa is an *independent programming language implementation* in Python, browser JavaScript and a C++ bytecode VM alpha. It should not compete with C++ on throughput, Python on library breadth, or Scratch solely on animations. Its proposed advantage is the *combination* of language accessibility, local relevance, offline execution, consistent behavior and transferable programming concepts.

## Evidence motivating the direction

1. [Ghana Ministry of Communication, Digital Technology and Innovations, National AI Strategy launch, April 24, 2026](https://moc.gov.gh/2026/04/24/ghana-launches-national-ai-strategy-to-drive-digital-transformation-and-economic-growth/) emphasizes AI/digital skills and localization to Ghanaian languages and contexts. This is policy alignment, **not an official endorsement of Kasa**.
2. [UNICEF Ghana, education in 2026](https://www.unicef.org/ghana/blog/what-should-we-really-be-thinking-about-ghanas-education-system-2026) highlights local-context teaching and the gap between native-language policy and the limited language support in most digital tools.
3. [Scratch Foundation creative-learning philosophy](https://www.scratchfoundation.org/learn/learning-library/scratch-creative-learning-philosophy) describes beginner-accessible, project-driven computing and low floors/wide walls/high ceilings. Kasa can learn from this without claiming that playful learning is a novel invention.
4. [Bank of Ghana Act, 2002 (Act 612)](https://www.bog.gov.gh/wp-content/uploads/2019/09/bank-of-ghana-act-2002-act-612.pdf) states that a cedi has **100 pesewas**. Using integer pesewas in beginner money calculations avoids floating-point money errors and teaches auditable arithmetic.

These sources support **relevance and design reasoning**, not a verified user-preference or learning-outcome claim. Validate with learners and teachers before making superiority claims.

## Initial product advantages to validate

| Focus | First tangible feature | Evidence of success |
| --- | --- | --- |
| Twi-first explanations | Link researched existing syntax to readable error explanations | Learners can locate and correct common mistakes |
| Offline first | Local Python/native execution and bundled browser runtime | Exercises run without a network connection |
| Practical numeracy and commerce | Cashbook, stock reorder, school-fee balance examples | Beginners build useful programs, not only greetings |
| Transferable skills | Kasa ↔ Python concept comparisons | Learners can explain and translate loops/functions |
| Safe financial computation | Integer subunits, explicit units and checks | Examples avoid accidental decimal money drift |
| Independent technology | Portable bytecode and VM with explicit conformance | The same supported programs execute consistently |

## First examples in this proposal

- [Market cashbook](../examples/market_cashbook.kasa): integer pesewa receipts, refunds, expenses and closing cash
- [Stock reorder](../examples/stock_reorder.kasa): inventory additions, sales and reorder threshold
- [School fees](../examples/school_fees.kasa): remaining fees after payments and scholarship

These are deterministic teaching programs with illustrative numbers. **They are not complete accounting packages** and do not provide bank reconciliation, audit trails, regulatory reporting, or financial controls.

## Experiment before scaling

A small **pilot proposal**: recruit consenting teachers and beginner learners across different experience levels; compare task completion, time to first useful program, error recovery, ability to explain the code, and offline usability. Record the method and privacy safeguards before involving minors. Neither improvement nor superiority may be claimed until measured.

Avoid replacing Python or JavaScript as the learning objective. The beginner should understand the underlying computational idea well enough to transfer it.

## Prioritized engineering roadmap

1. **Kasa 0.4 foundations:** local verification, consistent source locations, numeric and runtime semantics, native VM hardening.
2. **KBC1 draft:** compile `.kasa` to validated `.kbc` and execute it in C++; compare with source execution and reject malformed files. Do not advertise it as a secure untrusted-code format.
3. **Practical learning starter kit:** 15+ diverse offline programs, clear steps, real-world examples and teacher guidance.
4. **Language pedagogy:** linguistically reviewed Twi messages, better diagnostic hints, bilingual/English reference material and learners' feedback.
5. **Financial and data libraries (future):** fixed-point decimals/currency, structured CSV, ledgers, safe file APIs and data exchange—only after a security/permissions model.

## Non-goals for this phase

- New Twi keywords based on machine translation.
- Claims of being the first African-language programming language.
- Becoming a high-performance replacement for Python, JavaScript, Rust or C++.
- Shipping production accounting software before monetary representations and data integrity are carefully specified.
- Mandatory cloud AI, accounts, internet access, or paid subscriptions to run basic Kasa code.

**Review requirement:** Keep this direction revisable after evidence from Ghanaian learners, educators and community feedback.
