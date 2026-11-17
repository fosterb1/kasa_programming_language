#include "kasa/native.hpp"
#include <chrono>
#include <cstdint>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <iterator>
#include <random>
#include <stdexcept>
#include <string>
#include <system_error>
#include <vector>

using namespace std;

static vector<uint8_t> readAll(const filesystem::path& path) {
    ifstream in(path, ios::binary);
    if (!in) throw runtime_error("Cannot read mutation test file");
    return {istreambuf_iterator<char>(in), istreambuf_iterator<char>()};
}
static void writeAll(const filesystem::path& path, const vector<uint8_t>& bytes) {
    ofstream out(path, ios::binary|ios::trunc);
    if (!out) throw runtime_error("Cannot write mutation test file");
    out.write(reinterpret_cast<const char*>(bytes.data()), static_cast<streamsize>(bytes.size()));
    if (!out) throw runtime_error("Failed writing mutation test file");
}
static void refreshChecksum(vector<uint8_t>& bytes) {
    uint32_t crc=0xffffffffu;
    for (size_t i=16; i<bytes.size(); ++i) {
        crc ^= bytes[i];
        for (int bit=0; bit<8; ++bit)
            crc=(crc>>1)^((crc&1u)?0xedb88320u:0u);
    }
    crc ^= 0xffffffffu;
    for (int i=0; i<4; ++i)
        bytes[12+i]=static_cast<uint8_t>(crc>>(8*i));
}
int main() {
    // This tests parser robustness, NOT authenticity or permission to execute bytecode.
    const auto serial=chrono::steady_clock::now().time_since_epoch().count();
    const auto folder=filesystem::temp_directory_path()/
        ("kasa-kbc1-mutations-"+to_string(serial));
    struct Cleanup {
        filesystem::path path;
        ~Cleanup() { error_code ec; filesystem::remove_all(path,ec); }
    } cleanup{folder};
    try {
        filesystem::create_directories(folder);
        auto code=make_shared<kasa::Chunk>();
        kasa::Instruction literal;
        literal.op=kasa::Op::Constant;
        literal.loc={"","",1,1};
        literal.value=kasa::Value(string("Kasa ɔ!"));
        code->code.push_back(literal);
        kasa::Instruction print;
        print.op=kasa::Op::Print;
        print.loc={"","",1,4};
        code->code.push_back(print);
        const auto originalPath=folder/"original.kbc";
        const auto changedPath=folder/"changed.kbc";
        kasa::writeBytecode(code,originalPath.string());
        auto original=readAll(originalPath);
        if (original.size()<=16) throw runtime_error("Serialized payload is empty");
        (void)kasa::readBytecode(originalPath.string());

        mt19937_64 random(0x1acaba35ull); // deterministic, reproducible mutations
        int rejected=0,accepted=0;
        for (int i=0; i<2000; ++i) {
            auto bytes=original;
            const size_t position=16+static_cast<size_t>(random()%(bytes.size()-16));
            bytes[position]^=static_cast<uint8_t>(1u<<(random()%8));
            refreshChecksum(bytes);
            writeAll(changedPath,bytes);
            try {
                (void)kasa::readBytecode(changedPath.string());
                ++accepted; // Some mutated programs remain structurally valid.
            } catch(const exception&) {
                ++rejected;
            }
        }
        if (rejected==0 || accepted+rejected!=2000)
            throw runtime_error("Mutation coverage incomplete");
        cout<<"PASS 2000 checksum-adjusted KBC1 mutations handled: "
            <<rejected<<" rejected, "<<accepted<<" structurally accepted\n";
        return 0;
    } catch(const exception& error) {
        cerr<<"KBC1 mutation smoke failed: "<<error.what()<<"\n";
        return 1;
    }
}
