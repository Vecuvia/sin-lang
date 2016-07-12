# sin-lang

The Simple INtepreted language.

## Language specification

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
