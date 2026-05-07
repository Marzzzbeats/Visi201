
####################################
##             AST                ##
####################################

## Ce fichier permet de transformer notre suite de TOKENS
## en un AST (abstract syntax tree)



from lexer import Token
from collections.abc import Generator
from cpython.ast_node import *


class TokenStream:
    """
    Flux de tokens avec mise en tampon pour faciliter le parsing.

    Permet de consommer un générateur de tokens tout en offrant des
    opérations de lecture anticipée (peek), consommation (advance)
    et validation (match / expect).

    Attributes:
        buffer (list[Token]): Tampon de tokens déjà lus.
        token_gen (Generator[Token, None, None]): Générateur de tokens source.
    """
    def __init__(self, token_gen: Generator[Token, None, None]) -> None:
        self.buffer: list = []
        self.token_gen: Generator[Token, None, None] = token_gen

    def peek(self, k: int=0) -> Token:
        """
        Retourne le k-ième token sans le consommer.
        Remplit le buffer si nécessaire en avançant dans le générateur.

        Args:
            k (int): Position relative du token à lire (0 = courant).

        Returns:
            Token: Token à la position demandée.
        """
        while len(self.buffer) <= k:
            self.buffer.append(next(self.token_gen))
        return self.buffer[k]

    def advance(self) -> Token:
        """
        Consomme et retourne le prochain token.
        Si le buffer est vide, récupère d'abord un token depuis le générateur.

        Returns:
            Token: Prochain token consommé.
        """
        if len(self.buffer) == 0:
            self.peek()
        return self.buffer.pop(0)
    
    def match_token(self, type: str, value=None) -> bool:
        """
        Vérifie si le prochain token correspond au type (et éventuellement à la valeur),
        et le consomme si c'est le cas.

        Args:
            type (str): Type attendu.
            value (Any, optional): Valeur attendue.

        Returns:
            bool: True si le token correspond et a été consommé, sinon False.
        """
        tok: Token = self.peek()
        if (tok.type == type) and (value == None or tok.value == value):
            self.advance()
            return True
        else:
            return False
        
    def expect(self, type: str, value=None) -> Token:
        """
        Consomme le prochain token s'il correspond au type (et éventuellement à la valeur),
        sinon lève une erreur.

        Args:
            type (str): Type attendu.
            value (Any, optional): Valeur attendue.

        Returns:
            Token: Token consommé.

        Raises:
            SyntaxError: Si le token ne correspond pas.
        """
        tok: Token = self.peek()
        if (tok.type == type) and (value == None or tok.value == value):
            return self.advance()
        else:
            raise SyntaxError(f"expected {type} got {tok.type} ({tok.value!r}) at line {tok.line} col {tok.col}")





class Parser:
    """
    Analyseur syntaxique (parser) construisant un AST à partir d'un flux de tokens.

    Utilise une descente récursive pour analyser les expressions et instructions
    du langage et produire les nœuds correspondants.

    Attributes:
        ts (TokenStream): Flux de tokens utilisé pour le parsing.
    """
    def __init__(self, token_gen: Generator[Token, None, None]) -> None:
        self.ts: TokenStream = TokenStream(token_gen)

    def parse(self) -> Module:
        """
        Parse le programme complet.

        Consomme les tokens jusqu'à EOF et construit un Module contenant
        toutes les instructions.

        Returns:
            Module: Racine de l'AST.
        """
        body: list = []
        self.skip_newlines()
        while self.ts.peek().type != "EOF":
            body.append(self.parse_statement())
            self.skip_newlines()
        self.ts.expect("EOF")
        return Module(body)
    
    def parse_statement(self) -> Stmt:
        """
        Parse une instruction.

        Détermine le type d'instruction à partir du token courant
        (assignation, if, boucle, fonction, etc.).

        Returns:
            Stmt: Nœud correspondant à l'instruction.
        """
        tok: Token = self.ts.peek()
        if tok.type == "NAME":
            left: Expr = self.parse_expression()
            if self.ts.peek().type == "EQUAL":
                if not isinstance(left, (Name, Subscript)):
                    raise SyntaxError("Invalid assignment target")
                self.ts.expect("EQUAL")
                value: Expr = self.parse_expression()
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
        elif tok.type == "CLASS":
            return self.parse_class()
        elif tok.type == "PASS":
            self.ts.expect("PASS")
            return PassNode()
        elif tok.type == "TRY":
            return self.parse_try()
        else:
            raise SyntaxError(f"Expected statment but got {tok.type}")
    
    def parse_expression(self):
        """
        Parse une expression.
        """
        return self.parse_bool_or()
    
    def parse_bool_or(self):
        """
        Parse les opérations logiques OR.
        """
        left = self.parse_bool_and()
        tok = self.ts.peek()
        if tok.type == "OR":
            op = self.ts.advance()
            right = self.parse_bool_or()
            return BoolOp(left, op.type, right)
        return left
    
    def parse_bool_and(self):
        """
        Parse les opérations logiques AND.
        """
        left = self.parse_compare()
        tok = self.ts.peek()
        if tok.type == "AND":
            op = self.ts.advance()
            right = self.parse_bool_and()
            return BoolOp(left, op.type, right)
        return left
        
    def parse_compare(self):
        """
        Parse les comparaisons.
        Gère les opérateurs de comparaison (==, !=, <, <=, >, >=).
        """
        left = self.arith()
        tok = self.ts.peek()
        if tok.type in ["EQEQ", "NOTEQ", "LT", "LE", "GT", "GE"]:
            op = self.ts.advance()
            right = self.arith()
            return Compare(left, op.type, right)
        return left
    
    def arith(self):
        """
        Parse les opérations arithmétiques de niveau bas (+, -).
        Applique une évaluation gauche à droite.
        """
        left = self.term()  
        tok = self.ts.peek()
        while tok.type in ["PLUS","MINUS"]:
            op = self.ts.advance()
            right = self.term()
            left = BinOp(left, op.type, right)
            tok = self.ts.peek()
        return left

    def term(self):
        """
        Parse les opérations multiplicatives (*, /, %).
        Applique une évaluation gauche à droite.
        """
        left = self.postfix()
        tok = self.ts.peek()
        while tok.type in ["STAR","PERCENT", "SLASH"]:
            op = self.ts.advance()
            right = self.postfix()
            left = BinOp(left, op.type, right)
            tok = self.ts.peek()
        return left

    def postfix(self):
        """
        Parse les opérations postfixées.
        Gère les appels de fonction, accès indexé et attributs.
        """
        expr = self.unaryop()
        tok = self.ts.peek()

        while True:
            tok = self.ts.peek()
            if tok.type == "LPAREN":
                args = self.parse_call_args()
                expr = Call(expr, args)
            elif tok.type == "LBRACKET":
                expr = self.parse_subscript(expr)
            elif tok.type == "POINT":
                expr = self.parse_attribute(expr)
            else:
                break
        return expr
    
    def unaryop(self):
        """
        Parse les opérations unaires.
        Gère les opérateurs comme NOT et le signe negatif.
        """
        tok = self.ts.peek()
        if tok.type in ["NOT", "MINUS"]:
            self.ts.advance()
            operand = self.unaryop()
            expr = UnaryOp(tok.type, operand)
        else:
            expr = self.primary()
        return expr

    def primary(self):
        """
        Gère juste les Stmt de base
        """
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
        """
        Parse un accès indexé (subscript).

        e.g.:
            a[0]
        """
        self.ts.expect("LBRACKET")
        index = self.parse_expression()
        self.ts.expect("RBRACKET")
        return Subscript(value, index)
    
    def parse_attribute(self, inst):
        """
        Parse un accès à un attribut.

        e.g.:
            obj.attr
        """
        self.ts.expect("POINT")
        name = self.ts.expect("NAME")
        return Attribute(inst, name.value)
    
    def parse_list(self):
        """
        Parse une liste.
        Gère les listes vides et les éléments séparés par des virgules.
        """
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
        """
        Parse un dictionnaire.
        Gère les paires clé:valeur séparées par des virgules.
        """
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
        """
        Parse un block indenté peut importe l'indentation actuel
        """
        body = []
        self.ts.expect("INDENT")
        self.skip_newlines()
        while self.ts.peek().type not in ["DEDENT", "EOF", "ELIF", "ELSE"]:
            body.append(self.parse_statement())
            self.skip_newlines()
        self.ts.expect("DEDENT")
        return body
    
    def parse_if(self):
        """
        Parse une structure conditionnelle if/elif/else.
        """
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
        """
        Parse les clauses elif.
        Construit récursivement une chaîne de conditions.
        """
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
        """
        Parse une clause else.
        """
        if self.ts.peek().type != "ELSE":
            return []
        else:
            self.ts.expect("ELSE")
            self.ts.expect("COLON")
            self.ts.expect("NEWLINE")
            body_else = self.parse_block()
            return body_else
        
    def parse_args(self):
        """
        Parse les arguments d'une fonction.
        Retourne les noms des paramètres.
        """
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
        """
        Parse les arguments d'un appel de fonction.
        Retourne les expressions passées en argument.
        """
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
        """
        Parse une définition de fonction.
        """
        self.ts.expect("DEF")
        name = self.ts.expect("NAME")
        args = self.parse_args()
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body = self.parse_block()
        return Def(name.value, args, body)
        
    
    def parse_while(self):
        """
        Parse une boucle while.
        """
        self.ts.expect("WHILE")
        test = self.parse_expression()
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body = self.parse_block()
        return While(test, body)

    
    def parse_return(self):
        """
        Parse une instruction return.
        """
        self.ts.expect("RETURN")
        after_return = self.ts.peek()
        if after_return.type == "NEWLINE":
            return_value = Return(None)
        else:
            expr = self.parse_expression()
            return_value = Return(expr)
        self.ts.expect("NEWLINE")
        return return_value
    
    def parse_class(self):
        """
        Parse une définition de classe.
        """
        self.ts.expect("CLASS")
        name = self.ts.expect("NAME").value
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body = self.parse_block()
        return ClassDef(name, body)
    
    def parse_try(self):
        """
        Parse un bloc try/except.
        Lève une erreur si aucun handler n'est présent.
        """
        self.ts.expect("TRY")
        self.ts.expect("COLON")
        self.ts.expect("NEWLINE")
        body = self.parse_block()
        handlers = []
        while self.ts.peek().type == "EXCEPT":
            self.ts.expect("EXCEPT")
            if self.ts.peek().type != "COLON":
                exc_type = self.parse_expression()
            else:
                exc_type = None
            self.ts.expect("COLON")
            self.ts.expect("NEWLINE")
            handler_body = self.parse_block()
            handlers.append(ExceptHandler(type=exc_type, name=None, body=handler_body))

        if len(handlers) == 0:
            raise SyntaxError("try without except")
        return Try(body=body, handlers=handlers)

    
    def skip_newlines(self):
        while self.ts.match_token("NEWLINE"): 
            pass