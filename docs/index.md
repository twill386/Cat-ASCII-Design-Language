
CSC402 Programming Language Implementation Project  
**Author:** Thomas Williams

---

## Overview
CADL (Cat ASCII Description Language) is a domain-specific programming language
designed to describe cats using traits such as mood, ears, tail, and body type,
and render them as ASCII art.

This project demonstrates a full programming language pipeline:
- Lexer
- Parser
- Abstract Syntax Tree
- Interpreter
- ASCII Renderer

---

## Example CADL Program
```cadl
cat Miso {
    mood = sleepy;
    ears = pointy;
}
draw Miso;