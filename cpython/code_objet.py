

from typing import Any


class Instr:
    def __init__(self, op: str, arg: Any | None = None):
        self.op = op
        self.arg = arg


    def __repr__(self):
        if self.arg == None:
            return f"{self.op}"
        else:
            return f"{self.op} {self.arg}"
    

    
class CodeObject:
    def __init__(self, co_name: str = "<module>", co_argcount: int = 0, co_firstlineno: int = 1, co_varnames = None):
        self.co_name = co_name
        self.co_argcount = co_argcount
        self.co_varnames = co_varnames if co_varnames is not None else []
        self.co_names: list[str] = []
        self.co_consts: list[object] = []
        self.co_code: list[Instr] = []
        self.co_firstlineno = co_firstlineno
        self.co_stacksize = 0



class CompilerToCodeObject:
    def __init__(self, ast):
        self.ast = ast
        self.code = CodeObject()

    def compile(self):
        for stmt in self.ast.body:
            self.visit(stmt)
        idx = self.const_index(None)
        self.emit("LOAD_CONST", idx)
        self.emit("RETURN_VALUE")
        return self.code

    def emit(self, op, arg=None):
        instr = Instr(op, arg)
        self.code.co_code.append(instr)

    def emit_jump(self, op):
        self.emit(op)
        idx = len(self.code.co_code) - 1
        return idx
    
    def patch_jump(self, at_index, target_index):
        self.code.co_code[at_index].arg = target_index

    def const_index(self, value):
        for idx, existing in enumerate(self.code.co_consts):
            if (type(value), value) == (type(existing), existing):
                return idx
        self.code.co_consts.append(value)
        return len(self.code.co_consts) - 1
    
    def name_index(self, name: str):
        for idx, existing in enumerate(self.code.co_names):
            if name == existing:
                return idx
        self.code.co_names.append(name)
        return len(self.code.co_names) - 1

    def visit(self, node):
        visit = f"visit_{node.__class__.__name__}"
        method = getattr(self, visit)
        return method(node)

    def visit_Number(self, node):
        idx = self.const_index(node.value)
        self.emit("LOAD_CONST", idx)

    def visit_Name(self, node):
        idx = self.name_index(node.ID)
        self.emit("LOAD_NAME", idx)

    def visit_Assign(self, node):
        self.visit(node.value)
        target_name = node.target.ID
        idx = self.name_index(target_name)
        self.emit("STORE_NAME", idx)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.emit("BINARY_OP", node.op)

    def visit_Call(self, node):
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
        self.emit("CALL", len(node.args))

    def visit_Return(self, node):
        if node.value != None:
            self.visit(node.value)
        else:
            idx = self.const_index(None)
            self.emit("LOAD_CONST", idx)
        self.emit("RETURN_VALUE")

    def visit_Compare(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.emit("COMPARE_OP", node.op)

    def visit_If(self, node):
        self.visit(node.test)
        jump_false_index = self.emit_jump("JUMP_IF_FALSE")
        for stmt in node.body:
            self.visit(stmt)
        if node.orelse:
            jump_end_index = self.emit_jump("JUMP")
            self.patch_jump(jump_false_index, jump_end_index+1)
            for stmt in node.orelse:
                self.visit(stmt)
            self.patch_jump(jump_end_index, len(self.code.co_code))
        else:
            self.patch_jump(jump_false_index, len(self.code.co_code))

    def visit_While(self, node):
        start = len(self.code.co_code)
        self.visit(node.test)
        jump_false_index = self.emit_jump("JUMP_IF_FALSE")
        for stmt in node.body:
            self.visit(stmt)
        self.emit("JUMP", start)
        self.patch_jump(jump_false_index, len(self.code.co_code))

    def visit_Def(self, node):
        func_code = CodeObject(co_name=node.name, co_argcount=len(node.args), co_varnames=list(node.args))

        old_code = self.code
        self.code = func_code
        for stmt in node.body:
            self.visit(stmt)

        if not node.body or node.body[-1].__class__.__name__ != "Return":
            idx_none = self.const_index(None)
            self.emit("LOAD_CONST", idx_none)
            self.emit("RETURN_VALUE")
            
        self.code = old_code

        const_idx = len(self.code.co_consts)
        self.code.co_consts.append(func_code)

        self.emit("LOAD_CONST", const_idx)
        self.emit("MAKE_FUNCTION")
        self.emit("STORE_NAME", self.name_index(node.name))


    def visit_ExprStmt(self, node): 
        self.visit(node.expr)
        self.emit("POP_TOP")