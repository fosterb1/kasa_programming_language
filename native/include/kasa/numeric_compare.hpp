#pragma once
// Kasa's Python reference compares integers and binary64 decimals exactly.
// Never round an int64_t to double before doing a mixed-type comparison.
#include <cmath>
#include <cstdint>
#include <stdexcept>

namespace kasa::numbers {

// Return -1 when integer < decimal, 0 when equal, +1 when greater.
// Precondition: the decimal is a finite IEEE-754 binary64 value.
// The limit is exclusive for +2^63 and inclusive for -2^63.
inline int compareIntDouble(std::int64_t integer, double decimal) {
    if (!std::isfinite(decimal))
        throw std::domain_error("Non-finite decimal in numeric comparison");

    constexpr double twoTo63 = 0x1.0p63;
    if (decimal >= twoTo63) return -1;
    if (decimal < -twoTo63) return 1;

    // Conversion is defined here: -2^63 <= decimal < 2^63.
    const auto whole = static_cast<std::int64_t>(decimal);
    if (integer < whole) return -1;
    if (integer > whole) return 1;
    if (static_cast<double>(whole) == decimal) return 0;

    // The integer equals trunc(decimal), but decimal has a fractional part.
    return decimal > 0 ? -1 : 1;
}

}  // namespace kasa::numbers
