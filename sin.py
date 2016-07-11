"""
# sin.py

Interpreter for the **sin** (simple-interpreted) language.
"""
import re

class Enum(tuple): __getattr__ = tuple.index

Tokens = Enum("NUMBER IDENTIFIER LEFT_ROUND_PAREN RIGHT_ROUND_PAREN ASSIGN PYTHON_CODE IF THEN ELSE END INFIX_CALL FUNCTION COMMA".split())

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
    (r'=', Tokens.ASSIGN),
    (r',', Tokens.COMMA),
    (r'[+-]?[0-9]+', Tokens.NUMBER),
    (r'if', Tokens.IF),
    (r'then', Tokens.THEN),
    (r'else', Tokens.ELSE),
    (r'end', Tokens.END),
    (r'fun', Tokens.FUNCTION),
    (r'`[A-Za-z_][A-Za-z0-9_]*`', Tokens.INFIX_CALL),
    (r'{[A-Za-z_][A-Za-z0-9_.]*}', Tokens.PYTHON_CODE),
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
    def execute(self, env=None):
        if env is None: env = {}
        return env.get(self.name, None)

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "(lit {0})".format(self.value)
    def execute(self, env=None):
        return eval(self.value)

class Call(ASTNode):
    def __init__(self, name, *params):
        self.name, self.params = name, params
    def __str__(self):
        return "({0} {1})".format(self.name, " ".join(map(str, self.params)))
    def execute(self, env=None):
        if env is None: env = {}
        params = [param.execute(env) for param in self.params]
        if self.name == "add":
            return sum(params)
        elif self.name in env:
            return env[self.name].call(env, params)

class PyCall(ASTNode):
    def __init__(self, function, *params):
        self.function, self.params = function, params
    def __str__(self):
        return "({0} {1})".format(self.function.__name__, " ".join(map(str, self.params)))
    def execute(self, env=None):
        if env is None: env = {}
        return self.function(*[param.execute(env) for param in self.params])

class Assign(ASTNode):
    def __init__(self, variable, expression):
        self.variable, self.expression = variable, expression
    def __str__(self):
        return "(! {0} {1})".format(self.variable, self.expression)
    def execute(self, env=None):
        if env is None: env = {}
        value = self.expression.execute(env)
        env[self.variable.name] = value
        return value

class Block(ASTNode):
    def __init__(self, expressions):
        self.expressions = expressions
    def __str__(self):
        return "(begin {0})".format("\n".join(map(str, self.expressions)))
    def execute(self, env=None):
        if env is None: env = {}
        result = None
        for expression in self.expressions:
            result = expression.execute(env)
        return result

class Condition(ASTNode):
    def __init__(self, condition, if_true, if_false=None):
        self.condition, self.if_true, self.if_false = condition, if_true, if_false
    def __str__(self):
        return "(cond {0} {1} {2})".format(self.condition, self.if_true, self.if_false)
    def execute(self, env=None):
        if env is None: env = {}
        #print(self.condition.execute(env))
        if self.condition.execute(env):
            return self.if_true.execute(env)
        elif self.if_false:
            return self.if_false.execute(env)

class Function(ASTNode):
    def __init__(self, params, code):
        self.params, self.code = params, code
    def __str__(self):
        return "(lambda ({0}) {1})".format(self.params, self.code)
    def execute(self, env=None):
        return self
    def call(self, env, params):
        local_env = {}
        local_env.update(env)
        #print("**", self.params, params)
        for name, param in zip(self.params, params):
            local_env[name] = param
        return self.code.execute(local_env)

class Interpreter(object):
    def parse(self, text):
        self.text = text
        self.tokens = tokenize(text)
        self.token, self.next_token = None, None
        self.advance()
        return self.block()
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
        if self.accept(Tokens.IDENTIFIER) or self.accept(Tokens.PYTHON_CODE):
            identifier = self.token
            if self.accept(Tokens.LEFT_ROUND_PAREN):
                params = [self.expression()]
                while self.accept(Tokens.COMMA):
                    params.append(self.expression())
                self.expect(Tokens.RIGHT_ROUND_PAREN)
                if identifier.kind == Tokens.IDENTIFIER:
                    return Call(identifier.value, *params)
                else:
                    return PyCall(eval(identifier.value[1:-1]), *params)
            return Variable(self.token.value)
        elif self.accept(Tokens.NUMBER):
            return Literal(self.token.value)
        elif self.accept(Tokens.LEFT_ROUND_PAREN):
            value = self.expression()
            self.expect(Tokens.RIGHT_ROUND_PAREN)
            return value
        elif self.accept(Tokens.IF):
            condition = self.expression()
            self.expect(Tokens.THEN)
            if_true = self.block()
            if_false = None
            if self.accept(Tokens.ELSE):
                if_false = self.block()
            self.expect(Tokens.END)
            return Condition(condition, if_true, if_false)
        elif self.accept(Tokens.FUNCTION):
            self.expect(Tokens.LEFT_ROUND_PAREN)
            self.advance()
            params = [self.token.value]
            while self.accept(Tokens.COMMA):
                self.advance()
                params.append(self.token.value)
            self.expect(Tokens.RIGHT_ROUND_PAREN)
            code = self.block()
            self.expect(Tokens.END)
            return Function(params, code)
    def expression(self):
        left = self.atom()
        if self.accept(Tokens.INFIX_CALL):
            operation = self.token.value[1:-1]
            right = self.expression()
            return Call(operation, left, right)
        elif self.accept(Tokens.PYTHON_CODE):
            operation = eval(self.token.value[1:-1])
            right = self.expression()
            return PyCall(operation, left, right)
        elif self.accept(Tokens.ASSIGN):
            right = self.expression()
            return Assign(left, right)
        return left
    def block(self):
        expressions = []
        expression = self.expression()
        while expression is not None:
            expressions.append(expression)
            expression = self.expression()
        return Block(expressions)

test = """
add = fun (a, b) 
  {int.__add__}(a, b)
end
sub = fun (a, b)
  {int.__sub__}(a, b)
end
print = fun (s)
  {print}(s)
end
a = 2 `add` 2 `sub` 3
b = if a then 
  8 
else 
  4 
end
print(add(2, 3) `add` 5)
print(b)
print(a)
"""

tree = Interpreter().parse(test)
#print(tree)
tree.execute()