# G1.1 — experimental standard-library contract baseline

**Status:** Contract and reference-runtime fixtures on a development branch;
this does **not** promote G1 to the pinned G0 module catalog.

## Contract source

`tests/g1_contract_fixtures.json` names the **nine current G1 functions**,
their precise source files and 19 executable source/output cases. The
`tests/test_g1_contract.py` suite checks declarations against the actual Kasa
parser AST and executes each fixture with the Python reference interpreter.

| Library | Functions |
| --- | --- |
| `math` | `kasa_min_or`, `kasa_max_or`, `kasa_total`, `kasa_average_or`, `kasa_count_above` |
| `collections` | `kasa_first_index`, `kasa_last_index`, `kasa_count_distinct`, `kasa_all_equal` |

### Behavioral decisions

- Empty min/max and average lists return a **caller-provided fallback**.
- Empty total and distinct count return 0.
- Empty and one-element lists are considered all equal (`nokware`).
- Search indexes start at zero, and absent values return -1.
- Threshold comparison is **strictly greater than**, not greater-or-equal.
- Lists are not modified. The distinct-count algorithm is quadratic in the
  worst case, making it suitable for small educational datasets.
- Ordinary Kasa division and numeric limits still apply. This is **not**
  an exact decimal-money API. For accounting examples use integer pesewas.

### Cross-runtime readiness matrix

| Capability | Python reference | JS browser | Native C++ / KBC |
| --- | --- | --- | --- |
| G1 functions present as tracked pure-Kasa sources | Yes | Source exists, execution not established by this milestone | Source exists, execution not established by this milestone |
| 19 G1.1 source/output contract cases | Run with focused Python pytest | **Pending** shared-runner fixtures | **Pending** source/KBC tests |
| `fa math/collections firi stdlib` exposing G1 members | **No** | **No** | **No** |

**Do not change `stdlib/catalog.json` merely to make the new functions
appear importable.** G0 content hashes, allowlists, public exports and
bytecode rules are versioned constraints. The next milestone is a deliberate
G1 import/packaging design with real JS and native conformance evidence,
including all error and security boundaries.

## Local validation (Google Cloud Shell)

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/g11-stdlib-contract
source .venv/bin/activate
python -m pytest -q tests/test_g1_contract.py
python -m pytest -q tests/test_g1_numeric_analytics.py tests/test_g1_collection_analysis.py
python scripts/verify_local.py --profile full
```

Report revision, passes, failures and skips. Do not count merely writing
the fixtures as test execution. No Netlify deploy, G0.5 public security
claims or new Twi keywords.
