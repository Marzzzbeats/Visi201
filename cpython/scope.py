



class ScopeInfo:
    def __init__(self, kind: str, name: str, parent: "ScopeInfo"|None):
        self.kind = kind
        self.name = name
        self.parent = parent
        self.children = []
        self.assigned_here = set()
        self.used_here = set()
        self.cellvars = set()
        self.freevars = set()



class ScopeAnalyzer:
    def __init__(self):
        self.current_scope = ScopeInfo("module", "module", None)
        self.scope_stack = [self.current_scope]
        self.scope_map = {}

    def push(self, scope):
        self.scope_stack.append(scope)
        self.current_scope = scope

    def pop_top(self):
        if len(self.scope_stack) >= 2:
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
        else:
            raise IndexError

    def resolve_scope(self, scope):
        # child first
        for child in scope.children:
            self.resolve_scope(child)

        # freevars
        locals_here = scope.assigned_here # args included in visit_Def
        for used in scope.used_here:
            # its normal so skip
            if used in locals_here:
                continue
            
            # We loop trough all possible parents
            parent = scope.parent
            found_in_parent = False
            while parent is not None:
                if used in parent.assigned_here:
                    found_in_parent = True
                    break
                parent = parent.parent
            
            if found_in_parent:
                scope.freevars.add(used)

        # cellvars
        for child in scope.children:
            for name in child.freevars:
                if name in locals_here:
                    scope.cellvars.add(name)

        



    def analyze(self, node):
        self.visit(node)
        self.resolve_scope(self.scope_stack[0])
        return self.scope_map
    


    def visit(self, node):
        visit = f"visit_{node.__class__.__name__}"
        if node.__class__.__name__ in ["Def", "Module", "Name", "Assign"]:
            method = getattr(self, visit)
            return method(node)
    
    def visit_Module(self, node):
        for stmt in node.body:
            self.visit(stmt)

    def visit_Def(self, node):
        func_scope = ScopeInfo("function", node.name, self.scope_stack[-1])
        for arg in node.args:
            func_scope.assigned_here.add(arg)
        self.current_scope.children.append(func_scope)
        self.scope_map[node] = func_scope
        self.push(func_scope)
        for stmt in node.body:
            self.visit(stmt)
        self.pop_top()

    def visit_Assign(self, node):
        self.current_scope.assigned_here.add(node.target.ID)
        self.visit(node.value)

    def visit_Name(self, node):
        self.current_scope.used_here.add(node.ID)


    def visit_ExprStmt(self, node):
        self.visit(node.expr)

    def visit_Return(self, node):
        if node.value is not None:
            self.visit(node.value)

    def visit_If(self, node):
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)
        for stmt in node.orelse:
            self.visit(stmt)

    def visit_While(self, node):
        self.visit(node.test)
        for stmt in node.body:
            self.visit(stmt)

    def visit_BinOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_BoolOp(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_Compare(self, node):
        self.visit(node.left)
        self.visit(node.right)

    def visit_UnaryOp(self, node):
        self.visit(node.operand)

    def visit_ListNode(self, node):
        for value in node.values:
            self.visit(value)

    def visit_DictNode(self, node):
        for key in node.keys:
            self.visit(key)
        for value in node.values:
            self.visit(value)

    def visit_Subscript(self, node):
        self.visit(node.value)
        self.visit(node.index)

    def visit_Call(self, node):
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
    