import re
from collections.abc import Iterator, Generator


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
    ("COMMENT",     r"#.*"),
    ("SKIP",        r"[ \t]+"),
]


class IndentStack:
    def __init__(self):
        self.stack = [0]

    def current(self) -> int:
        return self.stack[-1]

    def push(self, indent: int) -> None:
        self.stack.append(indent)

    def dedent_to(self, indent: int) -> int:
        count = 0
        while indent < self.current():
            self.stack.pop()
            count += 1
        if indent != self.current():
            raise IndentationError
        return count
    

class Token:
    def __init__(self, type: str, value: str, line: int, col: int):
        self.type = type
        self.value = value
        self.line = line
        self.col = col

    def __repr__(self):
        return f"{self.type} : {self.value!r}"
    


def name_mapping(name: str, value: str, line: int, col: int) -> Token:
    if name == "NAME" and value in {"def", "return", "if", "elif", "else", "while", "and", "or", "not"}:
        return Token(value.upper(), value, line, col)
    elif name == "STRING":
        return Token(name, value.strip('"'), line, col)
    else:
        return Token(name, value, line, col)


def compute_indent(line) -> tuple:
    i: int = 0
    while i < len(line) and line[i] == " ":
        i += 1
    current_indent: int = i
    rest: str = line[i:]

    return current_indent, rest


def handle_indent(indent: int, indent_stack: IndentStack, line_pos: int) -> Generator[Token, None, None]:
    if indent > indent_stack.current():
        indent_stack.push(indent)
        yield Token("INDENT", " " * indent, line_pos+1, 1)
    elif indent < indent_stack.current():
        for _ in range(indent_stack.dedent_to(indent)):
            yield Token("DEDENT", " ", line_pos+1, 1)


def tokenize(line: str, line_pos: int, base_indent: int) -> Generator[Token, None, None]:
    regex: str = "|".join(f"(?P<{name}>{pat})" for name, pat in TOKEN_SPEC)
    pos_in_line: int = 0
    elms_match: Iterator = re.finditer(regex, line)
        
    for elm_match in elms_match:
        if elm_match.start() != pos_in_line:
            chunk = line[pos_in_line:elm_match.start()]
            raise SyntaxError(f"Lexical error line {line_pos+1}, col {base_indent + pos_in_line+1}: {chunk!r}")
            
        token_name, value = elm_match.lastgroup, elm_match.group()
        if not(token_name in ["SKIP", "COMMENT"]):
            token_col: int = base_indent + elm_match.start() + 1
            # yield Token(token_name, value, line_pos+1, token_col)
            yield name_mapping(token_name, value, line_pos+1, token_col)
        pos_in_line = elm_match.end()
        
    if pos_in_line != len(line):
            chunk = line[pos_in_line:]
            raise SyntaxError(f"Lexical error line {line_pos+1}, col {base_indent + pos_in_line+1}: {chunk!r}")
    
    yield Token("NEWLINE", "\n", line_pos+1, 1)
 

def flush_dedent(stack: IndentStack, line_pos: int) -> Generator[Token, None, None]:
    while stack.current() > 0:
        stack.dedent_to(stack.stack[-2])
        yield Token("DEDENT", " ", line_pos+1, 1)


def lex(code: list[str]) -> Generator[Token, None, None]:
    indent_stack: IndentStack = IndentStack()
    for line_pos, raw_line in enumerate(code):
        line: str = raw_line.replace("\t", " " * 4).rstrip("\n")
        stripped: str = line.lstrip(" ")
        if stripped == "" or stripped[0] == "#":
            yield Token("NEWLINE", "\n", line_pos+1, 1)
            continue

        current_indent, line_rest = compute_indent(line)
        yield from handle_indent(current_indent, indent_stack, line_pos)
        yield from tokenize(line_rest, line_pos, current_indent)
    yield from flush_dedent(indent_stack, line_pos)
    yield Token("EOF", None, line_pos+1, 1)
