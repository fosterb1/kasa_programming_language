#pragma once
// Kasa Native internal compiler and VM interfaces.
#include <cstdint>
#include <iosfwd>
#include <memory>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <variant>
#include <utility>
#include <vector>
#ifdef KASA_ENABLE_BIGINT_VM
#include "kasa/big_integer.hpp"
#endif
namespace kasa {
using namespace std;
struct Token { string kind, text; int line=1, col=1; };
struct Failure : runtime_error {
    Failure(const Token &t, const string &category, const string &message, const string &file)
      : runtime_error(file+":"+to_string(t.line)+":"+to_string(t.col)+": "+category+": "+message) {}
};


struct List;struct Function;struct Builtin {string name;};
struct Value {
#ifdef KASA_ENABLE_BIGINT_VM
    using Data=variant<monostate,int64_t,double,string,bool,shared_ptr<List>,shared_ptr<Function>,Builtin,bigint::Integer>;
#else
    using Data=variant<monostate,int64_t,double,string,bool,shared_ptr<List>,shared_ptr<Function>,Builtin>;
#endif
    Data data;
    Value()=default;
    Value(int64_t x):data(x){} Value(double x):data(x){} Value(string x):data(std::move(x)){} Value(bool x):data(x){}
#ifdef KASA_ENABLE_BIGINT_VM
    Value(bigint::Integer x):data(std::move(x)){}
#endif
    Value(shared_ptr<List> x):data(std::move(x)){} Value(shared_ptr<Function> x):data(std::move(x)){} Value(Builtin x):data(std::move(x)){}
};
struct List{vector<Value> items;};
struct Expr;using E=shared_ptr<Expr>;
struct Expr {string kind,op;Token token;Value value;vector<E> kids;};
struct Stmt;using S=shared_ptr<Stmt>;
struct Stmt{string kind,name;Token token;E a,b;vector<S> yes,no;vector<string>params;};

enum class Op{Constant,Load,Store,Pop,Print,Neg,Not,Add,Sub,Mul,Div,Mod,Eq,Ne,Lt,Le,Gt,Ge,CheckBool,Jump,JumpFalse,JumpTrue,MakeList,Index,SetIndex,MakeFunction,Call,Return,CountCheck};
struct Chunk;
struct FunctionDefinition{string name;vector<string>params;shared_ptr<Chunk>code;};
struct Instruction{Op op;Token loc;int number=0;string name;Value value;shared_ptr<FunctionDefinition> fn;};
struct Chunk{vector<Instruction> code;};

vector<Token> lex(string src,const string &filename);
vector<S> parseSource(vector<Token> tokens,const string &filename);
shared_ptr<Chunk> compileProgram(const vector<S>&stmts,const string&filename);
void runProgram(shared_ptr<Chunk>code,const string&filename,ostream&out,istream&in);
void disasm(const shared_ptr<Chunk>&code,ostream&out,int indent=0);
// KBC1 draft: serialized bytecode is validated before execution.
void writeBytecode(const shared_ptr<Chunk>&code,const string&path);
shared_ptr<Chunk> readBytecode(const string&path);
} // namespace kasa
