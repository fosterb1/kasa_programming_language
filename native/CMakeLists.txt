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

# Experimental cpp_int VM: never alter the default alpha or KBC1 wire format.
option(KASA_ENABLE_BIGINT_VM "Enable experimental exact integers in native VM" OFF)
if(KASA_ENABLE_BIGINT_VM)
    find_path(KASA_BOOST_VM_INCLUDE boost/multiprecision/cpp_int.hpp)
    if(NOT KASA_BOOST_VM_INCLUDE)
        message(FATAL_ERROR "Kasa experimental bigint VM requires Boost.Multiprecision headers")
    endif()
    target_include_directories(kasa-native PRIVATE "${KASA_BOOST_VM_INCLUDE}")
    target_compile_definitions(kasa-native PRIVATE KASA_ENABLE_BIGINT_VM=1)
    if(BUILD_TESTING)
        find_package(Python3 COMPONENTS Interpreter REQUIRED)
        add_test(NAME kasa_bigint_vm_rfc0008_source_and_kbc1
                 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/tests/bigint_vm_conformance.py"
                         "$<TARGET_FILE:kasa-native>")
        # Verify byte-for-byte KBC2 cross-platform determinism against the
        # reviewed SHA256 golden manifest (never regenerates expected hashes).
        add_test(NAME kasa_kbc2_cross_platform_golden
                 COMMAND "${Python3_EXECUTABLE}" "${CMAKE_CURRENT_SOURCE_DIR}/../scripts/verify_kbc2_golden.py"
                         --binary "$<TARGET_FILE:kasa-native>")
    endif()
endif()

# Explicitly opt-in until the bigint representation is integrated with Value,
# VM instructions and a versioned KBC2. Never require Boost for the existing
# KBC1 or native alpha build.
option(KASA_BUILD_BIGINT_EXPERIMENT "Build experimental RFC-0008 bigint smoke" OFF)
if(KASA_BUILD_BIGINT_EXPERIMENT)
    find_path(KASA_BOOST_MULTIPRECISION_INCLUDE_DIR boost/multiprecision/cpp_int.hpp)
    if(NOT KASA_BOOST_MULTIPRECISION_INCLUDE_DIR)
        message(FATAL_ERROR "Bigint experiment requires Boost.Multiprecision headers (boost/multiprecision/cpp_int.hpp)")
    endif()
    add_executable(kasa-bigint-smoke tests/big_integer_smoke.cpp)
    target_compile_features(kasa-bigint-smoke PRIVATE cxx_std_20)
    target_include_directories(kasa-bigint-smoke PRIVATE include "${KASA_BOOST_MULTIPRECISION_INCLUDE_DIR}")
    if(MSVC)
        target_compile_options(kasa-bigint-smoke PRIVATE /W4 /utf-8)
    else()
        target_compile_options(kasa-bigint-smoke PRIVATE -Wall -Wextra -Wpedantic)
    endif()
    if(BUILD_TESTING)
        add_test(NAME kasa_bigint_rfc0008_experiment COMMAND kasa-bigint-smoke)
    endif()
endif()
