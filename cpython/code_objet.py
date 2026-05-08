
####################################
##      compilation pipeline      ##
####################################

## Ce fichier permet de transformer notre AST en un code objet
## A noter que ce code object contient bien le bytcode



from typing import Any
from .ast_node import *

class Instr:
    """
    Représente une instruction de la machine virtuelle.

    Une instruction est composée d'une opération (opcode) et éventuellement
    d'un argument associé.

    Attributes:
        op (str): Nom de l'opération (ex: LOAD_CONST, ADD, JUMP, etc.).
        arg (Any | None): Argument de l'instruction, si nécessaire.
    """
    def __init__(self, op: str, arg: Any | None = None):
        self.op: str = op
        self.arg: Any = arg

    def __repr__(self):
        if self.arg == None:
            return f"{self.op}"
        else:
            return f"{self.op} {self.arg}"
    

    
class CodeObject:
    """
    Représente un objet de code compilé.

    Contient toutes les informations nécessaires à l'exécution d'un bloc
    de code par la machine virtuelle : instructions, constantes, noms
    et variables.

    Attributes:
        co_name (str): Nom du bloc de code (fonction, module, etc.).
        co_argcount (int): Nombre d'arguments attendus.
        co_varnames (list[str]): Noms des variables locales.
        co_names (list[str]): Noms utilisés (variables globales, attributs, etc.).
        co_consts (list[object]): Constantes utilisées dans le code.
        co_code (list[Instr]): Liste des instructions à exécuter.
        co_cellvars (list[str]): Variables locales capturées (closures).
        co_freevars (list[str]): Variables libres provenant d'un scope externe.
        co_firstlineno (int): Numéro de la première ligne du code source.
        co_stacksize (int): Taille maximale de la pile nécessaire à l'exécution.
    """
    def __init__(self, co_name: str = "<module>", co_argcount: int = 0, co_firstlineno: int = 1, co_varnames = None):
        self.co_name: str = co_name
        self.co_argcount: int = co_argcount
        self.co_varnames: list[str] = co_varnames if co_varnames is not None else []
        self.co_names: list[str] = []
        self.co_consts: list[object] = []
        self.co_code: list[Instr] = []
        self.co_cellvars: list[str] = []
        self.co_freevars: list[str] = []
        self.co_firstlineno = co_firstlineno
        self.co_stacksize: int = 0



class CompilerToCodeObject:
    """
    Compile un AST en objet de code exécutable.

    Transforme les nœuds de l'AST en une séquence d'instructions
    adaptées à la machine virtuelle, tout en construisant les
    structures associées (constantes, noms, variables, etc.).

    Responsabilités:
        - Parcourir l'AST.
        - Générer les instructions (bytecode/pseudo-bytecode).
        - Gérer les constantes et les noms.
        - Construire un CodeObject prêt à être exécuté.

    Sortie:
        CodeObject: Représentation compilée du programme.
    """
    def __init__(self, ast, scope_map):
        self.ast = ast
        self.scope_map = scope_map
        self.code: CodeObject = CodeObject()

    def compile(self):
        """
        Compile l'AST en instructions exécutables.

        Parcourt les instructions du module, génère les instructions
        correspondantes, puis ajoute un retour implicite (None).

        Returns:
            CodeObject: Objet de code compilé prêt à être exécuté.
        """
        for stmt in self.ast.body:
            self.visit(stmt)
        idx = self.const_index(None)
        self.emit("LOAD_CONST", idx)
        self.emit("RETURN_VALUE")
        return self.code
    
    # utilitaire

    def emit(self, op, arg=None):
        """
        Ajoute une instruction à la séquence de code.

        Args:
            op (str): Opcode de l'instruction.
            arg (Any, optional): Argument associé.
        """
        instr = Instr(op, arg)
        self.code.co_code.append(instr)

    def emit_jump(self, op):
        """
        Ajoute une instruction de saut et retourne son index.
        Permet de patcher la cible ultérieurement.

        Args:
            op (str): Opcode de saut.

        Returns:
            int: Index de l'instruction ajoutée.
        """
        self.emit(op)
        idx = len(self.code.co_code) - 1
        return idx
    
    def patch_jump(self, at_index, target_index):
        """
        Met à jour la cible d'une instruction de saut.

        Args:
            at_index (int): Index de l'instruction à modifier.
            target_index (int): Index cible du saut.
        """
        self.code.co_code[at_index].arg = target_index

    def in_function(self):
        """
        Indique si la compilation est en cours dans une fonction.

        Returns:
            bool: True si dans une fonction, False si au niveau module.
        """
        return self.code.co_name != "<module>"
    

    # les indexs

    def const_index(self, value):
        """
        Retourne l'index d'une constante dans le pool, en l'ajoutant si nécessaire.
        Compare à la fois le type et la valeur pour éviter les collisions.

        Args:
            value (Any): Constante à enregistrer.

        Returns:
            int: Index de la constante dans co_consts.
        """
        for idx, existing in enumerate(self.code.co_consts):
            if (type(value), value) == (type(existing), existing):
                return idx
        self.code.co_consts.append(value)
        return len(self.code.co_consts) - 1
    
    def name_index(self, name: str):
        """
        Retourne l'index d'un nom dans le pool, en l'ajoutant si nécessaire.

        Args:
            name (str): Nom à enregistrer.

        Returns:
            int: Index dans co_names.
        """
        for idx, existing in enumerate(self.code.co_names):
            if name == existing:
                return idx
        self.code.co_names.append(name)
        return len(self.code.co_names) - 1
    
    def varname_index(self, varname: str):
        """
        Retourne l'index d'une variable locale, en l'ajoutant si nécessaire.

        Args:
            varname (str): Nom de variable.

        Returns:
            int: Index dans co_varnames.
        """
        for idx, existing in enumerate(self.code.co_varnames):
            if varname == existing:
                return idx
        self.code.co_varnames.append(varname)
        return len(self.code.co_varnames) - 1
    
    def fast_index(self, varname: str):
        """
        Retourne l'index d'une variable locale existante.

        Args:
            varname (str): Nom de variable.

        Returns:
            int: Index dans co_varnames.

        Raises:
            NotImplementedError: Si la variable n'existe pas.
        """
        for idx, existing in enumerate(self.code.co_varnames):
            if varname == existing:
                return idx
        raise NotImplementedError
    
    def freevar_index(self, varname: str):
        """
        Retourne l'index d'une variable libre (freevar).

        Args:
            varname (str): Nom de variable.

        Returns:
            int: Index dans co_freevars.

        Raises:
            NotImplementedError: Si la variable n'existe pas.
        """
        for idx, existing in enumerate(self.code.co_freevars):
            if varname == existing:
                return idx
        raise NotImplementedError
    
    def cellvar_index(self, varname: str):
        """
        Retourne l'index d'une variable de cellule (cellvar).

        Args:
            varname (str): Nom de variable.

        Returns:
            int: Index dans co_cellvars.

        Raises:
            NotImplementedError: Si la variable n'existe pas.
        """
        for idx, existing in enumerate(self.code.co_cellvars):
            if varname == existing:
                return idx
        raise NotImplementedError
    
    def deref_index(self, name):
        """
        Retourne l'index d'une variable dans l'espace de fermeture.

        Les cellvars sont indexées en premier, suivies des freevars,
        conformément à la convention CPython.

        Args:
            name (str): Nom de la variable.

        Returns:
            int: Index combiné dans l'espace de fermeture.
        """
        # IMPORTANT : cellvars puis freevars (Cpython fait comme ca Convention)
        try:
            return self.code.co_cellvars.index(name)
        except ValueError:
            return len(self.code.co_cellvars) + self.code.co_freevars.index(name)


    # la partie qui compile

    def visit(self, node):
        """
        Applique dynamiquement la méthode de visite correspondant au type du nœud.

        Construit le nom de la méthode sous la forme "visit_<NomDuNoeud>" et
        l'appelle pour traiter le nœud.

        Args:
            node (Node): Nœud de l'AST à visiter.

        Returns:
            Any: Résultat de la méthode de visite associée.

        Raises:
            AttributeError: Si aucune méthode de visite n'est définie pour ce type de nœud.
        """
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
        if self.in_function():
            if node.ID in self.code.co_freevars:
                idx = self.freevar_index(node.ID)
                self.emit("LOAD_DEREF", idx)
            elif node.ID in self.code.co_cellvars:
                idx = self.cellvar_index(node.ID)
                self.emit("LOAD_DEREF", idx)
            elif node.ID in self.code.co_varnames:
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

    def visit_Attribute(self, node):
        self.visit(node.inst)
        self.emit("LOAD_ATTR", self.name_index(node.attribute))

    def visit_Assign(self, node):
        if isinstance(node.target, Name): # On differencie un x= d'un x[y]=
            self.visit(node.value)
            if not self.in_function(): # cas classique
                target_name = node.target.ID
                idx = self.name_index(target_name)
                self.emit("STORE_NAME", idx)
            else:
                target_name = node.target.ID
                if target_name in self.code.co_cellvars: # cas closure
                    idx = self.cellvar_index(target_name)
                    self.varname_index(target_name)
                    self.emit("STORE_DEREF", idx)
                else: # cas var local
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
        jump_false_index = self.emit_jump("POP_JUMP_IF_FALSE")
        for stmt in node.body:
            self.visit(stmt)
        if node.orelse:
            jump_end_index = self.emit_jump("JUMP_ABSOLUTE")
            self.patch_jump(jump_false_index, jump_end_index+1)
            for stmt in node.orelse:
                self.visit(stmt)
            self.patch_jump(jump_end_index, len(self.code.co_code))
        else:
            self.patch_jump(jump_false_index, len(self.code.co_code))

    def visit_While(self, node):
        start = len(self.code.co_code)
        self.visit(node.test)
        jump_false_index = self.emit_jump("POP_JUMP_IF_FALSE")
        for stmt in node.body:
            self.visit(stmt)
        self.emit("JUMP_ABSOLUTE", start)
        self.patch_jump(jump_false_index, len(self.code.co_code))

    def visit_PassNode(self, node):
        pass

    def visit_Call(self, node):
        self.visit(node.func)
        for arg in node.args:
            self.visit(arg)
        self.emit("CALL", len(node.args))

    def visit_Def(self, node):
        """
        Compile une définition de fonction.

        Crée un nouveau CodeObject pour la fonction, compile son corps dans
        ce contexte, puis génère les instructions nécessaires à sa création
        et à son stockage dans l'environnement courant.

        Gère également les variables de fermeture (cellvars et freevars)
        en construisant la structure attendue par la machine virtuelle.

        Args:
            node (Def): Nœud représentant la définition de fonction.
        """
        # On creer un nouveau code objet pour la fonction et on y met les info necessaire
        func_code: CodeObject = CodeObject(co_name=node.name, co_argcount=len(node.args), co_varnames=list(node.args))
        scope_node = self.scope_map[node]
        func_code.co_cellvars = list(scope_node.cellvars)
        func_code.co_freevars = list(scope_node.freevars)

        # On sauvgarde notre codeobjet actuel et on le remplace par le code objet de la fonctio
        old_code = self.code
        self.code = func_code

        # On compile le body de la fonction
        for stmt in node.body:
            self.visit(stmt)

        # On ajoute un return None a la fin si il y'en a pas
        if not node.body or node.body[-1].__class__.__name__ != "Return":
            idx_none = self.const_index(None)
            self.emit("LOAD_CONST", idx_none)
            self.emit("RETURN_VALUE")
        
        # On restaure notre ancien code objet
        self.code = old_code

        # On emet les closures
        for freevar in func_code.co_freevars:
            idx = self.deref_index(freevar)
            self.emit("LOAD_CLOSURE", idx)
        self.emit("BUILD_LIST", len(func_code.co_freevars))

        const_idx = len(self.code.co_consts)
        self.code.co_consts.append(func_code)

        # On emet la fonction
        self.emit("LOAD_CONST", const_idx)
        self.emit("MAKE_FUNCTION")
        self.emit("STORE_NAME", self.name_index(node.name))

    def visit_ClassDef(self, node):
        class_obj = CodeObject(co_name=node.name, co_argcount=0, co_varnames=[])
        
        old_code = self.code
        self.code = class_obj

        for stmt in node.body:
            self.visit(stmt)
        
        if not node.body or node.body[-1].__class__.__name__ != "Return":
            idx_none = self.const_index(None)
            self.emit("LOAD_CONST", idx_none)
            self.emit("RETURN_VALUE")

        self.code = old_code

        
        const_idx = len(self.code.co_consts)
        self.code.co_consts.append(class_obj)

        class_name_const_idx = self.const_index(node.name)
        self.emit("LOAD_CONST", class_name_const_idx)
        self.emit("LOAD_CONST", const_idx)
        self.emit("MAKE_CLASS")
        self.emit("STORE_NAME", self.name_index(node.name))

    def visit_Try(self, node: Try):
        handler_start = len(self.code.co_code)
        jump_to_handler = self.emit_jump("SETUP_TRY")

        for stmt in node.body:
            self.visit(stmt)

        self.emit("POP_TRY")
        jump_end = self.emit_jump("JUMP_ABSOLUTE")
        handler_index = len(self.code.co_code)
        self.patch_jump(jump_to_handler, handler_index)

        for handler in node.handlers:
            for stmt in handler.body:
                self.visit(stmt)

        end_index = len(self.code.co_code)
        self.patch_jump(jump_end, end_index)

    def visit_ExprStmt(self, node): 
        self.visit(node.expr)
        self.emit("POP_TOP")