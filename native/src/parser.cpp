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
E expr(string kind,const Token&t,string op="",Value val={},vector<E>kids={}){return make_shared<Expr>(Expr{std::move(kind),std::move(op),t,std::move(val),std::move(kids)});}
S statement(string kind,Token t){auto s=make_shared<Stmt>();s->kind=std::move(kind);s->token=t;return s;}

class Parser{
    vector<Token> t;size_t i=0;string file;int nesting=0;
    struct Nest {Parser &p;explicit Nest(Parser&p):p(p){if(++p.nesting>200)throw Failure(p.cur(),"ResourceError","Syntax nesting limit exceeded",p.file);}~Nest(){--p.nesting;}};
    const Token &cur() const{return t.at(i);}
    bool match(const string&k){if(cur().kind==k){++i;return true;}return false;}
    Token require(const string&k,const string&message=""){
        if(cur().kind!=k)throw Failure(cur(),"SyntaxError",message.empty()?"Expected '"+k+"'":message,file);
        return t.at(i++);
    }
    void nl(){while(match("NEWLINE")){} }
    void eol(){if(cur().kind!="EOF")require("NEWLINE","Expected a new line");}
    static int precedence(const string&k){
        if(k=="OR")return 10;
        if(k=="AND")return 20;
        if(k=="=="||k=="!=")return 30;
        if(k=="<"||k=="<="||k==">"||k==">=")return 40;
        if(k=="+"||k=="-")return 50;
        if(k=="*"||k=="/"||k=="%")return 60;
        return -1;
    }
    E primary(){
        Token x=cur();
        if(match("-"))return expr("unary",x,"-",{}, {expression(70)});
        if(match("NOT"))return expr("unary",x,"NOT",{}, {expression(70)});
        if(match("INTEGER")){
            try{return expr("literal",x,"",Value(static_cast<int64_t>(stoll(x.text))));}catch(...){throw Failure(x,"ResourceError","Integer literal exceeds 64-bit native range",file);}
        }
        if(match("DECIMAL")){
            try{double val=stod(x.text);if(!isfinite(val))throw out_of_range("nonfinite");return expr("literal",x,"",Value(val));}
            catch(...){throw Failure(x,"ResourceError","Decimal literal exceeds supported range",file);}
        }
        if(match("STRING"))return expr("literal",x,"",Value(x.text));
        if(match("TRUE"))return expr("literal",x,"",Value(true));
        if(match("FALSE"))return expr("literal",x,"",Value(false));
        if(match("NONE"))return expr("literal",x,"",Value());
        if(match("NAME"))return expr("name",x,x.text);
        if(match("(")){E result=expression();require(")","Expected closing ')' ");return result;}
        if(match("[")){
            vector<E> children;
            if(cur().kind!="]")while(true){children.push_back(expression());if(!match(","))break;}
            require("]","Expected closing ']'");return expr("list",x,"",{},std::move(children));
        }
        throw Failure(cur(),"SyntaxError","Expected an expression",file);
    }
    E expression(int minp=0){
        Nest guard(*this);
        E left=primary();bool compared=false;
        while(true){Token op=cur();
            if((op.kind=="("||op.kind=="[")&&80>=minp){
                ++i;
                if(op.kind=="("){
                    vector<E> a={left};if(cur().kind!=")")while(true){a.push_back(expression());if(!match(","))break;}
                    require(")","Expected ')' after function arguments");left=expr("call",op,"",{},std::move(a));
                }else{E key=expression();require("]","Expected ']' after list index");left=expr("index",op,"",{}, {left,key});}
                continue;
            }
            int p=precedence(op.kind);if(p<minp)break;
            if(p==40||p==30){if(compared)throw Failure(op,"SyntaxError","Comparison chaining is not supported",file);compared=true;}
            ++i;E right=expression(p+1);left=expr("binary",op,op.kind,{}, {left,right});
        }return left;
    }
    vector<S> block(const vector<string>&stop){
        Nest guard(*this);
        vector<S> out;nl();
        while(find(stop.begin(),stop.end(),cur().kind)==stop.end()){
            if(cur().kind=="EOF")throw Failure(cur(),"SyntaxError","Missing 'awiei' before end of file",file);
            if(cur().kind=="ELSE"||cur().kind=="END")throw Failure(cur(),"SyntaxError","Unexpected block delimiter",file);
            out.push_back(parseStatement());nl();
        }return out;
    }
    S parseStatement(){
        Token x=cur();
        if(match("PRINT")){auto s=statement("print",x);s->a=expression();eol();return s;}
        if(match("ASSIGN")){
            auto s=statement("assign",x);s->a=expression();
            if(s->a->kind!="name"&&s->a->kind!="index")throw Failure(x,"SyntaxError","Assignment target must be a variable or list index",file);
            // Index targets must ultimately refer to an existing variable.
            auto v=s->a;while(v->kind=="index")v=v->kids.at(0);
            if(v->kind!="name")throw Failure(x,"SyntaxError","List assignment must start with a variable",file);
            require("=","Expected '=' in assignment");s->b=expression();eol();return s;
        }
        if(match("IF")){
            auto s=statement("if",x);s->a=expression();Token mark=require("NAME","Expected 'a' after condition");
            if(mark.text!="a")throw Failure(mark,"SyntaxError","Expected 'a' after condition",file);
            eol();s->yes=block({"ELSE","END"});if(match("ELSE")){eol();s->no=block({"END"});}
            require("END","Expected 'awiei' to finish conditional");eol();return s;
        }
        if(match("REPEAT")||match("WHILE")){
            auto s=statement(x.kind=="REPEAT"?"repeat":"while",x);s->a=expression();eol();s->yes=block({"END"});
            require("END","Expected 'awiei' to finish loop");eol();return s;
        }
        if(match("FUNCTION")){
            auto s=statement("function",x);s->name=require("NAME","Expected function name").text;require("(");
            if(cur().kind!=")")while(true){string p=require("NAME","Expected parameter name").text;
                if(find(s->params.begin(),s->params.end(),p)!=s->params.end())throw Failure(x,"SyntaxError","Duplicate function parameter",file);
                s->params.push_back(p);if(!match(","))break;
            }
            require(")");eol();s->yes=block({"END"});require("END","Expected 'awiei' to finish function");eol();return s;
        }
        if(match("RETURN")){auto s=statement("return",x);if(cur().kind!="NEWLINE"&&cur().kind!="EOF")s->a=expression();eol();return s;}
        if(match("BREAK")){auto s=statement("break",x);eol();return s;}
        if(match("CONTINUE")){auto s=statement("continue",x);eol();return s;}
        auto s=statement("expression",x);s->a=expression();eol();return s;
    }
public:
    Parser(vector<Token> t,string filename):t(std::move(t)),file(std::move(filename)){}
    vector<S> parse(){auto body=block({"EOF"});require("EOF");return body;}
};


vector<S> parseSource(vector<Token> tokens,const string &filename){
    return Parser(std::move(tokens),filename).parse();
}
} // namespace kasa
