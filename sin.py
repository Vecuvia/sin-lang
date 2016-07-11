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

class ASTNode(object): pass

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "(var {0})".format(self.name)

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "(lit {0})".format(self.value)

class Call(ASTNode):
    def __init__(self, name, *params):
        self.name, self.params = name, params
    def __str__(self):
        return "({0} {1})".format(self.name, " ".join(map(str, self.params)))

class Interpreter(object):
    def parse(self, text):
        self.text = text
        self.tokens = tokenize(text)
        self.token, self.next_token = None, None
        self.advance()
        return self.expression()
    def advance(self):
        self.token, self.next_token = self.next_token, next(self.tokens, None)
    def accept(self, kind):
        if self.next_token is not None and self.next_token.kind == kind:
            self.advance()
            return True
        return False
    def expect(self, kind):
        if not self.accept(kind):
            raise SyntaxError("{0}: expected {1}".format(self.token, Tokens[kind]))
    def atom(self):
        if self.accept(Tokens.IDENTIFIER):
            return Variable(self.token.value)
        elif self.accept(Tokens.NUMBER):
            return Literal(self.token.value)
        elif self.accept(Tokens.LEFT_ROUND_PAREN):
            value = self.expression()
            self.expect(Tokens.RIGHT_ROUND_PAREN)
            return value
    def expression(self):
        left = self.atom()
        if self.accept(Tokens.IDENTIFIER):
            operation = self.token.value
            right = self.expression()
            return Call(operation, left, right)
        return left

print(Interpreter().parse("(a add 2) add 3"))