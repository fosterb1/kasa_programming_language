#include "kasa/numeric_compare.hpp"
#include <cstdint>
#include <iostream>
#include <limits>
#include <stdexcept>
#include <string>
#include <vector>

struct Case { const char* name; std::int64_t integer; double decimal; int expected; };

int main() {
    using kasa::numbers::compareIntDouble;
    const std::vector<Case> tests{
        {"integer beyond 2^53", 9007199254740993LL, 9007199254740992.0, 1},
        {"equal integer at 2^53", 9007199254740992LL, 9007199254740992.0, 0},
        {"negative integer beyond 2^53", -9007199254740993LL, -9007199254740992.0, -1},
        {"negative equal near 2^53", -9007199254740992LL, -9007199254740992.0, 0},
        {"maximum int64 below 2^63", INT64_MAX, 0x1.0p63, -1},
        {"minimum int64 equals -2^63", INT64_MIN, -0x1.0p63, 0},
        {"int64 above -2^63", INT64_MIN + 1, -0x1.0p63, 1},
        {"positive fractional decimal", 0, 0.5, -1},
        {"negative fractional decimal", 0, -0.5, 1},
        {"positive decimal below integer", 2, 1.5, 1},
        {"negative decimal above integer", -2, -1.5, -1},
        {"subnormal decimal", 0, std::numeric_limits<double>::denorm_min(), -1},
        {"negative zero", 0, -0.0, 0},
        {"large positive finite decimal", INT64_MAX, 1.0e300, -1},
        {"large negative finite decimal", INT64_MIN, -1.0e300, 1},
        {"small equal integer and decimal", 15, 15.0, 0},
    };
    int passed = 0;
    for (const auto& item : tests) {
        const int actual = compareIntDouble(item.integer, item.decimal);
        if (actual == item.expected) ++passed;
        else std::cerr << "FAIL " << item.name << ": expected " << item.expected << ", got " << actual << "\n";
    }
    const std::vector<double> invalid{
        std::numeric_limits<double>::quiet_NaN(),
        std::numeric_limits<double>::infinity()
    };
    for (const double decimal : invalid) {
        bool rejected = false;
        try { (void)compareIntDouble(1, decimal); }
        catch (const std::domain_error&) { rejected = true; }
        if (rejected) ++passed;
        else std::cerr << "FAIL non-finite numeric comparison was accepted\n";
    }
    const int total = static_cast<int>(tests.size() + invalid.size());
    std::cout << passed << "/" << total << " exact numeric comparison checks passed\n";
    return passed == total ? 0 : 1;
}
