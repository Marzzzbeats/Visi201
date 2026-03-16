

from typing import Any
from ast_node import *

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
    
    # utilitaire

    def emit(self, op, arg=None):
        instr = Instr(op, arg)
        self.code.co_code.append(instr)

    def emit_jump(self, op):
        self.emit(op)
        idx = len(self.code.co_code) - 1
        return idx
    
    def patch_jump(self, at_index, target_index):
        self.code.co_code[at_index].arg = target_index

    def in_function(self):
        return self.code.co_name != "<module>"
    

    # les indexs

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
    
    def varname_index(self, varname: str):
        for idx, existing in enumerate(self.code.co_varnames):
            if varname == existing:
                return idx
        self.code.co_varnames.append(varname)
        return len(self.code.co_varnames) - 1
    
    def fast_index(self, varname: str):
        for idx, existing in enumerate(self.code.co_varnames):
            if varname == existing:
                return idx
        raise NotImplementedError
    

    # la partie qui compile

    def visit(self, node):
        visit = f"visit_{node.__class__.__name__}"
        method = getattr(self, visit)
        return method(node)
    
    def visit_Boolean(self, node):
        idx = self.const_index(node.value)
        self.emit("LOAD_CONST", idx)

    def visit_Number(self, node):
        idx = self.const_index(node.value)
        self.emit("LOAD_CONST", idx)

    def visit_String(self, node):
        idx = self.const_index(node.value)
        self.emit("LOAD_CONST", idx)

    def visit_NoneLiteral(self, node):
        idx = self.const_index(node.value)
        self.emit("LOAD_CONST", idx)

    def visit_Name(self, node):
        if self.in_function() and node.ID in self.code.co_varnames:
            idx = self.fast_index(node.ID)
            self.emit("LOAD_FAST", idx)
        else:
            idx = self.name_index(node.ID)
            self.emit("LOAD_NAME", idx)

    def visit_ListNode(self, node):
        for value in node.values:
            self.visit(value)
        self.emit("BUILD_LIST", len(node.values))

    def visit_DictNode(self, node):
        for key, value in zip(node.keys, node.values):
            self.visit(key)
            self.visit(value)
        self.emit("BUILD_DICT", len(node.keys))

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.visit(node.index)
        self.emit("BINARY_SUBSCR")

    def visit_Assign(self, node):
        if isinstance(node.target, Name):
            self.visit(node.value)
            if not self.in_function():
                target_name = node.target.ID
                idx = self.name_index(target_name)
                self.emit("STORE_NAME", idx)
            else:
                target_name = node.target.ID
                idx = self.varname_index(target_name)
                self.emit("STORE_FAST", idx)
        elif isinstance(node.target, Subscript):
            self.visit(node.target.value)
            self.visit(node.target.index)
            self.visit(node.value)
            self.emit("STORE_SUBSCR")
        else:
            raise NotImplementedError(f"Unsupported assignment target: {type(node.target).__name__}")

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)
        self.emit("BINARY_OP", node.op)

    def visit_UnaryOp(self, node):
        self.visit(node.operand)
        if node.op == "MINUS":
            self.emit("UNARY_NEGATIVE")
        elif node.op == "NOT":
            self.emit("UNARY_NOT")
        else:
            raise SyntaxError
    
    def visit_BoolOp(self, node):
        self.visit(node.left)
        if node.op == "AND":
            jump_end_index = self.emit_jump("JUMP_IF_FALSE")
        elif node.op == "OR":
            jump_end_index = self.emit_jump("JUMP_IF_TRUE")
        self.emit("POP_TOP")
        self.visit(node.right)
        self.patch_jump(jump_end_index, len(self.code.co_code))

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

    def visit_Call(self, node):
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
        self.emit("CALL", len(node.args))

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