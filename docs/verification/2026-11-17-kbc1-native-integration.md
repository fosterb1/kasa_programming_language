# Kasa 0.4 — Independent native compiler and KBC1 integration verification

**Date:** 2026-11-17  
**Status:** Native C++20 compiler, disk bytecode loader and VM **passed focused complete-build tests** after a memory-leak fix. **Not** a stable 1.0 or security certification.  
**Review:** [PR #16](https://github.com/fosterb1/kasa_programming_language/pull/16)  
**Testing:** Independent Linux toolchain. GitHub Actions **not used**.

## Tested components and provenance

The full native source tree was reconstructed in a local isolated checkout. The byte content of each reconstructed source file was verified against the corresponding GitHub **Git-blob SHA-1** before compilation.

| PR #16 file | Git blob SHA-1 verified |
| --- | --- |
| `native/src/main.cpp` | `306af4e67945027861437cdfd826de74a1932ca0` |
| `native/src/lexer.cpp` | `7ae64d52aa9db383e7cac18e40081c439c30f1f7` |
| `native/src/parser.cpp` | `594d0cbebee7e831b597264d3b0113ef1fb434b1` |
| `native/src/compiler.cpp` | `ad4244d0acc8e4dcccfc03158c0c78d1fc7cb9c3` |
| `native/src/bytecode.cpp` | `acd7aefb80653694a4ef2d3bbc271e6e0bb590fe` |
| `native/src/vm.cpp` (after leak fix) | `887af9f16d28785a9448772c985b6de4c97842be` |
| `native/include/kasa/native.hpp` | `0afbe95d525fc98a75820198945f19862eb85717` |
| `native/CMakeLists.txt` | `8800fd7893a9e0b3612ba154cc9bebdf7c45cd5a` |
| `native/tests/test_bytecode.py` (after closure regression) | `886d567224d7293f6ff31f501c123b2eaaac66e8` |

All **ten bundled Kasa examples** (nine `examples/*.kasa`, one `native/examples/*.kasa`) were also verified against their respective Git blob hashes.

A Git-blob SHA is reproducibility information, **not a software signature or independent attestation**.

## Environment

- Linux x86-64
- GNU **g++ 14.2.0**
- LLVM **clang++ 17.0.0**
- Python **3.13.5** used for test harnesses
- CMake with GNU 14.2 toolchain
- No GitHub Actions, paid CI, deployed server or external sandbox service.

## Commands and observed verification

For a **complete Kasa checkout** with C++20 toolchains:

```bash
cmake -S native -B build/kasa-integration -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTING=OFF
cmake --build build/kasa-integration --parallel 2
python native/tests/test_bytecode.py build/kasa-integration/kasa-native

# Equivalent independent strict GCC and Clang C++20 builds
g++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I native/include native/src/{main,lexer,parser,compiler,bytecode,vm}.cpp -o kasa-native
clang++ -std=c++20 -O2 -Wall -Wextra -Wpedantic -Werror \
  -I native/include native/src/{main,lexer,parser,compiler,bytecode,vm}.cpp -o kasa-native-clang
python native/tests/test_bytecode.py ./kasa-native
python native/tests/test_bytecode.py ./kasa-native-clang

# Leak and undefined-behavior instrumentation (GNU)
g++ -std=c++20 -O1 -g -Wall -Wextra -Wpedantic -Werror \
  -fsanitize=address,undefined -fno-omit-frame-pointer \
  -I native/include native/src/{main,lexer,parser,compiler,bytecode,vm}.cpp -o kasa-native-asan
ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 \
  python native/tests/test_bytecode.py ./kasa-native-asan
```

The CMake command above deliberately uses `BUILD_TESTING=OFF` in the staged checkout because not every CTest source was reconstructed there. The **entire six-file native compiler/VM executable did compile and link**, not just the serializer component. CTest registration and full-repository Python/Node/WASM suites must be checked separately.

### Actual results (all post-fix)

| Check | Result |
| --- | --- |
| Full CMake native executable configure/build | **Passed** |
| GNU g++ strict C++20 full native compiler | **Passed** |
| Clang strict C++20 full native compiler | **Passed** |
| Source → KBC1 → VM smoke (compared with direct source output) | **Passed** |
| KBC1 Python-driven adversarial suite via GCC | **14/14 passed** |
| Same suite via Clang | **14/14 passed** |
| Same suite via ASan + UBSan GNU native binary | **14/14 passed**, no sanitizer errors reported |
| Nine root native example outputs vs published JavaScript expected outputs | **9/9 matched** |
| Standalone KBC1 serializer under strict C++20 | **7/7 passed** |
| Standalone KBC1 serializer under ASan + UBSan | **7/7 passed** |

The 14 grouped bytecode tests include all ten bundled program round-trips, valid input, deterministic output, corrupted/truncated files, invalid signatures/versions/flags/opcodes/Boolean constants/jump targets/stack underflow, oversized files, missing files, and source-path overwrite aliases. The new 14th group checks an **escaping lexical closure** and its captured state after source compilation and KBC1 loading.

## Discoveries made during this milestone

### 1. Writer/reader limits were inconsistent — fixed

The KBC1 writer could accept source-coordinate values larger than the loader permits and could individually validate chunks while exceeding the loader's **aggregate** 100,000-instruction limit across nested functions.

**Correction:** Enforce the loader's source-coordinate ceilings and global nested-instruction budget in `verifyChunk()` before serialization. Expanded standalone KBC1 smoke tests from five to **seven groups**, both passing under normal and sanitizer builds.

### 2. Sanitizer exposed a genuine reference cycle — fixed

**Initial failure:** Although ordinary GCC/Clang bytecode tests passed **13/13**, the full native ASan/LSan run failed on programs defining functions, reporting indirect memory leaks. This was a **real failed test**, not an infrastructure outage.

**Root cause:** `Environment::values` owns `Function` values, and `Function::closure` holds a shared pointer back to the environment. Function declarations and lexical closures can create cycles that normal reference counting cannot reclaim.

**Correction:** The VM tracks created environments with **weak references** and clears their captured values at VM destruction, after program execution finishes, including after exceptions. This breaks reference cycles while preserving captured variables and escaping closures throughout execution.

**Regression:** Added `test_escaping_lexical_closure_roundtrip`; it returns a function from an outer function, then calls it after the outer call has returned. Expected output: `18`. The source-compiled and file-compiled paths both pass.

**Post-fix result:** Full native suite **14/14 passed** with LeakSanitizer/AddressSanitizer/UndefinedBehaviorSanitizer enabled; no leaks were reported in this targeted suite.

**Tradeoff:** The VM keeps weak references to environments for cleanup. A bounded memory/resource profiling and more comprehensive closure-cycle tests are still warranted.

### 3. Serialization must reject non-finite numbers — previously fixed

The earlier standalone test found that the writer emitted `NaN` even though the loader rejected it. Both now reject `NaN` and infinity. See [serializer smoke and mutation record](./2026-11-17-kbc1-serializer-smoke.md).

## Remaining gates

1. Full Python reference and native-vs-Python conformance suite on the same commit (**not independently run in this reconstructed checkout**).
2. Full repository Node/WASM browser and all CTest targets with `BUILD_TESTING=ON`.
3. Windows/macOS compiler portability, installation and packaged binary tests.
4. Bytecode security and authenticity: CRC32 detects accidental corruption but **is not a signature**; bytecode structural validation is **not** a sandbox for hostile execution.
5. Linguistic human review and license selection before a stable educational release.

**Conclusion:** The native KBC1 alpha implementation has now passed meaningful end-to-end independent compiler/VM and adversarial verification. It is appropriate to integrate as an **experimental alpha feature with the above explicit limitations**, not advertise a stable or security-certified file format.
