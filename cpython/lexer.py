
####################################
##             LEXER              ##
####################################

## Ce fichier permet de transformer notre fichier .py
## en une suite lineaire de TOKEN



import re
from collections.abc import Iterator, Generator



# Definition des exrpressions regex pour detecter les different 
# keywords python et de les assosié a un nom
TOKEN_SPEC = [
    ("NUMBER",      r"\d+"),
    ("STRING",      r"'[^']*'|\"[^\"]*\""),
    ("NAME",        r"[a-zA-Z_]\w*"),
    ("PLUS",        r"\+"),
    ("MINUS",       r"-"),
    ("STAR",        r"\*"),
    ("SLASH",       r"/"),
    ("PERCENT",     r"%"),
    ("EQEQ",        r"=="),
    ("NOTEQ",       r"!="),
    ("LE",          r"<="),
    ("GE",          r">="),
    ("LT",          r"<"),
    ("GT",          r">"),
    ("EQUAL",       r"="),
    ("LPAREN",      r"\("),
    ("RPAREN",      r"\)"),
    ("LBRACKET",      r"\["),
    ("RBRACKET",      r"\]"),
    ("LBRACE",      r"\{"),
    ("RBRACE",      r"\}"),
    ("COLON",       r":"),
    ("COMMA",       r","),
    ("POINT",       r"\."),
    ("COMMENT",     r"#.*"),
    ("SKIP",        r"[ \t]+"),
]


# Une pile qui permet de gérer les indentation
class IndentStack:
    """
    Gère les niveaux d'indentation pour un lexer Python.

    Cette structure permet de suivre les niveaux d'indentation et de
    générer les DEDENT nécessaires lors de la diminution d'indentation.

    Attributes:
        stack (list[int]): Pile des niveaux d'indentation.
    """
    
    def __init__(self) -> None:
        """
        Initialise la pile avec une indentation de base à 0.
        """
        self.stack: list[int] = [0]


    def current(self) -> int:
        """
        Retourne le niveau d'indentation actuel.

        Returns:
            int: Valeur au sommet de la pile.
        """
        return self.stack[-1]
    

    def push(self, indent: int) -> None:
        """
        Ajoute un nouveau niveau d'indentation.

        Args:
            indent (int): Nouveau niveau d'indentation.
        """
        self.stack.append(indent)


    def dedent_to(self, indent: int) -> int:
        """
        Réduit l'indentation jusqu'au niveau donné.

        Supprime les niveaux supérieurs à `indent` et retourne
        le nombre de DEDENT effectués.

        Args:
            indent (int): Niveau d'indentation cible.

        Returns:
            int: Nombre de niveaux supprimés.

        Raises:
            IndentationError: Si le niveau cible est invalide.
        """
        count = 0
        while indent < self.current():
            self.stack.pop()
            count += 1
        if indent != self.current():
            raise IndentationError
        return count



class Token:
    """
    Représente un token issu du lexer.

    Attributes:
        type (str): Type du token (IDENTIFIER, NUMBER, INDENT, etc.)
        value (str): Valeur associée au token.
        line (int): Numéro de ligne.
        col (int): Position dans la ligne.
    """

    def __init__(self, type: str, value: str, line: int, col: int):
        self.type: str = type
        self.value: str = value
        self.line: int = line
        self.col: int = col


    def __repr__(self):
        return f"{self.type} : {self.value!r}"
    


def name_mapping(name: str, value: str, line: int, col: int) -> Token:
    """
    Transforme les TOKEN name en leur propre TOKEN
    Permet aussi de fix les chaines de characteres

    Args:
        name (str): Nom du token
        value (str): Valeur du token
        line (int): Numéro de ligne.
        col (int): Position dans la ligne.

    Returns:
        TOKEN : renvoie la value comme son propre TOKEN ==> e.g. ("DEF", "def", y, x) 
    """
    if name == "NAME" and value in {"def", "return", "if", "elif", "else", "while", "and", "or", "not", "pass", "class", "try", "except", "as"}:
        return Token(value.upper(), value, line, col)
    elif name == "STRING":
        return Token(name, value.strip('"'), line, col)  # On considere les strings sans les "" pour ne pas causer de bugs plus tard
    else:
        return Token(name, value, line, col)


def compute_indent(line) -> tuple:
    """
    Calcule l'indentation d'une ligne.

    Compte le nombre d'espaces en début de ligne, puis retourne
    le niveau d'indentation ainsi que le reste de la ligne sans
    les espaces initiaux.

    Args:
        line (str): Ligne à analyser.

    Returns:
        tuple[int, str]: Nombre d'espaces en début de ligne et contenu restant.
    """
    i: int = 0
    while i < len(line) and line[i] == " ":
        i += 1
    current_indent: int = i
    rest: str = line[i:]

    return current_indent, rest


def handle_indent(indent: int, indent_stack: IndentStack, line_pos: int) -> Generator[Token, None, None]:
    """
    Gère les changements d'indentation et génère les tokens associés.

    Compare l'indentation actuelle avec celle au sommet de la pile :
    - Si elle augmente, ajoute un niveau et émet un token INDENT.
    - Si elle diminue, retire des niveaux et émet un ou plusieurs tokens DEDENT.

    Args:
        indent (int): Niveau d'indentation de la ligne courante.
        indent_stack (IndentStack): Pile des niveaux d'indentation.
        line_pos (int): Index de la ligne (0-based).

    Yields:
        Token: Token INDENT ou DEDENT selon le changement d'indentation.
    """
    if indent > indent_stack.current():
        indent_stack.push(indent)
        yield Token("INDENT", " " * indent, line_pos+1, 1)
    elif indent < indent_stack.current():
        for _ in range(indent_stack.dedent_to(indent)):
            yield Token("DEDENT", " ", line_pos+1, 1)


def tokenize(line: str, line_pos: int, base_indent: int) -> Generator[Token, None, None]:
    """
    Tokenise une ligne en generant une suite de tokens.

    Parcourt la ligne à l'aide d'une expression régulière construite à partir
    de TOKEN_SPEC et produit les tokens correspondants. Vérifie qu'aucune
    portion de la ligne n'est ignorée (sinon lève une erreur lexicale).
    Ignore les tokens de type SKIP et COMMENT.

    Args:
        line (str): Ligne à analyser.
        line_pos (int): Index de la ligne (0-based).
        base_indent (int): Indentation de base à ajouter aux positions.

    Yields:
        Token: Tokens reconnus dans la ligne.

    Raises:
        SyntaxError: Si une portion de la ligne ne correspond à aucun token.
"""
    regex: str = "|".join(f"(?P<{name}>{pat})" for name, pat in TOKEN_SPEC) # On creer un enorme regex avec chacun de nos TOKEN_SPEC
    pos_in_line: int = 0
    elms_match: Iterator = re.finditer(regex, line) # Recupere tous nos element correspondant a notre regex
        
    for elm_match in elms_match:
        if elm_match.start() != pos_in_line: # On verifie que que notre position actuel est bien le debut de notre match acutel
            chunk = line[pos_in_line:elm_match.start()]
            raise SyntaxError(f"Lexical error line {line_pos+1}, col {base_indent + pos_in_line+1}: {chunk!r}")
            
        token_name, value = elm_match.lastgroup, elm_match.group() # group et lastgroup permettte de recuperer <name> et <pat> definit plus haut dans le regex => e.g (NAME, x)
        if not(token_name in ["SKIP", "COMMENT"]):
            token_col: int = base_indent + elm_match.start() + 1
            yield name_mapping(token_name, value, line_pos+1, token_col)
        pos_in_line = elm_match.end() # On update notre position actuel a la fin du match qu'on vient de traiter
        
    # Si notre derniere element traité ne fini pas a la fin de la ligne, c'est qu'on a un element non voula a la fin. Donc une erreur.
    if pos_in_line != len(line):
            chunk = line[pos_in_line:]
            raise SyntaxError(f"Lexical error line {line_pos+1}, col {base_indent + pos_in_line+1}: {chunk!r}")
    
    yield Token("NEWLINE", "\n", line_pos+1, 1)
 

def flush_dedent(stack: IndentStack, line_pos: int) -> Generator[Token, None, None]:
    """
    Vide la pile d'indentation en générant les tokens DEDENT restants.

    Réduit progressivement l'indentation jusqu'au niveau de base (0)
    en émettant un token DEDENT pour chaque niveau supprimé.

    Args:
        stack (IndentStack): Pile des niveaux d'indentation.
        line_pos (int): Index de la ligne (0-based).

    Yields:
        Token: Tokens DEDENT jusqu'à revenir à l'indentation de base.
    """
    while stack.current() > 0:
        stack.dedent_to(stack.stack[-2])
        yield Token("DEDENT", " ", line_pos+1, 1)


def lex(code: list[str]) -> Generator[Token, None, None]:
    """
    Analyse lexicale d'un code source ligne par ligne.

    Transforme une liste de lignes en une séquence de tokens en gérant :
    - les indentations (INDENT / DEDENT),
    - la tokenisation des éléments de chaque ligne,
    - les lignes vides et commentaires,
    - la fin de fichier (EOF).

    Args:
        code (list[str]): Liste des lignes du code source.

    Yields:
        Token: Suite de tokens représentant le code.

    """
    indent_stack: IndentStack = IndentStack()
    for line_pos, raw_line in enumerate(code):
        line: str = raw_line.replace("\t", " " * 4).rstrip("\n") # On considere les tabulation comme 4 espaces
        stripped: str = line.lstrip(" ")
        if stripped == "" or stripped[0] == "#":
            yield Token("NEWLINE", "\n", line_pos+1, 1) # on considere les ligne vide et les commentaires comme des NEWLINE
            continue

        current_indent, line_rest = compute_indent(line)
        yield from handle_indent(current_indent, indent_stack, line_pos)
        yield from tokenize(line_rest, line_pos, current_indent)
    yield from flush_dedent(indent_stack, line_pos)
    yield Token("EOF", None, line_pos+1, 1) # EOF pour singialer la fin de la liste (End Of File)
