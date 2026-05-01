
####################################
##             SCOPE              ##
####################################

## Gere les differents scopes et renvoie une scopemap



def dump_scope(scope_obj, indent=0):
    """
    Construit une représentation textuelle d'un objet de portée (scope).

    Args:
        scope_obj: Objet de scope à afficher.
        indent (int): Nombre d'espaces d'indentation.

    Returns:
        str: Représentation formatée du scope.
    """
    s = ""
    for line in scope_obj.manual_repr():
        s += " " * indent + line
    # for child in scope_obj.children:
    #     s += "\n" + dump_scope(child, indent + 8)
    return s



class ScopeInfo:
    """
    Représente les informations de portée (scope) pour l'analyse des variables.

    Stocke les variables définies, utilisées, ainsi que celles impliquées
    dans les fermetures (cellvars et freevars), afin de préparer la compilation.

    Attributes:
        kind (str): Type de scope (module, fonction, classe, etc.).
        name (str): Nom du scope.
        parent (ScopeInfo | None): Scope parent.
        children (list[ScopeInfo]): Sous-scopes imbriqués.
        assigned_here (set[str]): Variables définies dans ce scope.
        used_here (set[str]): Variables utilisées dans ce scope.
        cellvars (set[str]): Variables locales capturées par des scopes enfants.
        freevars (set[str]): Variables provenant d'un scope parent.
    """
    def __init__(self, kind: str, name: str, parent):
        self.kind = kind
        self.name = name
        self.parent = parent
        self.children = []
        self.assigned_here = set()
        self.used_here = set()
        self.cellvars = set()
        self.freevars = set()
    
    def manual_repr(self):
        return [
            f"ScopeInfo(\n",
            f"  kind={self.kind!r}, name={self.name!r},\n",
            f"  assigned={sorted(self.assigned_here)},\n",
            f"  used={sorted(self.used_here)},\n",
            f"  cellvars={sorted(self.cellvars)},\n",
            f"  freevars={sorted(self.freevars)}\n",
            f")"
        ]



class ScopeAnalyzer:
    """
    Analyse les portées (scopes) d'un AST afin de déterminer les variables locales,
    libres (freevars) et capturées (cellvars).

    Parcourt l'arbre syntaxique, construit une hiérarchie de scopes, puis résout
    les dépendances entre eux pour identifier les fermetures nécessaires.

    Attributes:
        current_scope (ScopeInfo): Scope courant lors de l'analyse.
        scope_stack (list[ScopeInfo]): Pile des scopes imbriqués.
        scope_map (dict[Node, ScopeInfo]): Association entre nœuds et leurs scopes.
    """
        
    def __init__(self):
        self.current_scope = ScopeInfo("module", "module", None)
        self.scope_stack = [self.current_scope]
        self.scope_map = {}

    def push(self, scope):
        """
        Ajoute un nouveau scope sur la pile et le définit comme courant.

        Args:
            scope (ScopeInfo): Scope à empiler.
        """
        self.scope_stack.append(scope)
        self.current_scope = scope

    def pop_top(self):
        """
        Retire le scope courant et revient au scope parent.

        Raises:
            IndexError: Si tentative de dépiler le scope racine.
        """
        if len(self.scope_stack) >= 2:
            self.scope_stack.pop()
            self.current_scope = self.scope_stack[-1]
        else:
            raise IndexError

    def resolve_scope(self, scope):
        """
        Résout les variables libres (freevars) et capturées (cellvars) pour un scope.

        Parcourt récursivement les sous-scopes, puis :
        - identifie les freevars en recherchant les variables utilisées mais non locales,
        - détermine les cellvars à partir des besoins des scopes enfants.

        Args:
            scope (ScopeInfo): Scope à analyser.
        """
        # On detecte les enfants d'abbord (pour avoir les ) car on en a besoin pour 
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
                else:
                    scope.freevars.add(name)

        



    def analyze(self, node):
        self.visit(node)
        self.resolve_scope(self.scope_stack[0])
        return self.scope_map
    


    def visit(self, node):
        """
        Applique dynamiquement la méthode de visite correspondant au type du nœud.

        Construit le nom de la méthode sous la forme "visit_<NomDuNoeud>" et
        l'appelle si elle existe.

        Args:
            node (Node): Nœud de l'AST à visiter.

        Returns:
            Any: Résultat de la méthode de visite, ou None si aucune méthode n'est définie.
        """
        visit = f"visit_{node.__class__.__name__}"
        method = getattr(self, visit, None)
        if method is not None:
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

    def visit_ClassDef(self, node):
        for stmt in node.body:
            self.visit(stmt)

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
    