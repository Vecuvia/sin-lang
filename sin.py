"""
# sin.py

Interpreter for the **sin** (simple-interpreted) language.
"""
import re

class Enum(tuple): __getattr__ = tuple.index

Tokens = Enum("NUMBER IDENTIFIER LEFT_ROUND_PAREN RIGHT_ROUND_PAREN ASSIGN PYTHON_CODE IF THEN ELSE END INFIX_CALL FUNCTION COMMA WHILE DO STRING INCLUDE".split())

class Token(object):
    __slots__ = ["kind", "value", "pos"]
    def __init__(self, value, kind, pos=0):
        self.value, self.kind, self.pos = value, kind, pos
    def __repr__(self):
        return "(%s %r @ %s)" % (Tokens[self.kind], self.value, self.pos)

Token_Patterns = [
    (r'[ \n\t]+', None),
    (r'#[^\n]*', None),
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
    (r'while', Tokens.WHILE),
    (r'do', Tokens.DO),
    (r'include', Tokens.INCLUDE),
    (r'"[^"\n]*"', Tokens.STRING),
    (r'`[A-Za-z_][A-Za-z0-9_]*`', Tokens.INFIX_CALL),
    (r'{[^\}]*}', Tokens.PYTHON_CODE),
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

class Environment(object):
    def __init__(self, parent):
        self.parent = parent
        self.data = {}
    def get(self, key, default):
        value = self[key]
        if value is None:
            return default
        return value
    def __getitem__(self, key):
        if key in self.data or self.parent is None:
            return self.data.get(key, None)
        elif self.parent:
            return self.parent[key]
    def __contains__(self, key):
        if key in self.data:
            return True
        return False
    def __setitem__(self, key, value):
        if self.parent and key in self.parent:
            self.parent[key] = value
        else:
            self.data[key] = value

class ASTNode(object): pass

class Variable(ASTNode):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return "(var {0})".format(self.name)
    def execute(self, env):
        return env.get(self.name, None)

class Literal(ASTNode):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "(lit {0})".format(self.value)
    def execute(self, env):
        return eval(self.value)

class PyLiteral(ASTNode):
    def __init__(self, value):
        self.value = value
    def __str__(self):
        return "(py {0})".format(self.value)
    def execute(self, env):
        return eval(self.value)

class Call(ASTNode):
    def __init__(self, name, *params):
        self.name, self.params = name, params
    def __str__(self):
        return "(call {0} {1})".format(self.name, " ".join(map(str, self.params)))
    def execute(self, env):
        env = Environment(parent=env)
        function = self.name.execute(env)
        params = [param.execute(env) for param in self.params]
        try:
            return function.call(env, params)
        except AttributeError:
            raise RuntimeError("{0} is not a function".format(self.name))

class PyCall(ASTNode):
    def __init__(self, function, *params):
        self.function, self.params = function, params
    def __str__(self):
        return "({0} {1})".format(self.function.__name__, " ".join(map(str, self.params)))
    def execute(self, env):
        env = Environment(parent=env)
        return self.function(*[param.execute(env) for param in self.params])

class Assign(ASTNode):
    def __init__(self, variable, expression):
        self.variable, self.expression = variable, expression
    def __str__(self):
        return "(! {0} {1})".format(self.variable, self.expression)
    def execute(self, env):
        value = self.expression.execute(env)
        #print("*ASSIGN", self.variable, value)
        env[self.variable.name] = value
        return value

class Block(ASTNode):
    def __init__(self, expressions):
        self.expressions = expressions
    def __str__(self):
        return "(begin {0})".format("\n".join(map(str, self.expressions)))
    def execute(self, env):
        #env = Environment(parent=env)
        result = None
        for expression in self.expressions:
            result = expression.execute(env)
        return result

class Condition(ASTNode):
    def __init__(self, condition, if_true, if_false=None):
        self.condition, self.if_true, self.if_false = condition, if_true, if_false
    def __str__(self):
        return "(cond {0} {1} {2})".format(self.condition, self.if_true, self.if_false)
    def execute(self, env):
        env = Environment(parent=env)
        if self.condition.execute(env):
            return self.if_true.execute(env)
        elif self.if_false:
            return self.if_false.execute(env)

class Loop(ASTNode):
    def __init__(self, condition, block):
        self.condition, self.block = condition, block
    def __str__(self):
        return "(loop {0} {1})".format(self.condition, self.block)
    def execute(self, env):
        env = Environment(parent=env)
        result = None
        while self.condition.execute(env):
            result = self.block.execute(env)
        result = None

class Function(ASTNode):
    def __init__(self, params, code):
        self.params, self.code = params, code
    def __str__(self):
        return "(lambda ({0}) {1})".format(self.params, self.code)
    def execute(self, env=None):
        return self
    def call(self, env, params):
        #print("**", self)
        env = Environment(parent=env)
        for name, param in zip(self.params, params):
            #print(name, param)
            env.data[name] = param
        return self.code.execute(env)

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
        if self.accept(Tokens.INCLUDE):
            self.expect(Tokens.STRING)
            filename = self.token.value[1:-1]
            with open(filename, "r") as included_file:
                source = included_file.read()
            tree = Interpreter().parse(source)
            return tree
        elif self.accept(Tokens.IDENTIFIER):
            identifier = self.token
            return Variable(self.token.value)
        elif self.accept(Tokens.PYTHON_CODE):
            return PyLiteral(self.token.value[1:-1])
        elif self.accept(Tokens.NUMBER) or self.accept(Tokens.STRING):
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
        elif self.accept(Tokens.WHILE):
            condition = self.expression()
            self.expect(Tokens.DO)
            block = self.block()
            self.expect(Tokens.END)
            return Loop(condition, block)
        elif self.accept(Tokens.FUNCTION):
            self.expect(Tokens.LEFT_ROUND_PAREN)
            #self.advance()
            params = []
            while self.accept(Tokens.IDENTIFIER):
                params.append(self.token.value)
                if not self.accept(Tokens.COMMA):
                    break
            self.expect(Tokens.RIGHT_ROUND_PAREN)
            code = self.block()
            self.expect(Tokens.END)
            return Function(params, code)
    def primary(self):
        left = self.atom()
        if self.accept(Tokens.LEFT_ROUND_PAREN):
            params = []
            param = self.expression()
            while param is not None:
                params.append(param)
                self.accept(Tokens.COMMA)
                param = self.expression()
            self.expect(Tokens.RIGHT_ROUND_PAREN)
            if type(left) in (Variable, Function, Condition):
                return Call(left, *params)
            elif type(left) is PyLiteral:
                return PyCall(eval(left.value), *params)
        return left
    def expression(self):
        left = self.primary()
        if self.accept(Tokens.INFIX_CALL):
            operation = self.token.value[1:-1]
            right = self.expression()
            return Call(Variable(operation), left, right)
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


test_1 = """
include "prelude.sin"

gt = fun (a, b)
  {int.__gt__}(a, b)
end

assert(3 `gt` 5, 1)
print(3 `gt` 5)
print(5 `gt` 3)

factorial = fun (n)
  if n `gt` 1 then
    n `mul` factorial(n `sub` 1)
  else
    1
  end
end

is_odd = fun (n)
  eq = fun (a, b) {int.__eq__}(a, b) end
  mod = fun (a, b) {int.__mod__}(a, b) end
  if (n `mod` 2) `eq` 0 then
    0
  else
    1
  end
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
print(factorial(10))

i = 10
while 
  if is_odd(i) then 
    i = i `sub` 1 
  else 
    i = i `sub` 3 
  end `gt` 0 do
  print(i)
end

print((fun (a) a `mul` 2 end)(8))
"""

test_2 = """
include "prelude.sin"

a = input()
print(assert(mul(2, 12), 23))
print((if a then mul else add end)(2, 12))

eq = fun (a, b) {int.__eq__}(a, b) end

fibonacci = fun (n)
  if n `eq` 0 then
    1
  else
    if n `eq` 1 then
      1
    else
      fibonacci(n `sub` 1) `add` fibonacci(n `sub` 2)
    end
  end
end

i = 10
while i = i `sub` 1 do
  print(fibonacci(i))
end
print("i " `concat` i)

test = fun ()
  c = 33
  print("within 'test', c is " `concat` c)
end

test()

print("c is " `concat` c)

c = 0
if a then 
  c = 33 
  print(c)
end

print(c)
"""

test_3 =  "include \"prelude.sin\" print(assert(mul(2, 12), 23))"

tree = Interpreter().parse(test_2)
#print(tree)
tree.execute(Environment(None))
