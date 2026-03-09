

class Module:
    def __init__(self, body):
        self.body = body

    def __repr__(self):
        res = "Module(\n\tbody=["
        for i, stmt in enumerate(self.body):
            res += f"\n\t\t{stmt}"
            if i < len(self.body) - 1:
                res += ","
        res += "\n\t]\n)"
        return res


# ---------- base ----------
class Node:
    pass


class Stmt(Node):
    pass


class Expr(Node):
    pass


# ---------- expressions ----------

class Boolean(Expr):
    def __init__(self, value):
        self.value = value

    def __repr__(self):
        return f"Bool({self.value})"

class Number(Expr):
    def __init__(self, value: int):
        self.value = value

    def __repr__(self):
        return f"Number({self.value})"


class Name(Expr):
    def __init__(self, ID: str):
        self.ID = ID

    def __repr__(self):
        return f"Name({self.ID})"


class Compare(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"Compare({self.left} {self.op} {self.right})"


class BinOp(Expr):
    def __init__(self, left: Expr, op: str, right: Expr):
        self.left = left
        self.op = op
        self.right = right

    def __repr__(self):
        return f"BinOp({self.left} {self.op} {self.right})"


# ---------- statements ----------
class ExprStmt(Stmt):
    def __init__(self, expr: Expr):
        self.expr = expr

    def __repr__(self):
        return f"ExprStmt({self.expr})"


class Assign(Stmt):
    def __init__(self, target: Name, value: Expr):
        self.target = target
        self.value = value

    def __repr__(self):
        return f"Assign({self.target} = {self.value})"


class Return(Stmt):
    def __init__(self, value: Expr | None):
        self.value = value

    def __repr__(self):
        return f"Return({self.value})"


class If(Stmt):
    def __init__(self, test: Expr, body: list[Stmt], orelse: list[Stmt]):
        self.test = test
        self.body = body
        self.orelse = orelse

    def __repr__(self):
        return f"If(test={self.test}, body={self.body}, orelse={self.orelse})"


class While(Stmt):
    def __init__(self, test: Expr, body: list[Stmt]):
        self.test = test
        self.body = body

    def __repr__(self):
        return f"While(test={self.test}, body={self.body})"


class Def:
    def __init__(self, name: str, args: list[str], body: list[Stmt]):
        self.name = name
        self.args = args
        self.body = body

    def __repr__(self):
        return f"Def(name={self.name}, args={self.args}, body={self.body})"
    

class Call(Expr):
    def __init__(self, func: Expr, args: list[Expr]):
        self.func = func
        self.args = args
    def __repr__(self):
        return f"Call(func={self.func}, args={self.args})"