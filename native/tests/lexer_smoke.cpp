#include "kasa/native.hpp"
#include <iostream>
#include <string>
#include <vector>
using namespace std;

struct Case { string name, source; int line, column; bool lexer_error; };

int main() {
    const vector<Case> cases = {
        {"ascii_control", "ka \"A\" & 3", 1, 8, true},
        {"twi_open_o", "ka \"ɔ\" & 3", 1, 8, true},
        {"twi_open_e", "ka \"ɛ\" & 3", 1, 8, true},
        {"two_twi_codepoints", "ka \"ɛɔ\" & 3", 1, 9, true},
        {"twi_identifier_on_second_line", "ma ɛdin = 2\nka ɛdin & 0", 2, 9, true},
        {"supplementary_unicode_symbol", "ka \"🙂\" & 3", 1, 8, true},
        {"twi_with_crlf", "ma ɛdin = 2\r\nka \"ɔ\" & 3", 2, 8, true},
        {"trailing_operator_eof", "ka 1 +", 1, 7, false},
        {"twi_before_eof_error", "ka \"ɔ\" +", 1, 9, false},
        {"supplementary_letter_identifier", "ma 𐐀 = 3\nka 𐐀 & 2", 2, 6, true},
        {"mixed_twi_supplementary_identifier", "ma ɛ𐐀 = 3\nka ɛ𐐀 & 2", 2, 7, true},
    };
    int passed = 0;
    for (const auto& testcase : cases) {
        bool ok = false;
        try {
            auto tokens = kasa::lex(testcase.source, "test.kasa");
            if (!testcase.lexer_error && !tokens.empty()) {
                const auto& eof = tokens.back();
                ok = eof.kind == "EOF" && eof.line == testcase.line && eof.col == testcase.column;
            }
        } catch (const kasa::Failure& error) {
            const string needle = "test.kasa:" + to_string(testcase.line) + ":" +
                                  to_string(testcase.column) + ": SyntaxError:";
            ok = testcase.lexer_error && string(error.what()).find(needle) != string::npos;
        } catch (const exception&) {
            ok = false;
        }
        cout << (ok ? "PASS " : "FAIL ") << testcase.name << '\n';
        passed += ok;
    }
    struct ValidIdentifier { string name, word, source; };
    const vector<ValidIdentifier> identifiers = {
        {"supplementary_identifier_valid", "𐐀", "ma 𐐀 = 3\nka 𐐀"},
        {"mixed_twi_identifier_valid", "ɛ𐐀", "ma ɛ𐐀 = 5\nka ɛ𐐀"},
    };
    for (const auto& testcase : identifiers) {
        bool ok = false;
        try {
            auto tokens = kasa::lex(testcase.source, "test.kasa");
            int matches = 0;
            for (const auto& token : tokens)
                if (token.kind == "NAME" && token.text == testcase.word) ++matches;
            ok = matches == 2;
        } catch (const exception&) {
            ok = false;
        }
        cout << (ok ? "PASS " : "FAIL ") << testcase.name << '\n';
        passed += ok;
    }
    const int total = static_cast<int>(cases.size() + identifiers.size());
    cout << passed << "/" << total << " native lexer checks passed\n";
    return passed == total ? 0 : 1;
}
