#include "kasa/native.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
using namespace std;
using namespace kasa;
int main(int argc,char **argv){
    if(argc==2&&string(argv[1])=="--version"){cout<<"Kasa Native 0.3.0-alpha (C++20 bytecode VM)\n";return 0;}
    if(argc!=3||!(string(argv[1])=="run"||string(argv[1])=="check"||string(argv[1])=="disasm")){
        cerr<<"Usage: kasa-native run|check|disasm file.kasa\n       kasa-native --version\n";return 2;
    }
    const string file=argv[2];ifstream stream(file,ios::binary);
    if(!stream){cerr<<"kasa-native: cannot open "<<file<<"\n";return 2;}
    string source((istreambuf_iterator<char>(stream)),istreambuf_iterator<char>());
    if(source.size()>1'000'000){cerr<<file<<":1:1: ResourceError: Source file is too large\n";return 1;}
    try{
        auto tokens=lex(source,file);auto statements=parseSource(move(tokens),file);
        auto code=compileProgram(statements,file);
        if(string(argv[1])=="check")return 0;
        if(string(argv[1])=="disasm"){disasm(code,cout);return 0;}
        runProgram(code,file,cout,cin);return 0;
    }catch(const Failure&e){cerr<<e.what()<<"\n";return 1;}
     catch(const exception&e){cerr<<file<<": InternalError: "<<e.what()<<"\n";return 1;}
}
