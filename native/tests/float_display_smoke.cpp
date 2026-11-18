#include "kasa/float_display.hpp"
#include <cstdint>
#include <iostream>
#include <limits>
#include <string>
#include <vector>
struct Case {const char* name;double input;const char* expected;};
int main(){const std::vector<Case> cases={
{"one seventh",1.0/7.0,"0.14285714285714285"},
{"one millionth",1.0/1000000.0,"1e-06"},
{"one ten millionth",1.0/10000000.0,"1e-07"},
{"small scientific",1.0/100000.0,"1e-05"},
{"fixed lower boundary",0.0001,"0.0001"},
{"fixed upper boundary",1e15,"1000000000000000.0"},
{"scientific upper boundary",1e16,"1e+16"},
{"large exponent",1e20,"1e+20"},
{"small fractional coefficient",0.0000123,"1.23e-05"},
{"large fractional coefficient",1.23e16,"1.23e+16"},
{"negative small",-1e-7,"-1e-07"},
{"negative zero",-0.0,"-0.0"},
{"positive zero",0.0,"0.0"},
{"subnormal",std::numeric_limits<double>::denorm_min(),"5e-324"},
{"exact fractional",1.2345678901234567,"1.2345678901234567"},
{"negative fixed fraction",-0.5,"-0.5"},
{"scientific 3-digit exponent",1e100,"1e+100"},
{"tiny scientific exponent",1e-100,"1e-100"}
};int passed=0;for(const auto& c:cases){auto got=kasa::numbers::displayFloat(c.input);if(got==c.expected)++passed;else std::cerr<<"FAIL "<<c.name<<" expected "<<c.expected<<" got "<<got<<'\n';}std::cout<<passed<<'/'<<cases.size()<<" native decimal display checks passed\n";return passed==static_cast<int>(cases.size())?0:1;}
