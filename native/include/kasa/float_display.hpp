#pragma once
// Kasa native binary64 display: Python-reference notation and shortest round-trip.
#include <charconv>
#include <cmath>
#include <stdexcept>
#include <string>
#include <system_error>

namespace kasa::numbers {
inline std::string displayFloat(double number) {
    if (!std::isfinite(number)) throw std::domain_error("Non-finite Kasa number");
    if (number == 0.0) return std::signbit(number) ? "-0.0" : "0.0";
    char buffer[128];
    const auto result = std::to_chars(buffer, buffer + sizeof(buffer), number,
                                      std::chars_format::scientific);
    if (result.ec != std::errc{}) throw std::runtime_error("Could not format Kasa number");
    const std::string encoded(buffer, result.ptr);
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
