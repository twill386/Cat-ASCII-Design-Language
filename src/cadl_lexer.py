'''
Lexer for CADL language

This lexer converts a CADL program into a stream of tokens that 
the parser can understand. It scans the source code and matches 
patterns using the token specs provided. Each match becomes a 
token object (type, value).
'''

import re

token_specs = [
#   type:          value:

    # Comments and Whitespace
    ('COMMENT',    r'//.*'),
    ('WHITESPACE', r'[ \t\n]+'),
    # CADL keywords
    ('CAT',        r'cat'),
    ('FUNC',       r'func'),
    ('DRAW',       r'draw'),
    ('RANDOMCAT',  r'randomcat'),
    ('RETURN',     r'return'),    
    ('WHILE',      r'while'),
    ('IF',         r'if'),
    ('ELSE',       r'else'),
    ('NOT',        r'not'),
    # Operators
    ('EQ',         r'=='),
    ('NOTEQ',     r'!='),
    ('ASSIGN',     r'='),
    ('DOT',        r'\.'),
    # Punctuation
    ('LPAREN',     r'\('),
    ('RPAREN',     r'\)'),
    ('LCURLY',     r'{'),
    ('RCURLY',     r'}'),
    ('SEMI',       r';'),
    ('COMMA',      r','),
    # Literals
    ('STRING',     r'"[^"]*"'),
    ('INTEGER',    r'[0-9]+'),
    #ID / Unkown
    ('ID',         r'[a-zA-Z][a-zA-Z0-9_]*'),
    ('UNKNOWN',    r'.'),
]

# used for sanity checking in lexer.
token_types = set(type for (type,_) in token_specs)

class Token:
    def __init__(self,type,value):
        self.type = type
        self.value = value

    def __str__(self):
        return 'Token({},{})'.format(self.type,self.value)

def tokenize(code):
    tokens = []
    re_list = ['(?P<{}>{})'.format(type,re) for (type,re) in token_specs]
    combined_re = '|'.join(re_list)
    match_object_list = list(re.finditer(combined_re, code))
    for mo in match_object_list:
        type = mo.lastgroup
        value = mo.group()
        if type in ['WHITESPACE','COMMENT']:
            continue #ignore
        elif type == 'UNKNOWN':
            raise ValueError("unexpected character '{}'".format(value))
        else:
            tokens.append(Token(type, value))
    tokens.append(Token('EOF', r'\eof'))
    return tokens

class Lexer:
    def __init__(self, input_string):
        self.tokens = tokenize(input_string)
        # the following is always valid because we will always have
        # at least the EOF token on the tokens list.
        self.curr_token_ix = 0

    def pointer(self):
        return self.tokens[self.curr_token_ix]

    def next(self):
        if not self.end_of_file():
            self.curr_token_ix += 1
        return self.pointer()

    def match(self, token_type):
        if token_type == self.pointer().type:
            tk = self.pointer()
            self.next()
            return tk
        elif token_type not in token_types:
            raise ValueError("unknown token type '{}'".format(token_type))
        else:
            raise SyntaxError('unexpected token {} while parsing, expected {}'
                              .format(self.pointer().type, token_type))

    def end_of_file(self):
        if self.pointer().type == 'EOF':
            return True
        else:
            return False

# test lexer
if __name__ == "__main__":

    prgm = \
    '''
    // test
    cat Miso {
    mood = happy;
    }

    draw Miso;
    '''
    lexer = Lexer(prgm)

    while not lexer.end_of_file():
        tok = lexer.pointer()
        print(tok)
        lexer.match(tok.type)