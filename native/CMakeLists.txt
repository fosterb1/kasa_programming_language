cmake_minimum_required(VERSION 3.16)
project(kasa_native VERSION 0.4.0 LANGUAGES CXX)
add_executable(kasa-native
    src/main.cpp
    src/lexer.cpp
    src/parser.cpp
    src/compiler.cpp
    src/bytecode.cpp
    src/vm.cpp
)
target_compile_features(kasa-native PRIVATE cxx_std_20)
target_include_directories(kasa-native PRIVATE include)
if(MSVC)
    target_compile_options(kasa-native PRIVATE /W4)
else()
    target_compile_options(kasa-native PRIVATE -Wall -Wextra -Wpedantic)
endif()
install(TARGETS kasa-native RUNTIME DESTINATION bin)

# A standalone lexer test executable: no VM, Python, or JavaScript required.
include(CTest)
if(BUILD_TESTING)
    add_executable(kasa-lexer-smoke src/lexer.cpp tests/lexer_smoke.cpp)
    target_compile_features(kasa-lexer-smoke PRIVATE cxx_std_20)
    target_include_directories(kasa-lexer-smoke PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-lexer-smoke PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-lexer-smoke PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME kasa_native_lexer_unicode COMMAND kasa-lexer-smoke)

    # Test portable KBC1 serialization without the compiler, VM or Python runtime.
    add_executable(kasa-kbc1-smoke src/bytecode.cpp tests/bytecode_smoke.cpp)
    target_compile_features(kasa-kbc1-smoke PRIVATE cxx_std_20)
    target_include_directories(kasa-kbc1-smoke PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-kbc1-smoke PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-kbc1-smoke PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME kasa_native_kbc1_serializer COMMAND kasa-kbc1-smoke)

    # Deterministic hostile-input mutation of the KBC1 loader; no VM execution.
    add_executable(kasa-kbc1-mutation-smoke src/bytecode.cpp tests/bytecode_mutation_smoke.cpp)
    target_compile_features(kasa-kbc1-mutation-smoke PRIVATE cxx_std_20)
    target_include_directories(kasa-kbc1-mutation-smoke PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-kbc1-mutation-smoke PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-kbc1-mutation-smoke PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME kasa_native_kbc1_mutation COMMAND kasa-kbc1-mutation-smoke)

    # Isolated numeric comparison check; no parser, compiler or VM required.
    add_executable(kasa-numeric-comparison-smoke tests/numeric_comparison_smoke.cpp)
    target_compile_features(kasa-numeric-comparison-smoke PRIVATE cxx_std_20)
    target_include_directories(kasa-numeric-comparison-smoke PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-numeric-comparison-smoke PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-numeric-comparison-smoke PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME kasa_numeric_comparison_exact COMMAND kasa-numeric-comparison-smoke)

    # Standalone shortest-round-trip binary64 display smoke; no VM dependency.
    add_executable(kasa-float-display-smoke tests/float_display_smoke.cpp)
    target_compile_features(kasa-float-display-smoke PRIVATE cxx_std_20)
    target_include_directories(kasa-float-display-smoke PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-float-display-smoke PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-float-display-smoke PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    add_test(NAME kasa_float_display_python_notation COMMAND kasa-float-display-smoke)

    # Native binary64 formatting differential: Python drives this executable.
    add_executable(kasa-float-display-probe tests/float_display_probe.cpp)
    target_compile_features(kasa-float-display-probe PRIVATE cxx_std_20)
    target_include_directories(kasa-float-display-probe PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-float-display-probe PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-float-display-probe PRIVATE -Wall -Wextra -Wpedantic)
    endif()

    # Python drives a reusable batch probe with 10,080 deterministic numeric
    # comparisons; unlike the fixed smoke it tests thousands of input pairs.
    add_executable(kasa-numeric-compare-probe tests/numeric_compare_probe.cpp)
    target_compile_features(kasa-numeric-compare-probe PRIVATE cxx_std_20)
    target_include_directories(kasa-numeric-compare-probe PRIVATE include)
    if(MSVC)
        target_compile_options(kasa-numeric-compare-probe PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-numeric-compare-probe PRIVATE -Wall -Wextra -Wpedantic)
    endif()
endif()
