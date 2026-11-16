// C ABI for the Kasa bytecode VM in a WebAssembly worker.
// All returned pointers are owned by the caller and freed with kasa_free().
#include "kasa/native.hpp"
#include <cstdlib>
#include <cstring>
#include <exception>
#include <sstream>
#include <string>
#include <utility>

#if defined(__EMSCRIPTEN__)
#include <emscripten/emscripten.h>
#define KASA_EXPORT EMSCRIPTEN_KEEPALIVE
#else
#define KASA_EXPORT
#endif

namespace {
constexpr size_t kMaxSourceBytes = 50'000;
constexpr size_t kMaxInputBytes = 50'000;
constexpr size_t kMaxOutputBytes = 64'000;

std::string escape_json(const std::string& value) {
    constexpr char digits[] = "0123456789abcdef";
    std::string result;
    result.reserve(value.size() + 2);
    result += '"';
    for (unsigned char ch : value) {
        switch (ch) {
        case '"': result += "\\\""; break;
        case '\\': result += "\\\\"; break;
        case '\b': result += "\\b"; break;
        case '\f': result += "\\f"; break;
        case '\n': result += "\\n"; break;
        case '\r': result += "\\r"; break;
        case '\t': result += "\\t"; break;
        default:
            if (ch < 0x20) {
                result += "\\u00";
                result += digits[ch >> 4];
                result += digits[ch & 15];
            } else {
                result += static_cast<char>(ch);
            }
        }
    }
    result += '"';
    return result;
}

std::string run(const char* code, const char* input, int check) {
    bool ok = false;
    std::string output;
    std::string error;
    const std::string mode = check ? "check" : "run";
    try {
        if (!code || !input) {
            error = "Invalid source or input";
        } else if (std::strlen(code) > kMaxSourceBytes) {
            error = "Source exceeds the 50,000-byte WebAssembly limit";
        } else if (std::strlen(input) > kMaxInputBytes) {
            error = "Input exceeds the 50,000-byte WebAssembly limit";
        } else {
            const std::string filename = "playground.kasa";
            const auto tokens = kasa::lex(code, filename);
            const auto ast = kasa::parseSource(tokens, filename);
            const auto compiled = kasa::compileProgram(ast, filename);
            if (!check) {
                std::ostringstream captured;
                std::istringstream stdin_stream(input);
                try {
                    kasa::runProgram(compiled, filename, captured, stdin_stream);
                } catch (...) {
                    output = captured.str();
                    throw;
                }
                output = captured.str();
                if (output.size() > kMaxOutputBytes) {
                    error = "Output exceeds the 64,000-byte WebAssembly limit";
                } else {
                    ok = true;
                }
            } else {
                ok = true;
            }
        }
    } catch (const kasa::Failure& failure) {
        error = failure.what();
    } catch (const std::exception& exception) {
        error = std::string("InternalError: ") + exception.what();
    } catch (...) {
        error = "InternalError: unexpected native failure";
    }

    return "{\"ok\":" + std::string(ok ? "true" : "false")
        + ",\"output\":" + escape_json(output)
        + ",\"error\":" + escape_json(error)
        + ",\"steps\":0"
        + ",\"mode\":" + escape_json(mode)
        + ",\"engine\":\"native-wasm\"}";
}
} // namespace

extern "C" {
KASA_EXPORT char* kasa_run(const char* code, const char* input, int check) {
    const std::string encoded = run(code, input, check);
    auto* data = static_cast<char*>(std::malloc(encoded.size() + 1));
    if (data) std::memcpy(data, encoded.c_str(), encoded.size() + 1);
    return data;
}
KASA_EXPORT void kasa_free(char* pointer) { std::free(pointer); }
}
