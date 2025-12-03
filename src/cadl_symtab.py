"""
Symbol table for CADL

Very similar to Cuppa3 scoped symbol table system.
CADL uses it without structural modification as cat objects are
simply stored as dictionaries:

  symtab.declare("Miso", {
      "type": "cat",
      "traits": { "ears": "pointy", "mood": "sleepy" }
  })
Things like trait access and mutation are handled by the 
interpreter.
"""

CURR_SCOPE = 0

class SymTab:

    def __init__(self):
        self.initialize()

    def initialize(self):
        # global scope dictionary must always be present
        self.scoped_symtab = [{}]

    def push_scope(self):
        # increment current scope and push new symbol table
        global CURR_SCOPE
        CURR_SCOPE += 1
        self.scoped_symtab = [{}] + self.scoped_symtab

    def pop_scope(self):
        # pop current scope and decrement scope pointer
        global CURR_SCOPE
        CURR_SCOPE -= 1
        self.scoped_symtab = self.scoped_symtab[1:]

    # CADL addition: check if a symbol exists in any scope
    def exists(self, sym):
        return any(sym in scope for scope in self.scoped_symtab)

    # Return True if current scope has an entry for sym
    def is_local(self, sym):
        return sym in self.scoped_symtab[0]


    # Retrieve the value associated with the symbol sym
    def lookup(self, sym):

        # look for symbol starting from the innermost scope
        for scope in self.scoped_symtab:
            if sym in scope:
                val = scope[sym]
                return val

        # not found
        raise ValueError("{} was not declared".format(sym))

    # Declare sym in current scope and give it value val
    def declare(self, sym, val):

        # only declare new symbol if not already in this scope
        if sym in self.scoped_symtab[0]:
            raise ValueError("{} already declared".format(sym))

        self.scoped_symtab[0][sym] = val

    # Update the value associated with sym somewhere in the stack
    def update(self, sym, val):

        # find first occurrence of sym and update its value
        for scope in self.scoped_symtab:
            if sym in scope:
                scope[sym] = val
                return

        # not found
        raise ValueError("{} was not declared".format(sym))

# global symbol table instance
symtab = SymTab()