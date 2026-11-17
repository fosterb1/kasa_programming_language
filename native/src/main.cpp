#include "kasa/native.hpp"
#include <fstream>
#include <iostream>
#include <iterator>
#include <utility>
using namespace std;
using namespace kasa;

int main(int argc, char **argv) {
    if (argc==2 && string(argv[1])=="--version") {
        cout << "Kasa Native 0.4.0-alpha (C++20 VM; experimental KBC1)\n";
        return 0;
    }
    if (argc<3) {
        cerr << "Usage: kasa-native run|check|disasm file.kasa\n"
             << "       kasa-native compile file.kasa [-o file.kbc]\n"
             << "       kasa-native run-bytecode|check-bytecode|disasm-bytecode file.kbc\n";
        return 2;
    }
    string mode=argv[1], file=argv[2];
    bool loading=(mode=="run-bytecode"||mode=="check-bytecode"||mode=="disasm-bytecode");
    bool compiling=mode=="compile";
    if (loading && argc!=3) { cerr<<"Unexpected arguments to "<<mode<<"\n";return 2; }
    if (compiling && !(argc==3 || (argc==5 && string(argv[3])=="-o"))) {
        cerr << "Usage: kasa-native compile file.kasa [-o file.kbc]\n";return 2;
    }
    if (!loading && !compiling && (!(mode=="run"||mode=="check"||mode=="disasm")||argc!=3)) {
        cerr << "Unknown command or argument count: "<<mode<<"\n";return 2;
    }
    try {
        shared_ptr<Chunk> code;
        if (loading) {
            code=readBytecode(file); // Includes checksum + control-flow verifier.
        } else {
            ifstream stream(file,ios::binary);
            if(!stream){cerr<<"kasa-native: cannot open "<<file<<"\n";return 2;}
            string source((istreambuf_iterator<char>(stream)),istreambuf_iterator<char>());
            if(source.size()>1'000'000){cerr<<file<<":1:1: ResourceError: Source file is too large\n";return 1;}
            auto tokens=lex(source,file);
            auto statements=parseSource(std::move(tokens),file);
            code=compileProgram(statements,file);
        }
        if (compiling) {
            string output;
            if (argc==5)output=argv[4];
            else {output=file;auto pos=output.find_last_of('.');auto sep=output.find_last_of("/\\");if(pos!=string::npos && (sep==string::npos || pos>sep))output.resize(pos);output+=".kbc";}
            if(output==file){cerr<<"Refusing to overwrite source file\n";return 2;}
            writeBytecode(code,output);
            cout<<"Compiled "<<file<<" -> "<<output<<"\n";
            return 0;
        }
        if(mode=="check"||mode=="check-bytecode")return 0;
        if(mode=="disasm"||mode=="disasm-bytecode"){disasm(code,cout);return 0;}
        runProgram(code,file,cout,cin);
        return 0;
    }catch(const Failure&e){cerr<<e.what()<<"\n";return 1;}
     catch(const exception&e){cerr<<file<<": "<<e.what()<<"\n";return 1;}
}
