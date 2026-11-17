#include "kasa/native.hpp"
#include <bit>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <limits>
#include <queue>
#include <set>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <vector>

namespace kasa {
namespace {
constexpr uint32_t kMaxPayload = 8'000'000;
constexpr uint32_t kMaxInstructions = 100'000;
constexpr uint32_t kMaxText = 1'000'000;
constexpr uint32_t kMaxName = 4096;
constexpr int kMaxNesting = 48;
constexpr int kMaxStack = 10'000;
constexpr uint8_t kLastOpcode = static_cast<uint8_t>(Op::CountCheck);

[[noreturn]] void invalid(const std::string &why) {
    throw std::runtime_error("Invalid KBC bytecode: " + why);
}
uint32_t crc32(const std::vector<uint8_t>& data) {
    uint32_t crc = 0xffffffffu;
    for (uint8_t b : data) {
        crc ^= b;
        for (int i = 0; i < 8; ++i) crc = (crc >> 1) ^ ((crc & 1u) ? 0xedb88320u : 0u);
    }
    return crc ^ 0xffffffffu;
}
class Writer {
public:
    std::vector<uint8_t> buf;
    void u8(uint8_t n) { buf.push_back(n); }
    void u16(uint16_t n) { for (int i = 0; i < 2; ++i) u8(static_cast<uint8_t>(n >> (8 * i))); }
    void u32(uint32_t n) { for (int i = 0; i < 4; ++i) u8(static_cast<uint8_t>(n >> (8 * i))); }
    void u64(uint64_t n) { for (int i = 0; i < 8; ++i) u8(static_cast<uint8_t>(n >> (8 * i))); }
    void str(const std::string& s) {
        if (s.size() > kMaxText) invalid("string too long");
        u32(static_cast<uint32_t>(s.size()));
        buf.insert(buf.end(), s.begin(), s.end());
    }
};
class Reader {
    const std::vector<uint8_t>& bytes;
    size_t pos;
    size_t finish;
public:
    Reader(const std::vector<uint8_t>& b, size_t start, size_t end): bytes(b), pos(start), finish(end) {}
    uint8_t u8() { if (pos >= finish) invalid("truncated input"); return bytes[pos++]; }
    uint16_t u16() { uint16_t n = 0; for(int i=0;i<2;++i)n |= static_cast<uint16_t>(u8()) << (8*i); return n; }
    uint32_t u32() { uint32_t n = 0; for(int i=0;i<4;++i)n |= static_cast<uint32_t>(u8()) << (8*i); return n; }
    uint64_t u64() { uint64_t n = 0; for(int i=0;i<8;++i)n |= static_cast<uint64_t>(u8()) << (8*i); return n; }
    std::string str(uint32_t maximum = kMaxText) {
        auto n = u32();
        if (n > maximum || n > finish - pos) invalid("invalid string length");
        auto result = std::string(bytes.begin() + static_cast<ptrdiff_t>(pos), bytes.begin() + static_cast<ptrdiff_t>(pos + n));
        pos += n;
        return result;
    }
    bool done() const { return pos == finish; }
};
void writeValue(Writer& w, const Value& value) {
    if (std::holds_alternative<std::monostate>(value.data)) w.u8(0);
    else if (const auto* n = std::get_if<int64_t>(&value.data)) { w.u8(1); w.u64(std::bit_cast<uint64_t>(*n)); }
    else if (const auto* n = std::get_if<double>(&value.data)) { if (!std::isfinite(*n)) invalid("non-finite constant"); w.u8(2); w.u64(std::bit_cast<uint64_t>(*n)); }
    else if (const auto* s = std::get_if<std::string>(&value.data)) { w.u8(3); w.str(*s); }
    else if (const auto* b = std::get_if<bool>(&value.data)) { w.u8(4); w.u8(*b ? 1 : 0); }
    else invalid("unsupported constant type");
}
Value readValue(Reader& r) {
    switch (r.u8()) {
    case 0: return Value{};
    case 1: return Value(std::bit_cast<int64_t>(r.u64()));
    case 2: { double n=std::bit_cast<double>(r.u64()); if(!std::isfinite(n))invalid("non-finite constant"); return Value(n); }
    case 3: return Value(r.str());
    case 4: { uint8_t b=r.u8(); if (b>1)invalid("invalid Boolean constant"); return Value(b==1); }
    default: invalid("unknown constant type");
    }
}
void writeChunk(Writer& w,const std::shared_ptr<Chunk>& chunk,int depth) {
    if (!chunk || depth > kMaxNesting || chunk->code.size()>kMaxInstructions) invalid("code exceeds limits");
    w.u32(static_cast<uint32_t>(chunk->code.size()));
    for(const auto& i:chunk->code) {
        w.u8(static_cast<uint8_t>(i.op));
        w.u32(static_cast<uint32_t>(i.loc.line));
        w.u32(static_cast<uint32_t>(i.loc.col));
        w.u32(std::bit_cast<uint32_t>(static_cast<int32_t>(i.number)));
        w.str(i.name);
        writeValue(w, i.value);
        w.u8(i.fn ? 1 : 0);
        if (i.fn) {
            w.str(i.fn->name);
            w.u32(static_cast<uint32_t>(i.fn->params.size()));
            for(const auto& p:i.fn->params) w.str(p);
            writeChunk(w,i.fn->code,depth+1);
        }
    }
    if (w.buf.size()>kMaxPayload) invalid("payload exceeds size limit");
}
std::shared_ptr<Chunk> readChunk(Reader& r,int depth,uint32_t& total) {
    if (depth > kMaxNesting)invalid("function nesting too deep");
    uint32_t count=r.u32();
    if (count>kMaxInstructions || count>kMaxInstructions-total)invalid("instruction limit exceeded");
    total+=count;
    auto chunk=std::make_shared<Chunk>();
    chunk->code.reserve(count);
    for(uint32_t n=0;n<count;++n) {
        uint8_t raw=r.u8();
        if (raw>kLastOpcode)invalid("invalid opcode");
        Instruction i;
        i.op=static_cast<Op>(raw);
        uint32_t line=r.u32(),col=r.u32();
        if (line==0||col==0||line>10'000'000||col>1'000'000)invalid("invalid source location");
        i.loc={"", "", static_cast<int>(line), static_cast<int>(col)};
        i.number=std::bit_cast<int32_t>(r.u32());
        i.name=r.str(kMaxName);
        i.value=readValue(r);
        uint8_t hasFn=r.u8(); if(hasFn>1)invalid("invalid function flag");
        if (hasFn) {
            auto f=std::make_shared<FunctionDefinition>();
            f->name=r.str(kMaxName);
            uint32_t params=r.u32();
            if(params>255)invalid("too many function parameters");
            for(uint32_t j=0;j<params;++j)f->params.push_back(r.str(kMaxName));
            f->code=readChunk(r,depth+1,total);
            i.fn=std::move(f);
        }
        chunk->code.push_back(std::move(i));
    }
    return chunk;
}
int stackEffect(Op op,int n,int& needs) {
    needs=0;
    switch(op) {
    case Op::Constant:case Op::Load: needs=0;return 1;
    case Op::Store:case Op::Pop:case Op::Print:case Op::JumpFalse:case Op::JumpTrue:case Op::Return: needs=1;return -1;
    case Op::Neg:case Op::Not:case Op::CheckBool:case Op::CountCheck:needs=1;return 0;
    case Op::Add:case Op::Sub:case Op::Mul:case Op::Div:case Op::Mod:
    case Op::Eq:case Op::Ne:case Op::Lt:case Op::Le:case Op::Gt:case Op::Ge: case Op::Index:needs=2;return -1;
    case Op::SetIndex:needs=3;return -3;
    case Op::MakeList:needs=n;return 1-n;
    case Op::Call:needs=n+1;return -n;
    case Op::MakeFunction:case Op::Jump:needs=0;return 0;
    }
    invalid("unsupported opcode");
}
void verifyChunk(const std::shared_ptr<Chunk>& chunk,int depth,bool function,uint32_t& total) {
    if(!chunk||depth>kMaxNesting||chunk->code.size()>kMaxInstructions)invalid("invalid code chunk");
    // The loader enforces a global instruction ceiling across nested functions;
    // the writer must apply the same limit before emitting a file.
    if(chunk->code.size()>kMaxInstructions-total)invalid("instruction limit exceeded");
    total+=static_cast<uint32_t>(chunk->code.size());
    auto N=chunk->code.size();
    for(const auto &i:chunk->code) {
        if (static_cast<uint8_t>(i.op)>kLastOpcode)invalid("unknown opcode");
        if (i.loc.line<1||i.loc.col<1||i.loc.line>10'000'000||i.loc.col>1'000'000)invalid("invalid source location");
        bool branch=(i.op==Op::Jump||i.op==Op::JumpFalse||i.op==Op::JumpTrue);
        bool count=(i.op==Op::MakeList||i.op==Op::Call);
        if (branch && (i.number<0||static_cast<size_t>(i.number)>N))invalid("jump target outside chunk");
        if (count && (i.number<0||i.number>(i.op==Op::Call?255:10'000)))invalid("operand count exceeds limit");
        if (!branch&&!count&&i.number!=0)invalid("unexpected numeric operand");
        bool naming=(i.op==Op::Load||i.op==Op::Store||i.op==Op::MakeFunction);
        if (naming?i.name.empty()||i.name.size()>kMaxName:!i.name.empty())invalid("invalid instruction name");
        if (i.op==Op::Constant) {
            if (i.fn)invalid("constant contains function");
        } else if (!std::holds_alternative<std::monostate>(i.value.data))invalid("unexpected constant payload");
        if (i.op==Op::MakeFunction) {
            if(!i.fn||i.fn->name!=i.name||i.fn->params.size()>255)invalid("invalid function definition");
            std::set<std::string> params;
            for (const auto& p:i.fn->params)if(p.empty()||p.size()>kMaxName||!params.insert(p).second)invalid("duplicate/invalid function parameter");
            verifyChunk(i.fn->code,depth+1,true,total);
        } else if (i.fn)invalid("unexpected function definition");
        if (i.op==Op::Return && !function)invalid("top-level return forbidden");
    }
    std::vector<int> heights(N+1,-1);std::queue<size_t> pending;
    heights[0]=0;pending.push(0);
    auto offer=[&](size_t position,int height) {
        if (heights[position]==-1){heights[position]=height;pending.push(position);}
        else if (heights[position]!=height)invalid("inconsistent stack height across branches");
    };
    while(!pending.empty()) {
        size_t at=pending.front();pending.pop();
        if (at==N)continue;
        const auto& i=chunk->code[at];
        int required=0,effect=stackEffect(i.op,i.number,required);
        int before=heights[at];
        if(before<required)invalid("operand stack underflow");
        int after=before+effect;
        if(after<0||after>kMaxStack)invalid("operand stack exceeds limits");
        if(i.op==Op::Return)continue;
        if(i.op==Op::Jump)offer(static_cast<size_t>(i.number),after);
        else if(i.op==Op::JumpFalse||i.op==Op::JumpTrue) {
            offer(static_cast<size_t>(i.number),after);offer(at+1,after);
        }else offer(at+1,after);
    }
    if(heights[N]>=0 && heights[N]!=0)invalid("stack is not empty at program end");
    if(function && heights[N]>=0)invalid("function can exit without RETURN");
}
} // namespace

void writeBytecode(const std::shared_ptr<Chunk>& code,const std::string& path) {
    uint32_t verifiedInstructions=0;
    verifyChunk(code,0,false,verifiedInstructions);
    Writer payload;writeChunk(payload,code,0);
    if(payload.buf.size()>kMaxPayload)invalid("payload exceeds size limit");
    Writer archive;
    for(char c:std::string("KBC1"))archive.u8(static_cast<uint8_t>(c));
    archive.u16(1);archive.u16(0);
    archive.u32(static_cast<uint32_t>(payload.buf.size()));
    archive.u32(crc32(payload.buf));
    archive.buf.insert(archive.buf.end(),payload.buf.begin(),payload.buf.end());
    std::ofstream out(path,std::ios::binary|std::ios::trunc);
    if(!out)throw std::runtime_error("Cannot create bytecode file: "+path);
    out.write(reinterpret_cast<const char*>(archive.buf.data()),static_cast<std::streamsize>(archive.buf.size()));
    if(!out)throw std::runtime_error("Failed writing bytecode: "+path);
}
std::shared_ptr<Chunk> readBytecode(const std::string& path) {
    std::ifstream in(path,std::ios::binary|std::ios::ate);
    if(!in)throw std::runtime_error("Cannot open bytecode file: "+path);
    auto size=in.tellg();
    if(size<16||size>static_cast<std::streamoff>(kMaxPayload+16))invalid("file length exceeds limits");
    in.seekg(0);
    std::vector<uint8_t> bytes(static_cast<size_t>(size));
    in.read(reinterpret_cast<char*>(bytes.data()),static_cast<std::streamsize>(bytes.size()));
    if(!in)invalid("file truncated");
    Reader header(bytes,0,16);
    for(char c:std::string("KBC1"))if(header.u8()!=static_cast<uint8_t>(c))invalid("wrong magic");
    if(header.u16()!=1)invalid("unsupported version");
    if(header.u16()!=0)invalid("unsupported flags");
    uint32_t length=header.u32(),digest=header.u32();
    if(length!=bytes.size()-16)invalid("payload length mismatch");
    std::vector<uint8_t> payload(bytes.begin()+16,bytes.end());
    if(crc32(payload)!=digest)invalid("checksum mismatch");
    Reader reader(bytes,16,bytes.size());
    uint32_t total=0;
    auto chunk=readChunk(reader,0,total);
    if(!reader.done())invalid("extra bytes after code");
    uint32_t verifiedInstructions=0;
    verifyChunk(chunk,0,false,verifiedInstructions);
    return chunk;
}
} // namespace kasa
