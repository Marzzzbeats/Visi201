
from lexer import Token
from collections.abc import Generator
from ast_node import *


class TokenStream:
    def __init__(self, token_gen: Generator[Token, None, None]) -> None:
        self.buffer: list = []
        self.token_gen: Generator[Token, None, None] = token_gen

    def peek(self, k: int=0) -> Token:
        while len(self.buffer) <= k:
            self.buffer.append(next(self.token_gen))
        return self.buffer[k]

    def advance(self) -> Token:
        if len(self.buffer) == 0:
            self.peek()
        return self.buffer.pop(0)
    
    def match_token(self, type: str, value=None) -> bool:
        tok: Token = self.peek()
        if (tok.type == type) and (value == None or tok.value == value):
            self.advance()
            return True
        else:
            return False
        
    def expect(self, type: str, value=None) -> Token:
        tok: Token = self.peek()
        if (tok.type == type) and (value == None or tok.value == value):
            return self.advance()
        else:
            raise SyntaxError(f"expected {tok.type} got {tok.value!r} at line {tok.line} col {tok.col}")





class Parser:
    def __init__(self, token_gen):
        self.ts = TokenStream(token_gen)

    def parse(self):
        body = []
        self.skip_newlines()
        while self.ts.peek().type != "EOF":
            body.append(self.parse_statement())
            self.skip_newlines()
        self.ts.expect("EOF")
        return Module(body)
    
    def parse_statement(self):
        tok = self.ts.peek()
        if tok.type == "NAME":
            left = self.parse_expression()
            if self.ts.peek().type == "EQUAL":
                if not isinstance(left, (Name, Subscript)):
                    raise SyntaxError("Invalid assignment target")
                self.ts.expect("EQUAL")
                value = self.parse_expression()
                self.ts.expect("NEWLINE")
                return Assign(left, value)
            else:
                self.ts.expect("NEWLINE")
                return ExprStmt(left)
        elif tok.type == "IF":
            return self.parse_if()
        elif tok.type == "DEF":
            return self.parse_def()
        elif tok.type == "WHILE":
            return self.parse_while()
        elif tok.type == "RETURN":
            return self.parse_return()
        else:
            raise SyntaxError(f"Expected statment but got {tok.type}")
    
    def parse_expression(self):
        return self.parse_bool_or()
    
    def parse_bool_or(self):
        left = self.parse_bool_and()
        tok = self.ts.peek()
        if tok.type == "OR":
            op = self.ts.advance()
            right = self.parse_bool_or()
            return BoolOp(left, op.type, right)
        return left
    
    def parse_bool_and(self):
        left = self.parse_compare()
        tok = self.ts.peek()
        if tok.type == "AND":
            op = self.ts.advance()
            right = self.parse_bool_and()
            return BoolOp(left, op.type, right)
        return left
        
    def parse_compare(self):
        left = self.arith()
        tok = self.ts.peek()
        if tok.type in ["EQEQ", "NOTEQ", "LT", "LE", "GT", "GE"]:
            op = self.ts.advance()
            right = self.arith()
            return Compare(left, op.type, right)
        return left
    
    def arith(self):
        left = self.term()  
        tok = self.ts.peek()
        while tok.type in ["PLUS","MINUS"]:
            op = self.ts.advance()
            right = self.term()
            left = BinOp(left, op.type, right)
            tok = self.ts.peek()
        return left

    def term(self):
        left = self.postfix()
        tok = self.ts.peek()
        while tok.type in ["STAR","PERCENT", "SLASH"]:
            op = self.ts.advance()
            right = self.postfix()
            left = BinOp(left, op.type, right)
            tok = self.ts.peek()
        return left

    def postfix(self):
        expr = self.unaryop()
        tok = self.ts.peek()

        while True:
            tok = self.ts.peek()
            if tok.type == "LPAREN":
                args = self.parse_call_args()
                expr = Call(expr, args)
            elif tok.type == "LBRACKET":
                expr = self.parse_subscript(expr)
            else:
                break
        return expr
    
    def unaryop(self):
        tok = self.ts.peek()
        if tok.type in ["NOT", "MINUS"]:
            self.ts.advance()
            operand = self.unaryop()
            expr = UnaryOp(tok.type, operand)
        else:
            expr = self.primary()
        return expr

    def primary(self):
        tok = self.ts.peek()
        if tok.type == "NUMBER":
            self.ts.expect("NUMBER")
            expr = Number(int(tok.value))
        elif tok.type == "NAME":
            self.ts.expect("NAME")
            if tok.value == "True":
                expr  = Boolean(True)
            elif tok.value == "False":
                expr = Boolean(False)
            elif tok.value == "None":
                expr = NoneLiteral()
            else:
                expr = Name(tok.value)
        elif tok.type == "STRING":
            self.ts.expect("STRING")
            expr = String(tok.value)
        elif tok.type == "LPAREN":
            self.ts.expect("LPAREN")
            expr = self.parse_expression()
            self.ts.expect("RPAREN")
        elif tok.type == "LBRACKET":
            self.ts.expect("LBRACKET")
            expr = self.parse_list()
            self.ts.expect("RBRACKET")
        elif tok.type == "LBRACE":
            self.ts.expect("LBRACE")
            expr = self.parse_dict()
            self.ts.expect("RBRACE")
        else:
            raise SyntaxError
        return expr
    
    def parse_subscript(self, value):
        self.ts.expect("LBRACKET")
        index = self.parse_expression()
        self.ts.expect("RBRACKET")
        return Subscript(value, index)
    
    def parse_list(self):
        if self.ts.peek().type == "RBRACKET":
            return ListNode([])
        else:
            elms = [self.parse_expression()]
            while self.ts.peek().type == "COMMA":
                self.ts.expect("COMMA")
                if self.ts.peek().type == "RBRACKET":
                    break
                elms.append(self.parse_expression())
        return ListNode(elms)
    
    def parse_dict(self):
        if self.ts.peek().type == "RBRACE":
            return DictNode([],[])
        else:
            keys = [self.parse_expression()]
            self.ts.expect("COLON")
            values = [self.parse_expression()]
            while self.ts.peek().type == "COMMA":
                self.ts.expect("COMMA")
                if self.ts.peek().type == "RBRACE":
                    break
                keys.append(self.parse_expression())
                self.ts.expect("COLON")
                values.append(self.parse_expression())
        return DictNode(keys, values)

    def parse_assign(self):
        name = self.ts.expect("NAME").value
        self.ts.expect("EQUAL")
        expr = self.parse_expression()
        return Assign(target=Name(name), value=expr)

    def parse_block(self):
        body = []
        self.ts.expect("INDENT")
        self.skip_newlines()
        while self.ts.peek().type not in ["DEDENT", "EOF", "ELIF", "ELSE"]:
            body.append(self.parse_statement())
            self.skip_newlines()
        self.ts.expect("DEDENT")
        return body
    
    def parse_if(self):
        self.ts.expect("IF")
        test = self.parse_expression()
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body_if = self.parse_block()
        orelse = self.parse_elif()
        if len(orelse) == 0:
            orelse = self.parse_else()
        return If(test, body_if, orelse)

    def parse_elif(self):
        if self.ts.peek().type != "ELIF":
            return []
        else:
            self.ts.expect("ELIF")
            test = self.parse_expression()
            self.ts.expect("COLON")
            self.ts.expect("NEWLINE")
            body_elif = self.parse_block()
            other_elif = self.parse_elif()
            if len(other_elif) > 0:
                return [If(test, body_elif, other_elif)]
            else:
                return [If(test, body_elif, self.parse_else())]
    
    def parse_else(self):
        if self.ts.peek().type != "ELSE":
            return []
        else:
            self.ts.expect("ELSE")
            self.ts.expect("COLON")
            self.ts.expect("NEWLINE")
            body_else = self.parse_block()
            return body_else
        
    def parse_args(self):
        self.ts.expect("LPAREN")
        args = []
        while self.ts.peek().type != "RPAREN":
            arg = self.ts.expect("NAME").value
            args.append(arg)
            if self.ts.peek().type == "COMMA":
                self.ts.expect("COMMA")
            else:
                break
        self.ts.expect("RPAREN")
        return args
    
    def parse_call_args(self):
        self.ts.expect("LPAREN")
        args = []
        while self.ts.peek().type != "RPAREN":
            arg = self.parse_expression()
            args.append(arg)
            if self.ts.peek().type == "COMMA":
                self.ts.expect("COMMA")
            else:
                break
        self.ts.expect("RPAREN")
        return args
    

    def parse_def(self):
        self.ts.expect("DEF")
        name = self.ts.expect("NAME")
        args = self.parse_args()
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body = self.parse_block()
        return Def(name.value, args, body)
        
    
    def parse_while(self):
        self.ts.expect("WHILE")
        test = self.parse_expression()
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body = self.parse_block()
        return While(test, body)

    
    def parse_return(self):
        self.ts.expect("RETURN")
        after_return = self.ts.peek()
        if after_return.type == "NEWLINE":
            return_value = Return(None)
        else:
            expr = self.parse_expression()
            return_value = Return(expr)
        self.ts.expect("NEWLINE")
        return return_value
    
    def skip_newlines(self):
        while self.ts.match_token("NEWLINE"): 
            pass