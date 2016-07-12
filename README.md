# sin-lang

The Simple INtepreted language.

Madames and monsieurs, lacking in operators and precedence levels, with a standard library consisting of arithmetic operations and with hacked-together scoping rules, I present to you THE SIN LANGUAGE!

So named because I'm bad at names *and* because I probably deserve to burn in hell for all eternity for writing it.

## What can I do with it?

Probably everything - lemme first write a Brainfuck interpreter in it and I'll come back to you on this. But see in the folder `examples`.

## Yes, but what is its syntax?

The base syntax is, per the language specification, extremely simple.

### Infix calls

Equivalent to `function(a, b)`.

```sin
a `<function>` b
```

### Python code

`<code>` is `eval`-ed and can then be called with `<params>`.

```sin
{<code>}
{<code>}(<params>)
```

### If blocks

They return the value of the last expression in the executed code block.

```sin
if <expression> then
  <block>
else
  <block>
end
```

### While blocks

They return the value of the last expression at the last iteration.

```sin
while <expression> do
  <block>
end
```

### Functions

They return the value of the last expression in the code block. They are anonymous, but can be assigned to a variable.

```sin
<name> = fun (<params>)
  <block>
end
```

## Language specification

**Warning:** might not be up to date - the language was more grown than built

```bnf
<block> := <expression> <expression>*
<expression> := <primary> [ ( <infix> | "=" ) <expression> ]
<primary> := <atom> [ "(" <expression_list ")" ]
<atom> := <identifier> 
        | "[" <expression_list> "]"
        | <literal> 
        | <python_code>
        | "(" <expression> ")"
        | "if" <expression> "then" <block> [ "else" <block> ] "end"
        | "while" <expression> "do" <block> "end"
        | "fun" "(" <identifier_list> ")" <block> "end"
<python_code> := "{" <code> "}"
<infix> := "`" <identifier> "`"
<expression_list> := <expression> [ "," <expression_list> ]
<identifier_list> := <identifier> [ "," <identifier_list> ]
```
