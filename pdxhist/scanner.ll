
/* basic startup scanner for reacclimating myself with flex */

%option 8bit
%option warn nodefault
%option yylineno
%option noyymore noyywrap
%option batch
%option nounistd never-interactive

%top{
	#include "token.h"
}

DIGIT		[0-9]
STR		[a-zA-Z0-9_\-]+
WS		[ \t\r\n\xA0]+
QSTR		\"[^"\n]+\"

%%

{DIGIT}{1,4}"."{DIGIT}{1,2}"."{DIGIT}{1,2}	{ return token::DATE; }
"-"?{DIGIT}+"."{DIGIT}+		{ return token::FLOAT; }
"-"?{DIGIT}+	{ return token::INT; }
"="		{ return token::EQ; }
"{"		{ return token::OPEN; }
"}"		{ return token::CLOSE; }
{STR}		{ return token::STR; }
{QSTR}		{ return token::QSTR; }
"#".*$		{ return token::COMMENT; }
{WS}+		/* skip */
.		{ return token::FAIL; }

%%
