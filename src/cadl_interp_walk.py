"""
CADL Interpreter Walker

This interpreter is able to support the following
- cat declarations
- trait assignment and access
- mood override logic
- RANDOMCAT generation
- draw statements
"""

from cadl_symtab import symtab
import random
from cadl_ascii_render import render_cat


class CADLInterpWalk:

    def __init__(self):
        self.return_flag = False
        self.return_value = None

    # Mood Override
    ####################################################################
    def apply_mood_override(self, cat):
        """
        Adjust cat traits based on mood.
        """
        traits = cat["traits"]
        mouth_locked = "mouth" in traits
        mood = traits.get("mood")

        if mood is None:
            return cat

        mood = mood.lower()

        if mood == "sleepy":
            traits["ears"] = "droopy"
            if not mouth_locked:
                traits["mouth"] = "neutral"
            traits["whiskers"] = "short"

        elif mood == "happy":
            if not mouth_locked:
                traits["mouth"] = "smile"
            traits["ears"] = "short"
            traits["whiskers"] = "long"

        elif mood == "angry":
            if not mouth_locked:
                traits["mouth"] = "scowl"
            traits["ears"] = "round"
            traits["whiskers"] = "curled"

        elif mood == "loving":
            if not mouth_locked:
                traits["mouth"] = "kiss"
            traits["ears"] = "pointy"
            traits["whiskers"] = "long"

        elif mood == "curious":
            traits["ears"] = "short"
            if not mouth_locked:
                traits["mouth"] = None
            traits["whiskers"] = "long"

        elif mood == "excited":
            if not mouth_locked:
                traits["mouth"] = "open"
            traits["ears"] = "long"
            traits["whiskers"] = "long"
        
        elif mood == "sad":
            if not mouth_locked:
                traits["mouth"] = "frown"
            traits["ears"] = "droopy"
            traits["whiskers"] = "short"


        return cat

    # Tuple AST Interpreter (used by cadl_fe.py)
    ###############################################################
    def visitTuple(self, node):
        tag = node[0]

        # STMTLIST
        if tag == "STMTLIST":
            for s in node[1]:
                self.visit(s)
                if self.return_flag:
                    break
            return

        # NIL
        if tag == "NIL":
            return None

        # CATDECL: define cat with traits
        if tag == "CATDECL":
            _, id_node, traits_list = node
            _, name = id_node
            traits = {}

            for trait_node in traits_list[1]:
                # ('TRAIT', ('ID', tname), expr)
                _, (_, tname), expr = trait_node

                # prevent unquoted values
                if isinstance(expr, tuple) and expr[0] == "ID":
                    bad = expr[1]
                    raise ValueError(
                        f"Trait value '{bad}' must be quoted.\n"
                        f"Example: {tname} = \"{bad}\";"
                    )

                traits[tname] = self.visit(expr)

            cat_obj = {"type": "cat", "traits": traits}
            symtab.declare(name, cat_obj)
            return

        # CATDECL_SIMPLE
        if tag == "CATDECL_SIMPLE":
            _, id_node = node
            _, name = id_node
            symtab.declare(name, {"type": "cat", "traits": {}})
            return

        # DRAW
        if tag == "DRAW":
            _, id_node = node
            _, name = id_node
            cat = symtab.lookup(name)
            cat = self.apply_mood_override(cat)
            print(render_cat(cat))
            # Print the cat's ID as its name unless ID is "noname"
            if name.lower() != "noname":
                print(name)
            return

        # RANDOMCATDECL / ASSIGN_RANDOMCAT
        if tag in ("RANDOMCATDECL", "ASSIGN_RANDOMCAT"):
            _, id_node = node
            _, name = id_node
            declare = (tag == "RANDOMCATDECL")

            choose_mood_mode = random.choice([True, False])

            all_traits = {
                "ears": ["pointy", "droopy", "round", "long", "short"],
                "mouth": ["smile", "frown", "neutral", "open", "smirk"],
                "body": ["smooth", "fluffy", "normal", "chubby"],
                "tail": ["none", "fluffy", "straight", "curled"],
                "whiskers": ["long", "short", "curled"],
                "mood": ["happy", "sleepy", "excited", "loving", "curious", "angry"],
            }

            # Mode 1: No mood, all random traits
            if not choose_mood_mode:
                traits = {}
                for t, options in all_traits.items():
                    if t == "mood":
                        continue
                    traits[t] = random.choice(options)
                cat_obj = {"type": "cat", "traits": traits}

            # Mode 2: Random mood, override, then fill remaining traits
            else:
                mood = random.choice(all_traits["mood"])
                traits = {"mood": mood}
                cat_obj = {"type": "cat", "traits": traits}
                cat_obj = self.apply_mood_override(cat_obj)

                for t, options in all_traits.items():
                    if t not in traits:
                        traits[t] = random.choice(options)

            if declare:
                symtab.declare(name, cat_obj)
            else:
                symtab.update(name, cat_obj)
            return

        # TRAITASSIGN
        if tag == "TRAITASSIGN":
            _, id_node, trait_node, expr = node
            _, catname = id_node
            _, traitname = trait_node

            if isinstance(expr, tuple) and expr[0] == "ID":
                bad = expr[1]
                raise ValueError(
                    f"Trait value '{bad}' must be quoted.\n"
                    f"Example: {traitname} = \"{bad}\";"
                )

            value = self.visit(expr)
            cat = symtab.lookup(catname)
            cat["traits"][traitname] = value

            if traitname == "mood":
                self.apply_mood_override(cat)

            symtab.update(catname, cat)
            return

        # ASSIGN (non-cat variable assignment)
        if tag == "ASSIGN":
            _, id_node, expr = node
            _, name = id_node

            if isinstance(expr, tuple) and expr[0] == "ID":
                bad = expr[1]
                raise ValueError(
                    f"Value '{bad}' must be quoted.\n"
                    f"Example: {name} = \"{bad}\";"
                )

            value = self.visit(expr)
            symtab.update(name, value)
            return

        # RETURN
        if tag == "RETURN":
            _, expr = node
            self.return_value = None if expr[0] == "NIL" else self.visit(expr)
            self.return_flag = True
            return

        # WHILE
        if tag == "WHILE":
            _, expr, stmt = node
            while self.visit(expr):
                self.visit(stmt)
                if self.return_flag:
                    break
            return

        # IF
        if tag == "IF":
            _, expr, then_stmt, else_stmt = node
            if self.visit(expr):
                self.visit(then_stmt)
            elif isinstance(else_stmt, tuple) and else_stmt[0] != "NIL":
                self.visit(else_stmt)
            return

        # BLOCK
        if tag == "BLOCK":
            _, sl = node
            self.visit(sl)
            return

        # FUNDECL
        if tag == "FUNDECL":
            _, id_node, params_list, body = node
            _, name = id_node
            symtab.declare(name, node)
            return

        # CALLSTMT
        if tag == "CALLSTMT":
            _, id_node, args_list = node
            _, name = id_node
            _ = self._call_function_by_name(name, args_list)
            return

        # CALLEXP
        if tag == "CALLEXP":
            _, id_node, args_list = node
            _, name = id_node
            return self._call_function_by_name(name, args_list)

        # Literals & expressions
        if tag == "INTEGER":
            return node[1]

        if tag == "STRING":
            s = node[1]
            # Strip matching single or double quotes
            if (s.startswith('"') and s.endswith('"')) or (s.startswith("'") and s.endswith("'")):
                return s[1:-1]
            return s

        if tag == "ID":
            return symtab.lookup(node[1])

        if tag == "ATTR":
            _, id_node, trait_node = node
            _, catname = id_node
            _, traitname = trait_node
            return symtab.lookup(catname)["traits"][traitname]

        if tag == "NOT":
            _, expr = node
            return not self.visit(expr)

        if tag in ("EQ", "NOTEQ"):
            _, left, right = node
            lval = self.visit(left)
            rval = self.visit(right)
            return (lval == rval) if tag == "EQ" else (lval != rval)

        raise RuntimeError(f"Unhandled tuple node tag: {tag}")

    # Function Call Helper
    ####################################################################
    def _call_function_by_name(self, name, args_list):
        func = symtab.lookup(name)
        if not isinstance(func, tuple) or func[0] != "FUNDECL":
            raise RuntimeError(f"{name} is not a function")

        _, _, params_list, body = func

        if args_list[0] == "LIST":
            arg_values = [self.visit(a) for a in args_list[1]]
        else:
            arg_values = []

        param_names = [p[1] for p in params_list[1]]

        symtab.push_scope()

        for pname, value in zip(param_names, arg_values):
            symtab.declare(pname, value)

        self.return_flag = False
        self.return_value = None

        self.visit(body)

        result = self.return_value
        self.return_flag = False    # clear return state after the call
        self.return_value = None
        symtab.pop_scope()
        return result

    # Dispatcher
    ####################################################################
    def visit(self, node):
        if isinstance(node, tuple):
            return self.visitTuple(node)

        raise RuntimeError("Unknown node type passed to interpreter")
