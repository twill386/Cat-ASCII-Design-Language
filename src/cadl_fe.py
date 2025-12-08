"""
Frontend for our CADL language - builds an AST where each
node is of the shape,

    (TYPE, [arg1, arg2, arg3,...])

Here TYPE is a string describing the node type.
"""

# stmt_list : ({CAT,ID,FUNC,DRAW,RANDOMCAT,RETURN,WHILE,IF,LCURLY} stmt)*
def stmt_list(stream):
    lst = []
    while stream.pointer().type in [
        'CAT', 'ID', 'FUNC', 'DRAW', 'RANDOMCAT',
        'RETURN', 'WHILE', 'IF', 'LCURLY'
    ]:
        s = stmt(stream)
        lst.append(s)
    return ('STMTLIST', lst)

# stmt :
#    {CAT}      CAT ID cat_suffix
#  | {FUNC}     FUNC ID func_suffix
#  | {DRAW}     DRAW ID ({SEMI} SEMI)?
#  | {RANDOMCAT} RANDOMCAT ID ({SEMI} SEMI)?
#  | {ID}       ID id_suffix
#  | {RETURN}   RETURN ({INTEGER,ID,STRING,LPAREN,NOT} exp)? ({SEMI} SEMI)?
#  | {WHILE}    WHILE LPAREN exp RPAREN stmt
#  | {IF}       IF LPAREN exp RPAREN stmt ({ELSE} ELSE stmt)?
#  | {LCURLY}   LCURLY stmt_list RCURLY
def stmt(stream):
    t = stream.pointer().type

    # cat declarations
    if t in ['CAT']:
        stream.match('CAT')
        id_tok = stream.match('ID')
        s = cat_suffix(stream, id_tok.value)
        return s

    # function declarations
    elif t in ['FUNC']:
        stream.match('FUNC')
        id_tok = stream.match('ID')
        s = func_suffix(stream, id_tok.value)
        return s

    # draw statements
    elif t in ['DRAW']:
        stream.match('DRAW')
        id_tk = stream.match('ID')
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return ('DRAW', ('ID', id_tk.value))

    # randomcat declaration (e.g., randomcat x;)
    elif t in ['RANDOMCAT']:
        stream.match('RANDOMCAT')
        id_tk = stream.match('ID')
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return ('RANDOMCATDECL', ('ID', id_tk.value))

    # ID statements: trait assign, randomcat assign, call, normal assign
    elif t in ['ID']:
        id_tok = stream.match('ID')
        e = id_suffix(stream)

        if e[0] == 'LIST':
            # function call statement
            return ('CALLSTMT', ('ID', id_tok.value), e)
        elif e[0] == 'TRAITASSIGN_RHS':
            (_, trait_id, rhs) = e
            return ('TRAITASSIGN', ('ID', id_tok.value), trait_id, rhs)
        elif e[0] == 'ASSIGN_RANDOMCAT_RHS':
            return ('ASSIGN_RANDOMCAT', ('ID', id_tok.value))
        else:
            # normal assignment: ID = exp;
            return ('ASSIGN', ('ID', id_tok.value), e)

    # RETURN
    elif t in ['RETURN']:
        stream.match('RETURN')
        if stream.pointer().type in ['INTEGER', 'ID', 'STRING', 'LPAREN', 'NOT']:
            e = exp(stream)
        else:
            e = ('NIL',)
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return ('RETURN', e)

    # WHILE loop
    elif t in ['WHILE']:
        stream.match('WHILE')
        stream.match('LPAREN')
        e = exp(stream)
        stream.match('RPAREN')
        s = stmt(stream)
        return ('WHILE', e, s)

    # IF / ELSE
    elif t in ['IF']:
        stream.match('IF')
        stream.match('LPAREN')
        e = exp(stream)
        stream.match('RPAREN')
        s1 = stmt(stream)
        if stream.pointer().type in ['ELSE']:
            stream.match('ELSE')
            s2 = stmt(stream)
            return ('IF', e, s1, s2)
        else:
            return ('IF', e, s1, ('NIL',))

    # BLOCK
    elif t in ['LCURLY']:
        stream.match('LCURLY')
        sl = stmt_list(stream)
        stream.match('RCURLY')
        return ('BLOCK', sl)

    else:
        raise SyntaxError("stmt: syntax error at {}"
                          .format(stream.pointer().value))

# cat_suffix :
#    {LCURLY} LCURLY trait_list RCURLY
#  | {SEMI}   SEMI
def cat_suffix(stream, cat_name):
    if stream.pointer().type in ['LCURLY']:
        stream.match('LCURLY')
        traits = trait_list(stream)
        stream.match('RCURLY')
        return ('CATDECL', ('ID', cat_name), traits)
    elif stream.pointer().type in ['SEMI']:
        stream.match('SEMI')
        return ('CATDECL_SIMPLE', ('ID', cat_name))
    else:
        raise SyntaxError("cat_suffix: syntax error at {}"
                          .format(stream.pointer().value))

# func_suffix :
#    {LPAREN} LPAREN params RPAREN stmt
# stmt will return a block
def func_suffix(stream, func_name):
    if stream.pointer().type in ['LPAREN']:
        stream.match('LPAREN')
        params = params_list(stream)
        stream.match('RPAREN')
        body = stmt(stream)
        return ('FUNDECL', ('ID', func_name), params, body)
    else:
        raise SyntaxError("func_suffix: syntax error at {}"
                          .format(stream.pointer().value))

# params_list : {ID} ID ({COMMA} COMMA ID)* | /* empty */
def params_list(stream):
    if stream.pointer().type in ['ID']:
        id_tok = stream.match('ID')
        ll = [('ID', id_tok.value)]
        while stream.pointer().type in ['COMMA']:
            stream.match('COMMA')
            id_tok = stream.match('ID')
            ll.append(('ID', id_tok.value))
        return ('LIST', ll)
    else:
        # empty parameter list
        return ('LIST', [])

# trait_list : ({ID} trait)+
# trait      : {ID} ID ASSIGN exp ({SEMI} SEMI)?
def trait_list(stream):
    lst = []
    if stream.pointer().type not in ['ID']:
        raise SyntaxError("trait_list: expected trait at {}"
                          .format(stream.pointer().value))
    while stream.pointer().type in ['ID']:
        lst.append(trait(stream))
    return ('LIST', lst)


def trait(stream):
    id_tok = stream.match('ID')
    stream.match('ASSIGN')
    e = exp(stream)
    if stream.pointer().type in ['SEMI']:
        stream.match('SEMI')
    return ('TRAIT', ('ID', id_tok.value), e)

# id_suffix :
#    {DOT}    DOT ID ASSIGN exp ({SEMI} SEMI)?
#  | {ASSIGN} ASSIGN RANDOMCAT ({SEMI} SEMI)?
#  | {LPAREN} LPAREN actual_args? RPAREN ({SEMI} SEMI)?
#  | {ASSIGN} ASSIGN exp ({SEMI} SEMI)?
#
# This Returns:
#   ('TRAITASSIGN_RHS', ('ID', traitName), expr)
#   ('ASSIGN_RANDOMCAT_RHS',)
#   ('LIST', [...])
#   <expr>
def id_suffix(stream):
    t = stream.pointer().type

    # Trait assignment: ID . ID = exp ;
    if t in ['DOT']:
        stream.match('DOT')
        trait_tok = stream.match('ID')
        stream.match('ASSIGN')
        e = exp(stream)
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return ('TRAITASSIGN_RHS', ('ID', trait_tok.value), e)

    # Assignment to randomcat: ID = randomcat ;
    elif t in ['ASSIGN'] and _peek(stream) in ['RANDOMCAT']:
        stream.match('ASSIGN')
        stream.match('RANDOMCAT')
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return ('ASSIGN_RANDOMCAT_RHS',)

    # Function call statement: ID ( actual_args? ) ;
    elif t in ['LPAREN']:
        stream.match('LPAREN')
        if stream.pointer().type in ['INTEGER', 'ID', 'STRING', 'LPAREN', 'NOT']:
            args = actual_args(stream)
        else:
            args = ('LIST', [])
        stream.match('RPAREN')
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return args  # ('LIST', ...)

    # Normal assignment: ID = exp ;
    elif t in ['ASSIGN']:
        stream.match('ASSIGN')
        e = exp(stream)
        if stream.pointer().type in ['SEMI']:
            stream.match('SEMI')
        return e

    else:
        raise SyntaxError("id_suffix: syntax error at {}"
                          .format(stream.pointer().value))

def _peek(stream):
    """Look one token ahead without consuming."""
    return stream.tokens[stream.curr_token_ix + 1].type

# exp : {INTEGER,ID,STRING,LPAREN,NOT} equality
def exp(stream):
    if stream.pointer().type in ['INTEGER', 'ID', 'STRING', 'LPAREN', 'NOT']:
        e = equality(stream)
        return e
    else:
        raise SyntaxError("exp: syntax error at {}"
                          .format(stream.pointer().value))

# equality :
#   {INTEGER,ID,STRING,LPAREN,NOT} primary ({EQ,NOTEQ} (EQ|NOTEQ) primary)*
def equality(stream):
    if stream.pointer().type in ['INTEGER', 'ID', 'STRING', 'LPAREN', 'NOT']:
        e = primary(stream)
        while stream.pointer().type in ['EQ', 'NOTEQ']:
            op_tk = stream.match(stream.pointer().type)  # EQ or NOTEQ
            tmp = primary(stream)
            e = (op_tk.type, e, tmp)
        return e
    else:
        raise SyntaxError("equality: syntax error at {}"
                          .format(stream.pointer().value))

# primary :
#    {INTEGER} INTEGER
#  | {STRING}  STRING
#  | {ID}      ID ( primary ID-suffix for call/attr )?
#  | {LPAREN}  LPAREN exp RPAREN
#  | {NOT}     NOT primary
#
#  ID:
#   - plain ID        ('ID', name)
#   - call expr       ('CALLEXP', ('ID', name), args)
#   - attribute expr  ('ATTR', ('ID', name), ('ID', trait))
def primary(stream):
    if stream.pointer().type in ['INTEGER']:
        tk = stream.match('INTEGER')
        return ('INTEGER', int(tk.value))

    elif stream.pointer().type in ['STRING']:
        tk = stream.match('STRING')
        return ('STRING', tk.value)

    elif stream.pointer().type in ['ID']:
        id_tk = stream.match('ID')
        # Could be attribute or call or just ID
        if stream.pointer().type in ['DOT']:
            stream.match('DOT')
            trait_tk = stream.match('ID')
            return ('ATTR', ('ID', id_tk.value), ('ID', trait_tk.value))
        elif stream.pointer().type in ['LPAREN']:
            stream.match('LPAREN')
            if stream.pointer().type in ['INTEGER', 'ID', 'STRING', 'LPAREN', 'NOT']:
                args = actual_args(stream)
            else:
                args = ('LIST', [])
            stream.match('RPAREN')
            return ('CALLEXP', ('ID', id_tk.value), args)
        else:
            return ('ID', id_tk.value)

    elif stream.pointer().type in ['LPAREN']:
        stream.match('LPAREN')
        e = exp(stream)
        stream.match('RPAREN')
        return e

    elif stream.pointer().type in ['NOT']:
        stream.match('NOT')
        e = primary(stream)
        return ('NOT', e)

    else:
        raise SyntaxError("primary: syntax error at {}"
                          .format(stream.pointer().value))


# ------------------------------------------------------------
# actual_args : {INTEGER,ID,STRING,LPAREN,NOT} exp ({COMMA} COMMA exp)*
# ------------------------------------------------------------
def actual_args(stream):
    if stream.pointer().type in ['INTEGER', 'ID', 'STRING', 'LPAREN', 'NOT']:
        e = exp(stream)
        ll = [e]
        while stream.pointer().type in ['COMMA']:
            stream.match('COMMA')
            e = exp(stream)
            ll.append(e)
        return ('LIST', ll)
    else:
        raise SyntaxError("actual_args: syntax error at {}"
                          .format(stream.pointer().value))

# frontend top-level driver
def parse(stream):
    from cadl_lexer import Lexer
    token_stream = Lexer(stream)
    sl = stmt_list(token_stream)
    if not token_stream.end_of_file():
        raise SyntaxError("parse: syntax error at {}"
                          .format(token_stream.pointer().value))
    else:
        return sl


if __name__ == "__main__":
    import sys
    from cadl_interp_walk import CADLInterpWalk

    if len(sys.argv) < 2:
        print("Usage: python3 cadl_fe.py <sourcefile>")
        sys.exit(1)

    filename = sys.argv[1]
    with open(filename, "r") as f:
        source = f.read()

    ast = parse(source)
    interp = CADLInterpWalk()
    interp.visit(ast)