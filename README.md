# sin-lang

The Simple INtepreted language.

## Language specification

```bnf
<block> := <expression> <expression>*
<expression> := <atom> [ ( <infix> | "=" | <py_code> ) <expression> ]
              | "if" <expression> "then" <block> [ "else" <block> ] "end"
<infix> := "`" <identifier> "`"
<atom> := <identifier> | <literal> | "(" <expression> ")" | <function_call>
<function_call> := <identifier> "(" <expression_list> ")"
<expression_list> := <expression> [ "," <expression_list> ]
```