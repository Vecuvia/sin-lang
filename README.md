# sin-lang

The Simple INtepreted language.

## Language specification

```bnf
<atom> := <identifier> | <literal> | "(" <expression> ")"
<expression> := <atom> [ ( <identifier> | "=" | <py_code> ) <expression> ]
<block> := <expression> <expression>*
```