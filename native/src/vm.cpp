#include "kasa/native.hpp"
#include "kasa/numeric_compare.hpp"
#include "kasa/float_display.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <iterator>
#include <limits>
#include <map>
#include <memory>
#include <regex>
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>
#include <cctype>
#include <cstdlib>
#include <cerrno>
namespace kasa {
using namespace std;
struct Environment{unordered_map<string,Value> values;shared_ptr<Environment> parent;
 explicit Environment(shared_ptr<Environment> parent=nullptr):parent(std::move(parent)){}
 Value get(const string&name,const Token&t,const string&file){for(auto p=this;p;p=p->parent.get()){
     auto it=p->values.find(name);if(it!=p->values.end())return it->second;}
     throw Failure(t,"NameError","Unknown name '"+name+"'",file);
 }
};
struct Function{shared_ptr<FunctionDefinition> definition;shared_ptr<Environment> closure;};

static bool numeric(const Value &v){
#ifdef KASA_ENABLE_BIGINT_VM
    if(holds_alternative<bigint::Integer>(v.data))return true;
#endif
    return holds_alternative<int64_t>(v.data)||holds_alternative<double>(v.data);
}
static bool integer(const Value &v){
#ifdef KASA_ENABLE_BIGINT_VM
    if(holds_alternative<bigint::Integer>(v.data))return true;
#endif
    return holds_alternative<int64_t>(v.data);
}
#ifdef KASA_ENABLE_BIGINT_VM
static bigint::Integer exactInt(const Value&v){
    return holds_alternative<int64_t>(v.data)?bigint::Integer(get<int64_t>(v.data)):get<bigint::Integer>(v.data);
}
static Value compactInt(const bigint::Integer&v){
    bigint::check(v);
    if(v>=numeric_limits<int64_t>::min()&&v<=numeric_limits<int64_t>::max())
        return Value(v.convert_to<int64_t>());
    return Value(v);
}
static int integerCompareFloat(const Value&v, double decimal){
    if(holds_alternative<int64_t>(v.data))
        return numbers::compareIntDouble(get<int64_t>(v.data),decimal);
    // Represent binary64 exactly as an integer numerator / power-of-two.
    // This avoids ever rounding large integers through double.
    if(!isfinite(decimal))throw domain_error("Non-finite decimal comparison");
    const auto n=exactInt(v);
    if(decimal==0)return n<0?-1:n>0?1:0;
    const bool negative=signbit(decimal);
    int exponent=0;
    const double fraction=frexp(abs(decimal),&exponent);
    const auto significand=static_cast<uint64_t>(ldexp(fraction,53));
    bigint::Integer numerator(significand);
    if(negative)numerator=-numerator;
    const int shift=exponent-53;
    const bigint::Integer lhs=shift>=0?n:(n<<-shift);
    const bigint::Integer rhs=shift>=0?(numerator<<shift):numerator;
    return lhs<rhs?-1:lhs>rhs?1:0;
}
#endif
static double asDouble(const Value &v){
#ifdef KASA_ENABLE_BIGINT_VM
    if(holds_alternative<bigint::Integer>(v.data))return get<bigint::Integer>(v.data).convert_to<double>();
#endif
    return holds_alternative<int64_t>(v.data)?static_cast<double>(get<int64_t>(v.data)):get<double>(v.data);
}
static string display(const Value &v,int depth=0){
    if(holds_alternative<monostate>(v.data))return "hwee";
    if(holds_alternative<int64_t>(v.data))return to_string(get<int64_t>(v.data));
#ifdef KASA_ENABLE_BIGINT_VM
    if(holds_alternative<bigint::Integer>(v.data))return get<bigint::Integer>(v.data).convert_to<string>();
#endif
    if(holds_alternative<double>(v.data)){
        return numbers::displayFloat(get<double>(v.data));
    }
    if(holds_alternative<bool>(v.data))return get<bool>(v.data)?"nokware":"atoro";
    if(holds_alternative<string>(v.data))return get<string>(v.data);
    if(holds_alternative<shared_ptr<Function>>(v.data))return "<dwumadie>";
    if(holds_alternative<Builtin>(v.data))return "<built-in>";
    if(depth>10)return "[...]";
    string s="[";const auto&list=get<shared_ptr<List>>(v.data)->items;
    for(size_t i=0;i<list.size();++i){
        if(i)s+=", ";
        bool text=holds_alternative<string>(list[i].data);
        if(text)s+="'";
        s+=display(list[i],depth+1);
        if(text)s+="'";
    }return s+"]";
}
static bool equal(const Value&a,const Value&b,int depth=0){
    if(integer(a)&&integer(b)){
#ifdef KASA_ENABLE_BIGINT_VM
        return exactInt(a)==exactInt(b);
#else
        return get<int64_t>(a.data)==get<int64_t>(b.data);
#endif
    }
    if(integer(a)&&holds_alternative<double>(b.data))
#ifdef KASA_ENABLE_BIGINT_VM
        return integerCompareFloat(a,get<double>(b.data))==0;
#else
        return numbers::compareIntDouble(get<int64_t>(a.data),get<double>(b.data))==0;
#endif
    if(holds_alternative<double>(a.data)&&integer(b))
#ifdef KASA_ENABLE_BIGINT_VM
        return integerCompareFloat(b,get<double>(a.data))==0;
#else
        return numbers::compareIntDouble(get<int64_t>(b.data),get<double>(a.data))==0;
#endif
    if(numeric(a)&&numeric(b))return get<double>(a.data)==get<double>(b.data);
    if(a.data.index()!=b.data.index())return false;
    if(holds_alternative<monostate>(a.data))return true;
    if(holds_alternative<bool>(a.data))return get<bool>(a.data)==get<bool>(b.data);
    if(holds_alternative<string>(a.data))return get<string>(a.data)==get<string>(b.data);
    if(holds_alternative<shared_ptr<List>>(a.data)){
        const auto&x=get<shared_ptr<List>>(a.data)->items;const auto&y=get<shared_ptr<List>>(b.data)->items;
        if(x.size()!=y.size())return false;
        if(depth>15)return &x==&y;
        for(size_t i=0;i<x.size();++i)if(!equal(x[i],y[i],depth+1))return false;
        return true;
    }
    return false;
}

class VM{
    ostream &out;istream &in;string filename;size_t steps=0,printed=0;int depth=0;
    const size_t maxSteps=100000,maxOutput=64000,maxList=10000,maxText=1000000;
    static size_t countUnicodeCodepoints(const string& text) {
        size_t count=0;
        for(unsigned char byte:text) if((byte&0xc0)!=0x80) ++count;
        return count;
    }
    void emit(const string& text,const Token& token,bool flushOutput=false) {
        const size_t characters=countUnicodeCodepoints(text);
        if(characters>maxOutput-printed)
            error(token,"ResourceError","Output exceeded the 64,000-character limit");
        out<<text;
        printed+=characters;
        if(flushOutput)out<<flush;
    }
    // Functions capture environments using shared ownership. Recursive and nested
    // definitions can therefore produce cycles (environment -> function -> environment).
    // Track environments weakly and break cycles only when the entire VM finishes,
    // preserving escaping lexical closures during program execution.
    vector<weak_ptr<Environment>> trackedEnvironments;
    shared_ptr<Environment> makeEnvironment(shared_ptr<Environment> parent=nullptr) {
        auto environment=make_shared<Environment>(std::move(parent));
        trackedEnvironments.emplace_back(environment);
        return environment;
    }

    static Value pop(vector<Value>&v){if(v.empty())throw runtime_error("VM operand stack underflow");Value x=std::move(v.back());v.pop_back();return x;}
    [[noreturn]]void error(const Token&t,const string&category,const string&msg)const{throw Failure(t,category,msg,filename);}
    bool truth(const Value&v,const Token&t){if(!holds_alternative<bool>(v.data))error(t,"TypeError","Condition requires a Boolean");return get<bool>(v.data);}
    double number(const Value&v,const Token&t){if(!numeric(v))error(t,"TypeError","Arithmetic requires numbers, not Boolean or text");return asDouble(v);}
    int64_t count(const Value&v,const Token&t){
#ifdef KASA_ENABLE_BIGINT_VM
        if(!integer(v)||exactInt(v)<0)error(t,"TypeError","mpɛn requires a nonnegative integer");
        if(exactInt(v)>numeric_limits<int64_t>::max())error(t,"ResourceError","Repeat count is too large");
        return exactInt(v).convert_to<int64_t>();
#else
        if(!integer(v)||get<int64_t>(v.data)<0)error(t,"TypeError","mpɛn requires a nonnegative integer");
        return get<int64_t>(v.data);
#endif
    }
    int64_t index(const Value&v,const Token&t){
        if(!integer(v))error(t,"TypeError","List index must be an integer");
#ifdef KASA_ENABLE_BIGINT_VM
        const auto n=exactInt(v);
        if(n<numeric_limits<int64_t>::min()||n>numeric_limits<int64_t>::max())
            error(t,"IndexError","List index out of range");
        return n.convert_to<int64_t>();
#else
        return get<int64_t>(v.data);
#endif
    }
#ifdef KASA_ENABLE_BIGINT_VM
    Value safeAdd(int64_t a,int64_t b,const Token&t){
        try {return compactInt(bigint::add(bigint::Integer(a),bigint::Integer(b)));}
        catch(const bigint::SizeLimit&){error(t,"ResourceError","Integer exceeds size limit");}
    }
    Value safeSub(int64_t a,int64_t b,const Token&t){
        try {return compactInt(bigint::subtract(bigint::Integer(a),bigint::Integer(b)));}
        catch(const bigint::SizeLimit&){error(t,"ResourceError","Integer exceeds size limit");}
    }
    Value safeMul(int64_t a,int64_t b,const Token&t){
        try {return compactInt(bigint::multiply(bigint::Integer(a),bigint::Integer(b)));}
        catch(const bigint::SizeLimit&){error(t,"ResourceError","Integer exceeds size limit");}
    }
#else
    Value safeAdd(int64_t a,int64_t b,const Token&t){
        if((b>0&&a>INT64_MAX-b)||(b<0&&a<INT64_MIN-b))error(t,"ResourceError","Integer exceeds native 64-bit range");
        return Value(a+b);
    }
    Value safeSub(int64_t a,int64_t b,const Token&t){
        if((b<0&&a>INT64_MAX+b)||(b>0&&a<INT64_MIN+b))error(t,"ResourceError","Integer exceeds native 64-bit range");
        return Value(a-b);
    }
    Value safeMul(int64_t a,int64_t b,const Token&t){
        bool bad=false;
        if(a!=0&&b!=0){
            if(a==-1)bad=(b==INT64_MIN);
            else if(b==-1)bad=(a==INT64_MIN);
            else if(a>0)bad=b>0?(a>INT64_MAX/b):(b<INT64_MIN/a);
            else bad=b>0?(a<INT64_MIN/b):(a<INT64_MAX/b);
        }
        if(bad)error(t,"ResourceError","Integer exceeds native 64-bit range");
        return Value(a*b);
    }
#endif
    Value checkedDouble(double x,const Token&t){if(!isfinite(x))error(t,"ResourceError","Number exceeds supported range");return Value(x);}
    Value arithmetic(Op op,const Value&a,const Value&b,const Token&t){
        if(op==Op::Add&&holds_alternative<string>(a.data)&&holds_alternative<string>(b.data)){
            auto s=get<string>(a.data)+get<string>(b.data);if(s.size()>maxText)error(t,"ResourceError","Text is too large");return Value(s);
        }
#ifdef KASA_ENABLE_BIGINT_VM
        if(integer(a)&&integer(b)){
            try {
                const auto p=exactInt(a),q=exactInt(b);
                if(op==Op::Add)return compactInt(bigint::add(p,q));
                if(op==Op::Sub)return compactInt(bigint::subtract(p,q));
                if(op==Op::Mul)return compactInt(bigint::multiply(p,q));
                if(op==Op::Mod){
                    if(q==0)error(t,"ZeroDivisionError","Cannot divide by zero");
                    return compactInt(bigint::floorRemainder(p,q));
                }
            } catch(const bigint::SizeLimit&){
                error(t,"ResourceError","Integer exceeds size limit");
            }
        }
#endif
        // Only floating-point operations require conversion to binary64.
        // Keep arbitrary integer arithmetic entirely exact and bounded.
        if(op==Op::Div){
            double x=number(a,t),y=number(b,t);
            if(y==0)error(t,"ZeroDivisionError","Cannot divide by zero");
            return checkedDouble(x/y,t);
        }
        if(op==Op::Mod){if(!integer(a)||!integer(b))error(t,"TypeError","Remainder requires integers");
            int64_t z=get<int64_t>(b.data);if(z==0)error(t,"ZeroDivisionError","Cannot divide by zero");
            int64_t n=get<int64_t>(a.data);
            if(n==INT64_MIN&&z==-1)return Value(int64_t(0));
            // Kasa remainder follows the Python reference, not C++ truncating
            // remainder: a nonzero result must have the divisor's sign.
            int64_t remainder=n%z;
            if(remainder!=0&&((remainder<0)!=(z<0)))remainder+=z;
            return Value(remainder);
        }
        if(holds_alternative<int64_t>(a.data)&&holds_alternative<int64_t>(b.data)){
            int64_t p=get<int64_t>(a.data),q=get<int64_t>(b.data);
            if(op==Op::Add)return safeAdd(p,q,t);
            if(op==Op::Sub)return safeSub(p,q,t);
            if(op==Op::Mul)return safeMul(p,q,t);
        }
        double x=number(a,t),y=number(b,t);
        if(op==Op::Add)return checkedDouble(x+y,t);
        if(op==Op::Sub)return checkedDouble(x-y,t);
        if(op==Op::Mul)return checkedDouble(x*y,t);
        error(t,"RuntimeError","Invalid arithmetic operator");
    }
    Value builtin(const Builtin&b,const vector<Value>&args,const Token&t){
        if(b.name=="bisa"){
            if(args.size()>1)error(t,"TypeError","bisa expects zero or one argument");
            if(!args.empty()){
                if(!holds_alternative<string>(args[0].data))error(t,"TypeError","bisa prompt must be text");
                const string&prompt=get<string>(args[0].data);
                emit(prompt,t,true);
            }
            string line;if(!getline(in,line))error(t,"InputError","No more input is available");
            // getline consumes LF but retains CR in CRLF input. Kasa's Python
            // reference and browser runtime discard terminal CR/LF characters,
            // including when the last input line has no final LF.
            while(!line.empty()&&line.back()=='\r')line.pop_back();
            if(line.size()>maxText)error(t,"ResourceError","Input is too long");
            return Value(line);
        }
        if(args.size()!=1)error(t,"TypeError",b.name+" expects one argument");
        const Value&v=args[0];
        if(b.name=="nsɛm")return Value(display(v));
        if(b.name=="tentɛn"){
            if(holds_alternative<shared_ptr<List>>(v.data))return Value(static_cast<int64_t>(get<shared_ptr<List>>(v.data)->items.size()));
            if(holds_alternative<string>(v.data)){
                auto&s=get<string>(v.data);int64_t n=0;for(unsigned char c:s)if((c&0xc0)!=0x80)++n;return Value(n);
            }
            error(t,"TypeError","tentɛn requires text or a list");
        }
        if(b.name=="nɔma"){
            if(numeric(v))return v;
            if(!holds_alternative<string>(v.data))error(t,"TypeError","nɔma expects number or numeric text");
            string s=get<string>(v.data);size_t a=s.find_first_not_of(" \t\n\r");if(a==string::npos)error(t,"TypeError","Invalid numeric text");
            size_t e=s.find_last_not_of(" \t\n\r");s=s.substr(a,e-a+1);
            if(s.size()>1000)error(t,"ResourceError","Numeric text is too long");
            // Use the same ASCII-decimal grammar as the Python/JS runtimes.
            // std::stod alone accepts exponent notation and other spellings
            // which are not legal Kasa numeric input.
            static const regex decimalGrammar(R"([+-]?([0-9]+(\.[0-9]+)?|\.[0-9]+))");
            if(!regex_match(s,decimalGrammar))error(t,"TypeError","Invalid numeric text");
            try{
#ifndef KASA_ENABLE_BIGINT_VM
                size_t used=0;
#endif
                if(s.find('.')!=string::npos){
                    // std::stod throws out_of_range even when a finite decimal
                    // correctly rounds to zero or a subnormal binary64 value.
                    // strtod preserves IEEE-754 underflow results; reject only
                    // non-finite overflow after strict Kasa grammar validation.
                    char* end=nullptr;
                    const double d=std::strtod(s.c_str(),&end);
                    if(end!=s.c_str()+s.size())
                        error(t,"TypeError","Invalid numeric text");
                    return checkedDouble(d,t);
                }
#ifdef KASA_ENABLE_BIGINT_VM
                return compactInt(bigint::decimal(s));
#else
                int64_t n=stoll(s,&used);
                if(used!=s.size())error(t,"TypeError","Invalid numeric text");
                return Value(n);
#endif
            }catch(const out_of_range&){error(t,"ResourceError","Numeric value is too large");
            }catch(const invalid_argument&){error(t,"TypeError","Invalid numeric text");}
        }
        error(t,"NameError","Unknown built-in");
    }
    Value runChunk(const shared_ptr<Chunk>&chunk,const shared_ptr<Environment>&env){
        vector<Value>stack;const auto&code=chunk->code;size_t ip=0;
        while(ip<code.size()){
            const auto&i=code.at(ip++);
            if(++steps>maxSteps)error(i.loc,"ResourceError","Execution limit exceeded");
            switch(i.op){
                case Op::Constant:stack.push_back(i.value);break;
                case Op::Load:stack.push_back(env->get(i.name,i.loc,filename));break;
                case Op::Store:env->values[i.name]=pop(stack);break;
                case Op::Print:{string text=display(pop(stack))+"\n";
                    emit(text,i.loc);break;}
                case Op::Pop:pop(stack);break;
                case Op::Neg:{Value x=pop(stack);if(integer(x)){
#ifdef KASA_ENABLE_BIGINT_VM
                        try {stack.push_back(compactInt(-exactInt(x)));}
                        catch(const bigint::SizeLimit&){error(i.loc,"ResourceError","Integer exceeds size limit");}
#else
                        stack.push_back(safeSub(0,get<int64_t>(x.data),i.loc));
#endif
                    } else stack.push_back(checkedDouble(-number(x,i.loc),i.loc));
                    break;}
                case Op::Not:{Value x=pop(stack);stack.push_back(Value(!truth(x,i.loc)));break;}
                case Op::Add:case Op::Sub:case Op::Mul:case Op::Div:case Op::Mod:{Value b=pop(stack),a=pop(stack);stack.push_back(arithmetic(i.op,a,b,i.loc));break;}
                case Op::Eq:case Op::Ne:{Value b=pop(stack),a=pop(stack);bool ok=equal(a,b);stack.push_back(Value(i.op==Op::Eq?ok:!ok));break;}
                case Op::Lt:case Op::Le:case Op::Gt:case Op::Ge:{Value b=pop(stack),a=pop(stack);
                    bool result;
                    if(integer(a)&&integer(b)){
#ifdef KASA_ENABLE_BIGINT_VM
                        auto x=exactInt(a),y=exactInt(b);
#else
                        int64_t x=get<int64_t>(a.data),y=get<int64_t>(b.data);
#endif
                        result=i.op==Op::Lt?x<y:i.op==Op::Le?x<=y:i.op==Op::Gt?x>y:x>=y;
                    }else if(integer(a)&&holds_alternative<double>(b.data)){
                        #ifdef KASA_ENABLE_BIGINT_VM
                        int cmp=integerCompareFloat(a,get<double>(b.data));
#else
                        int cmp=numbers::compareIntDouble(get<int64_t>(a.data),get<double>(b.data));
#endif
                        result=i.op==Op::Lt?cmp<0:i.op==Op::Le?cmp<=0:i.op==Op::Gt?cmp>0:cmp>=0;
                    }else if(holds_alternative<double>(a.data)&&integer(b)){
                        #ifdef KASA_ENABLE_BIGINT_VM
                        int cmp=-integerCompareFloat(b,get<double>(a.data));
#else
                        int cmp=-numbers::compareIntDouble(get<int64_t>(b.data),get<double>(a.data));
#endif
                        result=i.op==Op::Lt?cmp<0:i.op==Op::Le?cmp<=0:i.op==Op::Gt?cmp>0:cmp>=0;
                    }else{
                        double x=number(a,i.loc),y=number(b,i.loc);
                        result=i.op==Op::Lt?x<y:i.op==Op::Le?x<=y:i.op==Op::Gt?x>y:x>=y;
                    }
                    stack.push_back(Value(result));break;}
                case Op::CheckBool:{Value x=pop(stack);stack.push_back(Value(truth(x,i.loc)));break;}
                case Op::Jump:ip=static_cast<size_t>(i.number);break;
                case Op::JumpFalse:{Value x=pop(stack);if(!truth(x,i.loc))ip=static_cast<size_t>(i.number);break;}
                case Op::JumpTrue:{Value x=pop(stack);if(truth(x,i.loc))ip=static_cast<size_t>(i.number);break;}
                case Op::MakeList:{auto list=make_shared<List>();if(i.number>static_cast<int>(maxList))error(i.loc,"ResourceError","List is too large");
                    list->items.resize(i.number);for(int x=i.number-1;x>=0;--x)list->items[x]=pop(stack);stack.push_back(Value(list));break;}
                case Op::Index:{Value idx=pop(stack),list=pop(stack);if(!holds_alternative<shared_ptr<List>>(list.data))error(i.loc,"TypeError","Can only index lists");
                    auto v=get<shared_ptr<List>>(list.data);int64_t k=index(idx,i.loc);
                    if(k<0||static_cast<size_t>(k)>=v->items.size())error(i.loc,"IndexError","List index out of range");
                    stack.push_back(v->items[k]);break;}
                case Op::SetIndex:{Value value=pop(stack),idx=pop(stack),list=pop(stack);
                    if(!holds_alternative<shared_ptr<List>>(list.data))error(i.loc,"TypeError","Can only assign list indexes");
                    auto v=get<shared_ptr<List>>(list.data);int64_t k=index(idx,i.loc);
                    if(k<0||static_cast<size_t>(k)>=v->items.size())error(i.loc,"IndexError","List index out of range");
                    v->items[k]=value;break;}
                case Op::CountCheck:{Value v=pop(stack);stack.push_back(Value(count(v,i.loc)));break;}
                case Op::MakeFunction:{auto fn=make_shared<Function>(Function{i.fn,env});env->values[i.name]=Value(fn);break;}
                case Op::Call:{
                    vector<Value>args(i.number);for(int x=i.number-1;x>=0;--x)args[x]=pop(stack);
                    Value callee=pop(stack);
                    if(holds_alternative<Builtin>(callee.data)){stack.push_back(builtin(get<Builtin>(callee.data),args,i.loc));break;}
                    if(!holds_alternative<shared_ptr<Function>>(callee.data))error(i.loc,"TypeError","Value is not callable");
                    auto fn=get<shared_ptr<Function>>(callee.data);
                    if(args.size()!=fn->definition->params.size())error(i.loc,"TypeError","Wrong number of function arguments");
                    if(depth>=64)error(i.loc,"ResourceError","Function call depth exceeded");
                    auto local=makeEnvironment(fn->closure);
                    for(size_t x=0;x<args.size();++x)local->values[fn->definition->params[x]]=args[x];
                    ++depth;try{stack.push_back(runChunk(fn->definition->code,local));}catch(...){--depth;throw;}--depth;break;
                }
                case Op::Return:return pop(stack);
            }
        }
        return Value();
    }
public:
    VM(string filename,ostream&out,istream&in):out(out),in(in),filename(std::move(filename)){}
    ~VM() {
        // VM lifetime ends after output and all ephemeral functions are consumed.
        // Clearing captured scopes breaks shared_ptr cycles even on runtime errors.
        for(auto& weak:trackedEnvironments)if(auto env=weak.lock())env->values.clear();
    }
    void run(shared_ptr<Chunk>code){
        auto env=makeEnvironment();
        for(const char*s:{"bisa","tentɛn","nɔma","nsɛm"})env->values[s]=Value(Builtin{s});
        runChunk(code,env);
    }
};

static const char*opname(Op op){
    switch(op){
      case Op::Constant:return "CONST";case Op::Load:return "LOAD";case Op::Store:return "STORE";case Op::Pop:return "POP";
      case Op::Print:return "PRINT";case Op::Neg:return "NEG";case Op::Not:return "NOT";case Op::Add:return "ADD";
      case Op::Sub:return "SUB";case Op::Mul:return "MUL";case Op::Div:return "DIV";case Op::Mod:return "MOD";
      case Op::Eq:return "EQ";case Op::Ne:return "NE";case Op::Lt:return "LT";case Op::Le:return "LE";case Op::Gt:return "GT";
      case Op::Ge:return "GE";case Op::CheckBool:return "CHECK_BOOL";case Op::Jump:return "JUMP";
      case Op::JumpFalse:return "JUMP_FALSE";case Op::JumpTrue:return "JUMP_TRUE";case Op::MakeList:return "LIST";
      case Op::Index:return "INDEX";case Op::SetIndex:return "INDEX_SET";case Op::MakeFunction:return "FUNCTION";
      case Op::Call:return "CALL";case Op::Return:return "RETURN";case Op::CountCheck:return "COUNT_CHECK";
    }return "?";
}
void disasm(const shared_ptr<Chunk>&c,ostream &out,int indent){
    for(size_t n=0;n<c->code.size();++n){const auto&i=c->code[n];
        out<<string(indent,' ')<<setw(4)<<n<<"  "<<left<<setw(14)<<opname(i.op)<<right;
        if(!i.name.empty()&&i.name[0]!=1)out<<" "<<i.name;
        if(i.op==Op::Constant)out<<" "<<display(i.value);
        if(i.op==Op::Jump||i.op==Op::JumpFalse||i.op==Op::JumpTrue||i.op==Op::Call||i.op==Op::MakeList)out<<" "<<i.number;
        out<<"\n";
        if(i.op==Op::MakeFunction&&i.fn){out<<string(indent+2,' ')<<"<"<<i.fn->name<<">\n";disasm(i.fn->code,out,indent+4);}
    }
}

void runProgram(shared_ptr<Chunk>code,const string&filename,ostream&out,istream&in){
    VM(filename,out,in).run(code);
}
} // namespace kasa
