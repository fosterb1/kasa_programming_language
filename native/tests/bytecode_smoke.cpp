#include "kasa/native.hpp"
#include <chrono>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <limits>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

using namespace std;

static void require(bool ok, const string& explanation) {
    if(!ok) throw runtime_error(explanation);
}
static vector<unsigned char> readBytes(const filesystem::path& path) {
    ifstream in(path, ios::binary);
    require(bool(in), "Cannot read KBC1 smoke fixture");
    return {istreambuf_iterator<char>(in), istreambuf_iterator<char>()};
}
static void writeBytes(const filesystem::path& path, const vector<unsigned char>& data) {
    ofstream out(path, ios::binary | ios::trunc);
    require(bool(out), "Cannot write KBC1 smoke fixture");
    out.write(reinterpret_cast<const char*>(data.data()), static_cast<streamsize>(data.size()));
    require(bool(out), "Failed writing KBC1 smoke fixture");
}
static void expectInvalid(const filesystem::path& path, const string& diagnostic) {
    try {
        (void)kasa::readBytecode(path.string());
    } catch(const exception& error) {
        require(string(error.what()).find("Invalid KBC bytecode: " + diagnostic) != string::npos,
                "Unexpected validation error: " + string(error.what()));
        return;
    }
    throw runtime_error("Corrupt bytecode was accepted: " + diagnostic);
}

int main() {
    // Make each invocation independent, including concurrent local test runs.
    const auto serial=chrono::steady_clock::now().time_since_epoch().count();
    const filesystem::path folder=filesystem::temp_directory_path() /
        ("kasa-kbc1-smoke-" + to_string(serial));
    struct Cleanup {
        filesystem::path p;
        ~Cleanup() {
            error_code ec;
            filesystem::remove_all(p, ec);
        }
    } cleanup{folder};
    try {
        filesystem::create_directories(folder);
        auto code=make_shared<kasa::Chunk>();
        kasa::Instruction literal;
        literal.op=kasa::Op::Constant;
        literal.loc={"", "", 1, 1};
        literal.value=kasa::Value(string("Kasa"));
        code->code.push_back(literal);

        kasa::Instruction print;
        print.op=kasa::Op::Print;
        print.loc={"", "", 1, 4};
        code->code.push_back(print);

        const auto first=folder/"first.kbc";
        const auto second=folder/"second.kbc";
        const auto tampered=folder/"corrupt.kbc";
        kasa::writeBytecode(code,first.string());
        kasa::writeBytecode(code,second.string());

        const auto original=readBytes(first);
        require(original==readBytes(second),"Output is not deterministic");
        require(original.size()>20 && original[0]=='K' && original[1]=='B' &&
                original[2]=='C' && original[3]=='1',"KBC1 magic missing");

        auto restored=kasa::readBytecode(first.string());
        require(restored && restored->code.size()==2,"Bytecode round-trip size mismatch");
        require(restored->code[0].op==kasa::Op::Constant &&
                restored->code[1].op==kasa::Op::Print,"Bytecode opcodes changed");
        const auto* text=get_if<string>(&restored->code[0].value.data);
        require(text && *text=="Kasa","Literal changed after serialization");
        cout<<"PASS deterministic KBC1 round-trip\n";

        auto wrongMagic=original;wrongMagic[0]='X';
        writeBytes(tampered,wrongMagic);expectInvalid(tampered,"wrong magic");
        cout<<"PASS magic validation\n";

        auto wrongVersion=original;wrongVersion[4]=2;
        writeBytes(tampered,wrongVersion);expectInvalid(tampered,"unsupported version");
        cout<<"PASS version validation\n";

        auto wrongChecksum=original;wrongChecksum.back()^=1;
        writeBytes(tampered,wrongChecksum);expectInvalid(tampered,"checksum mismatch");
        cout<<"PASS checksum rejection\n";

        // The writer must not emit a file the reader will reject.
        const auto invalidFloatPath=folder/"invalid-float.kbc";
        auto rejectNonFinite = [&](double value, const string& label) {
            auto bad=make_shared<kasa::Chunk>(*code);
            bad->code.front().value=kasa::Value(value);
            try {
                kasa::writeBytecode(bad, invalidFloatPath.string());
            } catch(const exception& error) {
                require(string(error.what()).find("Invalid KBC bytecode: non-finite constant") != string::npos,
                        "Unexpected error when rejecting " + label + ": " + error.what());
                require(!filesystem::exists(invalidFloatPath), "Writer created invalid bytecode for " + label);
                return;
            }
            throw runtime_error("Writer incorrectly accepted " + label);
        };
        rejectNonFinite(numeric_limits<double>::quiet_NaN(), "NaN");
        rejectNonFinite(numeric_limits<double>::infinity(), "infinity");
        cout<<"PASS non-finite floating-point writer rejection\n";

        cout<<"5/5 KBC1 standalone smoke checks passed\n";
        return 0;
    } catch(const exception& error) {
        cerr<<"KBC1 smoke test failed: "<<error.what()<<"\n";
        return 1;
    }
}
