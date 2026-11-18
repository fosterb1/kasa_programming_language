// Deterministic batch probe for exact int64-versus-binary64 comparisons.
// The Python differential harness drives this executable; it is not a VM.
#include "kasa/numeric_compare.hpp"
#include <cerrno>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <string>

int main() {
    std::int64_t integer = 0;
    std::string decimal_text;
    while (std::cin >> integer >> decimal_text) {
        char* end = nullptr;
        const double decimal = std::strtod(decimal_text.c_str(), &end);
        if (end == decimal_text.c_str() || !end || *end != '\0') {
            std::cerr << "Invalid decimal test input\n";
            return 2;
        }
        try {
            std::cout << kasa::numbers::compareIntDouble(integer, decimal) << '\n';
        } catch (const std::exception& error) {
            std::cerr << "Comparison failed: " << error.what() << '\n';
            return 2;
        }
    }
    if (!std::cin.eof()) {
        std::cerr << "Invalid integer test input\n";
        return 2;
    }
    return 0;
}
