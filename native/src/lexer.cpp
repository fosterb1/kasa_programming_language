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
static bool idstart(unsigned char c){return isalpha(c) || c=='_' || c>=128;}
static bool idcont(unsigned char c){return idstart(c) || isdigit(c);}
static const unordered_map<string,string> words={
 {"ka","PRINT"},{"ma","ASSIGN"},{"sɛ","IF"},{"anyɛ_saa_a","ELSE"},
 {"mpɛn","REPEAT"},{"bere_a","WHILE"},{"dwumadie","FUNCTION"},
 {"sanma","RETURN"},{"awiei","END"},{"nokware","TRUE"},
 {"atoro","FALSE"},{"hwee","NONE"},{"ne","AND"},{"anaa","OR"},
 {"ɛnyɛ","NOT"},{"gyae","BREAK"},{"toa_so","CONTINUE"}};

vector<Token> lex(string src, const string &file){
    vector<Token> tokens;size_t i=0;int line=1,col=1;
    auto take=[&](){char ch=src.at(i++);if(ch=='\n'){++line;col=1;}else ++col;return ch;};
    auto add=[&](string kind,string text,int l,int c){tokens.push_back({move(kind),move(text),l,c});};
    while(i<src.size()){
        unsigned char ch=static_cast<unsigned char>(src[i]);int l=line,c=col;
        if(ch==' '||ch=='\t'){take();continue;}
        if(ch=='\r'){++i; if(i<src.size()&&src[i]=='\n')++i; ++line;col=1;add("NEWLINE","\\n",l,c);continue;}
        if(ch=='\n'){take();add("NEWLINE","\\n",l,c);continue;}
        if(ch=='#'){while(i<src.size()&&src[i]!='\n'&&src[i]!='\r')take();continue;}
        if(ch=='"'){
            take();string content;bool complete=false;
            while(i<src.size()&&src[i]!='\n'&&src[i]!='\r'){
                char x=take();if(x=='"'){complete=true;break;}
                if(x=='\\'){
                    if(i>=src.size())throw Failure({"STRING","",l,c},"SyntaxError","Unterminated string escape",file);
                    char e=take();switch(e){case 'n':x='\n';break;case 'r':x='\r';break;case 't':x='\t';break;case '"':x='"';break;case '\\':x='\\';break;
                    default:throw Failure({"STRING","",l,c},"SyntaxError","Unsupported string escape",file);}
                }
                content+=x;
            }
            if(!complete)throw Failure({"STRING","",l,c},"SyntaxError","Unterminated string literal",file);
            add("STRING",content,l,c);continue;
        }
        if(ch>='0'&&ch<='9'){
            string num;while(i<src.size()&&src[i]>='0'&&src[i]<='9')num+=take();string kind="INTEGER";
            if(i+1<src.size()&&src[i]=='.'&&src[i+1]>='0'&&src[i+1]<='9'){
                kind="DECIMAL";num+=take();while(i<src.size()&&src[i]>='0'&&src[i]<='9')num+=take();
            }
            if(num.size()>1000)throw Failure({kind,"",l,c},"SyntaxError","Number is too long",file);
            add(kind,num,l,c);continue;
        }
        if(idstart(ch)){
            string id;while(i<src.size()&&idcont(static_cast<unsigned char>(src[i])))id+=take();
            auto p=words.find(id);add(p==words.end()?"NAME":p->second,id,l,c);continue;
        }
        string pair=src.substr(i,2);
        if(pair=="=="||pair=="!="||pair=="<="||pair==">="){take();take();add(pair,pair,l,c);continue;}
        if(string("+-*/%<>=()[],").find(static_cast<char>(ch))!=string::npos){string op(1,take());add(op,op,l,c);continue;}
        throw Failure({"INVALID",string(1,static_cast<char>(ch)),l,c},"SyntaxError","Unexpected character",file);
    }
    if(tokens.size()>200000)throw Failure({"EOF","",line,col},"ResourceError","Too many source tokens",file);
    add("EOF","",line,col);return tokens;
}

} // namespace kasa
