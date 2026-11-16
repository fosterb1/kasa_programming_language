cmake_minimum_required(VERSION 3.16)
project(kasa_native VERSION 0.3.0 LANGUAGES CXX)
add_executable(kasa-native
    src/main.cpp
    src/lexer.cpp
    src/parser.cpp
    src/compiler.cpp
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
