"""
# sin.py

Interpreter for the **sin** (simple-interpreted) language.
"""
import re

class Enum(tuple): __getattr__ = tuple.index

Tokens = Enum("NUMBER IDENTIFIER LEFT_ROUND_PAREN RIGHT_ROUND_PAREN".split())

class Token(object):
    __slots__ = ["kind", "value", "pos"]
    def __init__(self, value, kind, pos=0):
        self.value, self.kind, self.pos = value, kind, pos
    def __repr__(self):
        return "(%s %r @ %s)" % (Tokens[self.kind], self.value, self.pos)

Token_Patterns = [
    (r'[ \n\t]+', None),
    (r'\(', Tokens.LEFT_ROUND_PAREN),
    (r'\)', Tokens.RIGHT_ROUND_PAREN),
    (r'[+-]?[0-9]+', Tokens.NUMBER),
    (r'[A-Za-z_][A-Za-z0-9_]*', Tokens.IDENTIFIER)
]

def tokenize(text):
    position = 0
    while position < len(text):
        match = None
        for token_pattern in Token_Patterns:
            pattern, kind = token_pattern
            regex = re.compile(pattern, re.I)
            match = regex.match(text, position)
            if match:
                matched_text = match.group(0)
                if kind is not None:
                    token = Token(matched_text, kind, position)
                    yield token
                break
        if match is None:
            raise SyntaxError("Illegal character %r @ %s" % (text[position], position))
        else:
            position = match.end(0)

