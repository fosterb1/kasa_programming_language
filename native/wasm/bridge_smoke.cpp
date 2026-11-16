// Test the same C ABI without Emscripten to catch host-bridge regressions.
#include <cassert>
#include <cstdlib>
#include <string>
#include <iostream>
extern "C" char* kasa_run(const char*, const char*, int);
extern "C" void kasa_free(char*);
int main() {
    auto exercise = [](const char *source, const char* input, int check, const char* expected) {
        char *ptr = kasa_run(source, input, check);
        assert(ptr != nullptr);
        const std::string result(ptr);
        kasa_free(ptr);
        if (result.find(expected) == std::string::npos) {
            std::cerr << "Expected " << expected << " in " << result << "\n";
            std::abort();
        }
    };
    exercise("ka \"Maakye, Ghana!\"", "", 0, "Maakye, Ghana!\\n");
    exercise("dwumadie fa_bi(a,b)\n sanma a+b\nawiei\nka fa_bi(4, 6)", "", 0, "10\\n");
    exercise("ka bisa()", "Akosua\n", 0, "Akosua\\n");
    exercise("ka 7 / 0", "", 0, "ZeroDivisionError");
    exercise("ka 7 / 0", "", 1, "\"ok\":true");
    exercise("ka dodo", "", 0, "NameError");
    exercise("ka \"twi: ɛ ɔ\"", "", 0, "ɛ ɔ");
    exercise("ka \"\\\"\"", "", 0, "\\\"\\n");
    std::cout << "Kasa C ABI bridge smoke checks passed\n";
}
