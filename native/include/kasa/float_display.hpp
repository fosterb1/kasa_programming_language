#pragma once
// Kasa native binary64 display: Python-reference notation and shortest round-trip.
#include <charconv>
#include <bit>
#include <cstdint>
#include <iomanip>
#include <locale>
#include <sstream>
#include <cmath>
#include <stdexcept>
#include <string>
#include <system_error>

namespace kasa::numbers {
inline std::string displayFloat(double number) {
    if (!std::isfinite(number)) throw std::domain_error("Non-finite Kasa number");
    if (number == 0.0) return std::signbit(number) ? "-0.0" : "0.0";
    std::string encoded;
#if defined(__APPLE__) && defined(_LIBCPP_VERSION)
    // Apple's older libc++ (including the Ventura/Apple Clang 14 SDK) declares
    // floating-point std::to_chars unavailable, despite C++20 support.
    // Instead, find the minimum significant decimal digits that round-trip
    // through binary64. Use the classic locale so commas cannot enter Kasa
    // numeric output. Keep std::to_chars on platforms that support it.
    //
    // The differential test compares this branch with Python's repr over
    // thousands of deterministic IEEE-754 bit patterns on a real Mac.
    bool found = false;
    for (int digits = 1; digits <= 17; ++digits) {
        std::ostringstream out;
        out.imbue(std::locale::classic());
        out << std::scientific << std::setprecision(digits - 1) << number;
        const std::string candidate = out.str();
        std::istringstream in(candidate);
        in.imbue(std::locale::classic());
        double decoded = 0.0;
        in >> decoded;
        if (in && in.peek() == std::char_traits<char>::eof() &&
            std::bit_cast<std::uint64_t>(decoded) ==
                std::bit_cast<std::uint64_t>(number)) {
            encoded = candidate;
            found = true;
            break;
        }
    }
    if (!found) throw std::runtime_error("Could not format Kasa number");
#else
    char buffer[128];
    const auto result = std::to_chars(buffer, buffer + sizeof(buffer), number,
                                      std::chars_format::scientific);
    if (result.ec != std::errc{}) throw std::runtime_error("Could not format Kasa number");
    encoded.assign(buffer, result.ptr);
#endif
    const std::size_t marker = encoded.find('e');
    if (marker == std::string::npos) throw std::runtime_error("Malformed numeric encoding");
    const int exponent = std::stoi(encoded.substr(marker + 1));
    const std::string mantissa = encoded.substr(0, marker);
    if (exponent < -4 || exponent >= 16) {
        const std::string magnitude = std::to_string(std::abs(exponent));
        return mantissa + "e" + (exponent < 0 ? "-" : "+") +
               (magnitude.size() < 2 ? "0" : "") + magnitude;
    }
    const bool negative = mantissa[0] == '-';
    const std::string unsignedMantissa = negative ? mantissa.substr(1) : mantissa;
    std::string digits;
    for (const char c : unsignedMantissa) if (c != '.') digits += c;
    const int decimalPos = exponent + 1;
    std::string fixed;
    if (decimalPos <= 0)
        fixed = "0." + std::string(static_cast<std::size_t>(-decimalPos), '0') + digits;
    else if (static_cast<std::size_t>(decimalPos) >= digits.size())
        fixed = digits + std::string(static_cast<std::size_t>(decimalPos) - digits.size(), '0') + ".0";
    else
        fixed = digits.substr(0, static_cast<std::size_t>(decimalPos)) + "." +
                digits.substr(static_cast<std::size_t>(decimalPos));
    return negative ? "-" + fixed : fixed;
}
} // namespace kasa::numbers
