#pragma once
// Experimental arbitrary-precision integer operations for RFC-0008.
// Not wired into native Value, the VM, or KBC1 yet.
#include <boost/multiprecision/cpp_int.hpp>
#include <cctype>
#include <cstddef>
#include <stdexcept>
#include <string>
#include <string_view>

namespace kasa::bigint {
using Integer = boost::multiprecision::cpp_int;
inline constexpr std::size_t kMaxBits = 16'384;
inline constexpr std::size_t kMaxLiteralDigits = 1'000;

class SizeLimit : public std::runtime_error {
public:
    explicit SizeLimit(const char* message) : std::runtime_error(message) {}
};
inline std::size_t bits(const Integer& number) {
    if(number == 0) return 0;
    Integer magnitude = number < 0 ? -number : number;
    return static_cast<std::size_t>(boost::multiprecision::msb(magnitude)) + 1;
}
inline void check(const Integer& number) {
    if(bits(number) > kMaxBits) throw SizeLimit("Integer exceeds supported size limit");
}
inline Integer decimal(std::string_view text) {
    if(text.empty()) throw std::invalid_argument("Empty integer literal");
    std::size_t start = (text.front() == '+' || text.front() == '-') ? 1 : 0;
    if(start == text.size() || text.size() - start > kMaxLiteralDigits)
        throw SizeLimit("Integer literal exceeds digit limit");
    Integer result = 0;
    for(std::size_t i = start; i < text.size(); ++i) {
        const char digit = text[i];
        if(digit < '0' || digit > '9') throw std::invalid_argument("Invalid integer literal");
        result *= 10;
        result += digit - '0';
    }
    if(start && text.front() == '-') result = -result;
    check(result);
    return result;
}
inline Integer add(const Integer& a, const Integer& b) {
    check(a); check(b);
    Integer r = a + b; check(r); return r;
}
inline Integer subtract(const Integer& a, const Integer& b) {
    check(a); check(b);
    Integer r = a - b; check(r); return r;
}
inline Integer multiply(const Integer& a, const Integer& b) {
    check(a); check(b);
    // Bound estimated result before allocating a full-size product. Some
    // products are one bit shorter than this estimate; use the actual result
    // check for the final decision.
    if(bits(a) && bits(b) && bits(a) + bits(b) - 1 > kMaxBits)
        throw SizeLimit("Integer multiplication exceeds size limit");
    Integer r = a * b; check(r); return r;
}
inline Integer floorRemainder(const Integer& a, const Integer& b) {
    check(a); check(b);
    if(b == 0) throw std::domain_error("Division by zero");
    Integer r = a % b;
    if(r != 0 && ((r < 0) != (b < 0))) r += b;
    check(r);
    return r;
}
} // namespace kasa::bigint
