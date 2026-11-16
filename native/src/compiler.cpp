#include "kasa/native.hpp"
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
#include <sstream>
#include <stdexcept>
#include <string>
#include <unordered_map>
#include <utility>
#include <variant>
#include <vector>
#include <cctype>
namespace kasa {
using namespace std;
class Compiler{
    string filename;shared_ptr<Chunk> code=make_shared<Chunk>();
    struct Loop{vector<int> breaks,continues;};vector<Loop> loops;
    bool insideFunction=false;int temporary=0;
    int emit(Op op,const Token&t,int n=0,string name="",Value val={},shared_ptr<FunctionDefinition> fn=nullptr){
        code->code.push_back({op,t,n,std::move(name),std::move(val),std::move(fn)});return static_cast<int>(code->code.size()-1);
    }
    void patch(int index,int destination){code->code.at(index).number=destination;}
    int pc()const{return static_cast<int>(code->code.size());}
    void expression(const E&e){
        if(e->kind=="literal"){emit(Op::Constant,e->token,0,"",e->value);return;}
        if(e->kind=="name"){emit(Op::Load,e->token,0,e->op);return;}
        if(e->kind=="list"){
            for(auto&x:e->kids)expression(x);
            emit(Op::MakeList,e->token,static_cast<int>(e->kids.size()));return;
        }
        if(e->kind=="index"){expression(e->kids[0]);expression(e->kids[1]);emit(Op::Index,e->token);return;}
        if(e->kind=="call"){
            for(const auto&x:e->kids)expression(x);
            emit(Op::Call,e->token,static_cast<int>(e->kids.size()-1));return;
        }
        if(e->kind=="unary"){
            expression(e->kids[0]);emit(e->op=="-"?Op::Neg:Op::Not,e->token);return;
        }
        if(e->kind=="binary"){
            const string&k=e->op;
            if(k=="AND"||k=="OR"){
                expression(e->kids[0]);emit(Op::CheckBool,e->token);
                int shortcut=emit(k=="AND"?Op::JumpFalse:Op::JumpTrue,e->token,-1);
                expression(e->kids[1]);emit(Op::CheckBool,e->token);
                int end=emit(Op::Jump,e->token,-1);
                patch(shortcut,pc());emit(Op::Constant,e->token,0,"",Value(k=="OR"));patch(end,pc());return;
            }
            expression(e->kids[0]);expression(e->kids[1]);
            static const map<string,Op> ops={{"+",Op::Add},{"-",Op::Sub},{"*",Op::Mul},{"/",Op::Div},{"%",Op::Mod},
                {"==",Op::Eq},{"!=",Op::Ne},{"<",Op::Lt},{"<=",Op::Le},{">",Op::Gt},{">=",Op::Ge}};
            emit(ops.at(k),e->token);return;
        }
        throw Failure(e->token,"CompilerError","Unsupported expression",filename);
    }
    void statements(const vector<S>&body){for(auto&s:body)statement(s);}
    void statement(const S&s){
        const auto&t=s->token;
        if(s->kind=="print"){expression(s->a);emit(Op::Print,t);return;}
        if(s->kind=="expression"){expression(s->a);emit(Op::Pop,t);return;}
        if(s->kind=="assign"){
            if(s->a->kind=="name"){expression(s->b);emit(Op::Store,t,0,s->a->op);}
            else{expression(s->a->kids[0]);expression(s->a->kids[1]);expression(s->b);emit(Op::SetIndex,t);}
            return;
        }
        if(s->kind=="if"){
            expression(s->a);int jfalse=emit(Op::JumpFalse,t,-1);
            statements(s->yes);int jend=emit(Op::Jump,t,-1);patch(jfalse,pc());statements(s->no);patch(jend,pc());return;
        }
        if(s->kind=="while"){
            int begin=pc();expression(s->a);int jexit=emit(Op::JumpFalse,t,-1);
            loops.emplace_back();statements(s->yes);
            auto loop=std::move(loops.back());loops.pop_back();
            for(int j:loop.continues)patch(j,begin);
            emit(Op::Jump,t,begin);patch(jexit,pc());for(int j:loop.breaks)patch(j,pc());return;
        }
        if(s->kind=="repeat"){
            string key="\x01count_"+to_string(++temporary);
            expression(s->a);emit(Op::CountCheck,t);emit(Op::Store,t,0,key);
            int begin=pc();emit(Op::Load,t,0,key);emit(Op::Constant,t,0,"",Value(int64_t(0)));emit(Op::Gt,t);
            int jexit=emit(Op::JumpFalse,t,-1);loops.emplace_back();statements(s->yes);
            auto loop=std::move(loops.back());loops.pop_back();
            int next=pc();for(int j:loop.continues)patch(j,next);
            emit(Op::Load,t,0,key);emit(Op::Constant,t,0,"",Value(int64_t(1)));emit(Op::Sub,t);emit(Op::Store,t,0,key);
            emit(Op::Jump,t,begin);patch(jexit,pc());for(int j:loop.breaks)patch(j,pc());return;
        }
        if(s->kind=="break"||s->kind=="continue"){
            if(loops.empty())throw Failure(t,"SyntaxError","'"+(s->kind=="break"?string("gyae"):string("toa_so"))+"' outside a loop",filename);
            int j=emit(Op::Jump,t,-1);
            if(s->kind=="break")loops.back().breaks.push_back(j);else loops.back().continues.push_back(j);return;
        }
        if(s->kind=="function"){
            Compiler inner(filename,true);inner.statements(s->yes);inner.emit(Op::Constant,t);inner.emit(Op::Return,t);
            auto def=make_shared<FunctionDefinition>(FunctionDefinition{s->name,s->params,inner.code});
            emit(Op::MakeFunction,t,0,s->name,{},def);return;
        }
        if(s->kind=="return"){
            if(!insideFunction)throw Failure(t,"SyntaxError","'sanma' outside a function",filename);
            if(s->a)expression(s->a);else emit(Op::Constant,t);
            emit(Op::Return,t);return;
        }
        throw Failure(t,"CompilerError","Unsupported statement",filename);
    }
public:
    Compiler(string filename,bool function=false):filename(std::move(filename)),insideFunction(function){}
    shared_ptr<Chunk> compile(const vector<S>&body){statements(body);return code;}
};


shared_ptr<Chunk> compileProgram(const vector<S>&stmts,const string&filename){
    return Compiler(filename).compile(stmts);
}
} // namespace kasa
