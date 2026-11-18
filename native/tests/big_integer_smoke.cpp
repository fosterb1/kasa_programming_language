// RFC-0008 experimental native bigint library smoke. Not KBC1/VM parity yet.
#include "kasa/big_integer.hpp"
#include <cassert>
#include <stdexcept>
#include <string>
using namespace kasa::bigint;

template <typename Error, typename Action>
void expectError(Action action) {
    bool thrown = false;
    try { action(); }
    catch(const Error&) { thrown = true; }
    assert(thrown);
}
int main() {
    const auto maximum = decimal("9223372036854775807");
    assert(add(maximum, decimal("1")).convert_to<std::string>() == "9223372036854775808");
    assert(subtract(decimal("-9223372036854775808"), decimal("1")).convert_to<std::string>() == "-9223372036854775809");
    assert(multiply(decimal("18446744073709551616"), decimal("18446744073709551616")).convert_to<std::string>()
           == "340282366920938463463374607431768211456");
    assert(floorRemainder(decimal("-18446744073709551617"), decimal("7")) == 4);
    assert(floorRemainder(decimal("18446744073709551617"), decimal("-7")) == -4);
    assert(floorRemainder(decimal("-5"), decimal("-3")) == -2);
    assert(decimal("-00000") == 0);
    assert(bits(decimal("-9223372036854775808")) == 64);
    expectError<std::invalid_argument>([] { (void)decimal("1e3"); });
    expectError<std::invalid_argument>([] { (void)decimal("1 2"); });
    expectError<SizeLimit>([] { (void)decimal(std::string(1001, '9')); });
    Integer edge = Integer(1) << 16383;
    check(edge);
    expectError<SizeLimit>([&] { (void)add(edge, edge); });
    expectError<SizeLimit>([&] { (void)multiply(edge, Integer(2)); });
    assert(floorRemainder(decimal("-7"), decimal("3")) == 2);
    expectError<std::domain_error>([] { (void)floorRemainder(decimal("8"), Integer(0)); });
    return 0;
}
