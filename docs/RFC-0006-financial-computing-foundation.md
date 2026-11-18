# RFC-0006 — Financial computing foundation without new language keywords

**Status:** Experimental teaching design, not a production finance library.  
**Date:** 2026-11-18  
**Scope:** Kasa programs using existing lists, integers, comparisons, loops and functions.

## The Kasa north star remains unchanged

Kasa is a **Twi-first, offline-first programming language for Ghanaian learners**, not a
Python translation and not primarily an accounting application. Practical tasks
such as cashbooks, school fees, merchant inventory and financial reconciliation
are meaningful **teaching contexts** for learning transferable algorithms.

The new financial-computing track must never eclipse language correctness,
Twi linguistic review, beginner teaching outcomes, security and independent
Python/JavaScript/C++/KBC1 conformance.

## Current implemented teaching algorithm

The program `examples/bank_reconciliation_matching.kasa` demonstrates
one-to-one exact-amount matching using integer pesewas:

1. Maintain a ledger-used Boolean list. Each ledger transaction is eligible once.
2. Process each bank transaction in input order.
3. Select the **first** currently unused ledger value with exactly the same amount.
4. Mark the ledger entry used and count the match.
5. Accumulate unmatched bank and ledger counts and signed totals separately.

Duplicate values must not cause the same ledger transaction to be reused.
The algorithm's worst-case runtime is **O(B × L)** for B bank and L ledger
entries and uses **O(L)** matching-state memory. For the sample, bank has
[5000, 7000, 5000, 12000], ledger has [5000, 5000, 9000, 7000],
and the program matches three transactions; 12000 pesewas remains unmatched
on the bank and 9000 on the ledger.

The shared regression corpus tests baseline, duplicate-only, disjoint and
zero-value cases. The golden stdout is registered in the root-example corpus.

## What this demonstrator must NOT claim

- Matching on amount alone is **ambiguous**; duplicate entries can represent
  different dates, accounts, counterparties, references, fees or fraud.
- It does not import real bank statements, normalize debit/credit directions,
  support partial/split settlements, date tolerances, currency conversions,
  reversal pairs, approval controls, privacy protections or audit trails.
- Positive/negative signs are carried as integer values but real account
  direction semantics are not modeled here.
- Counts and totals are examples, not confirmed banking transactions or
  evidence of accounting accuracy.
- No `Finance Core` standard-library API has been implemented or announced.

## Non-negotiable future design gates

**0.4 gate:** Execute all source and KBC1 reference-conformance cases under a
complete local checkout; keep existing Twi vocabulary stable.

**Currency gate:** Define a currency-tagged fixed-subunit value contract with
explicit overflow, sign and rounding policies. A bare integer is not sufficient
to represent currencies with different subunit scales.

**Input gate:** Define deterministic, bounded UTF-8 CSV parsing, explicit
schema mapping, line-level diagnostics and a permissions policy before exposing
file access. No silent field guessing or AI-derived transaction decisions.

**Matching gate:** Define structured transactions, ordered matching rules,
ambiguity handling, stable tie-breaking, unmatched reason codes, duplicate IDs,
and replayable provenance. Do not auto-mark ambiguous cases as reconciled.

**Teaching gate:** Seek fluent Asante and Akuapem reviewers plus educators before
new Twi built-ins, lessons or diagnostics are considered approved. Keep all core
learning content runnable without cloud accounts or subscriptions.

**Security gate:** Never run untrusted bytecode as if CRC32 or file validation were
sandboxing. Define OS access and resource quotas before processing external data.

## Independent verification status

On 2026-11-18 the repository's actual JavaScript runtime directly executed
four parameterized reconciliation scenarios, **4/4 passing** in an isolated V8
context. Python pytest, native executable and serialized KBC1 test cases are
registered but **not independently run on the full project revision here**.
This does not increase the 0.4 or 1.0 progress percentage.

The next action is to run the real local parity verifier and audit its JSON
report, then resolve observed discrepancies before designing a finance API.
