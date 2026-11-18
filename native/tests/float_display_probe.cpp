#include "kasa/float_display.hpp"
#include <bit>
#include <cstdint>
#include <iostream>
#include <string>
int main(){std::string token;while(std::cin>>token){try {auto bits=std::stoull(token,nullptr,16);const double value=std::bit_cast<double>(static_cast<std::uint64_t>(bits));std::cout<<kasa::numbers::displayFloat(value)<<'\n';}catch(const std::exception&){std::cout<<"ERROR\n";}}}
