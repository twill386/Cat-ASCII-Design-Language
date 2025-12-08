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
        Only uses traits that exist in CADLTraits.txt
        and are supported by the ASCII renderer.
        """
        traits = cat["traits"]
        mood = traits.get("mood")

        if mood is None:
            return cat  # no mood, no override

        mood = mood.lower()

        if mood == "sleepy":
            traits["ears"] = "droopy"
            traits["mouth"] = "neutral"
            traits["whiskers"] = "short"
        elif mood == "happy":
            traits["mouth"] = "smile"
            traits["ears"] = "pointy"
            traits["whiskers"] = "long"
        elif mood == "angry":
            traits["mouth"] = "frown"
            traits["ears"] = "short"   
            traits["whiskers"] = "curled"
        elif mood == "loving":
            traits["mouth"] = "smile"
            traits["ears"] = "round"
            traits["whiskers"] = "long"
        elif mood == "curious":
            traits["ears"] = "pointy"
            traits["mouth"] = "neutral"
            traits["whiskers"] = "long"
        elif mood == "excited":
            traits["mouth"] = "open"
            traits["ears"] = "long"
            traits["whiskers"] = "long"

        return cat
    
    # Program & Statement List
    ####################################################################
    def visitProgram(self, node):
        return self.visit(node.stmt_list)

    def visitStmtList(self, node):
        for stmt in node.stmts:
            self.visit(stmt)
            if self.return_flag:
                break
    
    # Cat Declarations
    ####################################################################
    def visitCatDecl(self, node):
        """
        cat Miso { ears = pointy; mood = sleepy; }
        """
        traits = {}

        for trait in node.traits:
            name = trait.name
            value = self.visit(trait.expr)
            traits[name] = value

        cat_obj = {
            "type": "cat",
            "traits": traits
        }

        symtab.declare(node.id, cat_obj)
    
    # Draw
    ####################################################################
    def visitDraw(self, node):
        """
        draw Miso;
        """
        cat = symtab.lookup(node.id)
        cat = self.apply_mood_override(cat)

        art = render_cat(cat)     # generate ASCII
        print(art)                # output ASCII

    # RANDOMCAT
    ####################################################################
    def visitRandomCat(self, node):
        """
        ID = randomcat;
        Randomly chooses between:
        - random traits
        - random mood
        """

        # Randomly choose between the 2 options
        choose_mood_mode = random.choice([True, False])

        # CADL trait options (CADLTraits.txt)
        all_traits = {
            "ears": ["pointy", "droopy", "round", "long", "short"],
            "mouth": ["smile", "frown", "neutral", "open", "smirk"],
            "body": ["smooth", "fluffy", "normal", "chubby"],
            "tail": ["none", "fluffy", "straight", "curled"],  
            "whiskers": ["long", "short", "curled"],
            "mood": ["happy", "sleepy", "excited", "loving", "curious", "angry"]
        }

        # Random traits
        if not choose_mood_mode:

            traits = {}
            for t, options in all_traits.items():
                if t == "mood":  
                    continue  # ignore mood for this mode
                traits[t] = random.choice(options)

            cat_obj = {
                "type": "cat",
                "traits": traits
            }

            symtab.update(node.id, cat_obj)
            return

        # Random mood
        mood = random.choice(all_traits["mood"])

        # start with only mood
        traits = {"mood": mood}

        # cat object
        cat_obj = {"type": "cat", "traits": traits}

        # override for mood-controlled traits
        cat_obj = self.apply_mood_override(cat_obj)

        # fill in unaffected traits randomly
        for t, options in all_traits.items():
            if t not in cat_obj["traits"]:
                cat_obj["traits"][t] = random.choice(options)

        symtab.update(node.id, cat_obj)

    # Trait Assignment (ID.trait = expr)
    ####################################################################
    def visitTraitAssign(self, node):
        """
        Miso.ears = pointy;
        """
        cat = symtab.lookup(node.id)
        value = self.visit(node.expr)

        cat["traits"][node.trait] = value

        # If mood changed, apply override
        if node.trait == "mood":
            self.apply_mood_override(cat)

        symtab.update(node.id, cat)

    # Simple Assignment (ID = expr)
    ####################################################################
    def visitAssign(self, node):
        value = self.visit(node.expr)
        symtab.update(node.id, value)

    # Function Declaration
    ####################################################################
    def visitFuncDecl(self, node):
        symtab.declare(node.id, node)

    # Function Call
    ####################################################################
    def visitFuncCall(self, node):
        func = symtab.lookup(node.id)

        # Push new scope
        symtab.push_scope()

        # Bind parameters
        for param, arg in zip(func.params, node.args):
            symtab.declare(param, self.visit(arg))

        # Execute function
        self.return_flag = False
        self.visit(func.stmts)

        retval = self.return_value

        # Pop scope
        symtab.pop_scope()

        return retval

    # Return
    ####################################################################
    def visitReturn(self, node):
        self.return_flag = True
        self.return_value = self.visit(node.expr)

    # If and While
    ####################################################################
    def visitIf(self, node):
        cond = self.visit(node.expr)
        if cond:
            self.visit(node.then_stmt)
        elif node.else_stmt:
            self.visit(node.else_stmt)

    def visitWhile(self, node):
        while self.visit(node.expr):
            self.visit(node.stmt)

    # Expressions
    ####################################################################
    def visitBinaryOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        op = node.op

        if op == "==":
            return left == right
        elif op == "!=":
            return left != right

        raise RuntimeError("Unknown binary operator: " + op)

    # Primary (ID, NUMBER, STRING, (expr), !expr)
    ####################################################################
    def visitIdentifier(self, node):
        """
        Handles ID or ID.trait access.
        """
        val = symtab.lookup(node.id)

        # Dot-access case: Miso.ears
        if hasattr(node, "trait") and node.trait is not None:
            return val["traits"][node.trait]

        return val

    def visitNumber(self, node):
        return node.value

    def visitString(self, node):
        return node.value

    def visitNot(self, node):
        return not self.visit(node.expr)

    # Visit
    ####################################################################
    def visit(self, node):
        method_name = "visit" + node.__class__.__name__
        method = getattr(self, method_name)
        return method(node)