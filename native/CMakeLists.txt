cmake_minimum_required(VERSION 3.16)
project(kasa_native VERSION 0.3.0 LANGUAGES CXX)
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
endif()
