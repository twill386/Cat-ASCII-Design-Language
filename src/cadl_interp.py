#!/usr/bin/env python
"""
CADL Interpreter

This file is a lightly modified version of cuppa3_interp.py.
It puts together:
  - CADL lexer / parser front-end
  - CADL AST
  - CADL interpreter walker
  - Symbol table

The actual execution of the CADL program is handled by:
  - CADLInterpWalk
"""

from cadl_fe import parse        
from cadl_interp_walk import CADLInterpWalk
from cadl_symtab import symtab
from dumpast import dumpast

def interp(input_stream, dump=False, exceptions=False):
    try:
        # Reset symbol table before each run
        symtab.initialize()

        # Parse CADL source to AST
        ast = parse(input_stream)

        # Dump AST if requested
        if dump:
            dumpast(ast)
            return None

        # Interpret (execute CADL program)
        walker = CADLInterpWalk()
        walker.visit(ast)

    except Exception as e:
        if exceptions:
            raise e  # rethrow for visibility
        else:
            print("error: " + str(e))

    return None


if __name__ == "__main__":
    import sys
    import os

    ast_switch = False
    except_switch = False

    # CASE 1: FILE PROVIDED, run normally
    ########################################################
    if len(sys.argv) > 1:
        args = sys.argv[1:-1]      # all except last
        input_file = sys.argv[-1]  # last argument

        ast_switch = "-d" in args
        except_switch = "-e" in args

        if not os.path.isfile(input_file):
            print(f"unknown file {input_file}")
            sys.exit(0)

        with open(input_file, "r") as f:
            char_stream = f.read()

        interp(char_stream, dump=ast_switch, exceptions=except_switch)
        sys.exit(0)

    # CASE 2: NO FILE PROVIDED, INTERACTIVE MODE
    ########################################################
    print("CADL Interactive Mode (type 'exit' to quit)")
    walker = CADLInterpWalk()
    symtab.initialize()

    while True:
        try:
            line = input("CADL> ")
            if line.strip().lower() in ["exit", "quit"]:
                break

            ast = parse(line)
            walker.visit(ast)

        except Exception as e:
            print("error:", e)