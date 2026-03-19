import dis
from code_objet import CompilerToCodeObject, CodeObject, Instr
import builtins  #Sert a importer les fonctions de base de python pour la gestion des print


class Stack():

    def __init__(self):
        self.pile = []
    
    def taille(self):
        return len(self.pile)
    
    def empiler(self, elt):
        self.pile.append(elt)
    
    def depiler(self):
        return self.pile.pop()

    def clearAll(self):
        while len(self.pile)>0:
            self.pile.pop()

    def pushAll(self):
        new = []
        while len(self.pile)>0:
            new += [self.pile.pop()]
        return new
    
class Function():
    def __init__(self, code_obj, closure):
        self.code = code_obj
        self.argcount = code_obj.co_argcount
        if closure is not None:
            self.closure= closure
        else :
            self.closure = {}


class Frame():

    def __init__(self, bytecode:Bytecode, locals:dict, closure=None): #chaque frame à ses propres variables locales, son propre bytecode, et donc son propre stack
        self.btc = bytecode
        self.loc = locals
        self.stack = Stack()
        self.pointeur = 0
        if closure is not None:
            self.closure = closure
        else:
            self.closure = {}


    def next(self):
        """Renvoie l'instruction d'après dans le bytecode de la frame"""
        result = self.btc.inst(self.pointeur)
        self.pointeur+=1
        return result

    def estVide(self):
        """Renvoie si le frame est vide"""
        return self.pointeur > len(self.btc.bytecode)-1
    
    def stackAdd(self, res):
        """Empile sur le stack du frame"""
        self.stack.empiler(res)

    def stackRem(self):
        """Dépile"""
        return self.stack.depiler()



class Bytecode():

    def __init__(self):
        self.bytecode = []

    def ajouter_instruction(self, name, value=None):
        """Permet d'ajouter une instruction bytecode à la liste d'instruction. Selon l'instruction, la valeur peut être None"""
        self.bytecode.append((name, value))
    
    def inst(self, ind:int):
        """Renvoie l'instruction a l'indice ind"""
        return self.bytecode[ind]
    
    
    
def miniVm(instructions:Bytecode):
    """Fonction qui prend en entrée une liste d'instruction de bytecode et l'execute. Fait l'effet d'une "mini VM Python" ou un interprêteur de Bytecode créé pour des fonctions de base simples"""
    functions = {}
    global_vars = {}  # dictionnaire pour le niveau module
    call_stack = Stack()
    current_frame = Frame(instructions, {})
    res = None
    while not current_frame.estVide():
        inst = current_frame.next()
        if inst[0] == "LOAD_CONST":
            current_frame.stackAdd(inst[1])
        elif inst[0] == "LOAD_FAST":
            current_frame.stackAdd(current_frame.loc[inst[1]])
        elif inst[0] == "STORE_FAST":
            current_frame.loc[inst[1]] = current_frame.stackRem()
        elif inst[0] == "BINARY_OP":
            if inst[1] == "PLUS":
                addition = current_frame.stackRem() + current_frame.stackRem()
                current_frame.stackAdd(addition)
            elif inst[1] == "MINUS":
                b = current_frame.stackRem()
                a = current_frame.stackRem()
                soustraction = a - b
                current_frame.stackAdd(soustraction)
            elif inst[1] == "STAR":
                multiplication = current_frame.stackRem() * current_frame.stackRem()
                current_frame.stackAdd(multiplication)
            elif inst[1] == "SLASH":
                b = current_frame.stackRem()
                a = current_frame.stackRem()
                division = a / b
                current_frame.stackAdd(division)
            elif inst[1] == "PERCENT":
                b = current_frame.stackRem()
                a = current_frame.stackRem()
                division = a%b
                current_frame.stackAdd(division)
        elif inst[0] == "COMPARE_OP":
            b = current_frame.stackRem()
            a = current_frame.stackRem()
            op = inst[1]
            if op == "EQEQ":
                current_frame.stackAdd(a == b)
            elif op == "LT":
                current_frame.stackAdd(a < b)
            elif op == "GT":
                current_frame.stackAdd(a > b)
            elif op == "LE":
                current_frame.stackAdd(a <= b)
            elif op == "GE":
                current_frame.stackAdd(a >= b)
            elif op == "NOTEQ":
                current_frame.stackAdd(a != b)
        elif inst[0] == "POP_JUMP_IF_FALSE":
            condition = current_frame.stackRem()
            if not condition:
                current_frame.pointeur = inst[1] - 1  # -1 car next() incrémente le pointeur
        elif inst[0] == "POP_JUMP_IF_TRUE":
            condition = current_frame.stackRem()
            if condition:
                current_frame.pointeur = inst[1] - 1
        elif inst[0] == "JUMP_ABSOLUTE":
            current_frame.pointeur = inst[1]
        elif inst[0] == "MAKE_FUNCTION":
            code_obj = current_frame.stackRem()
            closure = current_frame.loc.copy() #recupère les variables actuelles
            func = Function(code_obj, closure)
            current_frame.stackAdd(func)
        elif inst[0] == "CALL":
            arg_count = inst[1]
            args = []

            for i in range(arg_count):
                args.append(current_frame.stackRem())
            args.reverse()
            func = current_frame.stackRem()

            # fonction python builtin. permet de gerer print par exemple
            if callable(func):
                result = func(*args)
                current_frame.stackAdd(result)
            else:
                call_stack.empiler(current_frame)
                func_code = func.code
                func_bytecode = coCodeToBytecode(func_code)
                new_locals = {}

                #Passe les arguments aux fonctions
                for i, val in enumerate(func.code.co_varnames[:func.argcount]): #slice pour prendre uniquement les arguments de la fonction, et eviter un index error
                    new_locals[val] = args[i]

                current_frame = Frame(func_bytecode, new_locals)
                current_frame.closure = func.closure

        elif inst[0] == "RETURN_VALUE":
            value = current_frame.stackRem()
            if call_stack.taille() == 0: #fin du programme
                return value  
            current_frame = call_stack.depiler()
            current_frame.stackAdd(value)
        elif inst[0] == "STORE_NAME":
            name = inst[1]  # inst[1] est déjà le nom de la variable
            if call_stack.taille() == 0:
                global_vars[name] = current_frame.stackRem()
            else:
                current_frame.loc[name] = current_frame.stackRem()
        elif inst[0] == "LOAD_NAME":
            name = inst[1]
            if name in current_frame.loc:
                value = current_frame.loc[name]
            elif name in current_frame.closure:
                value = current_frame.closure[name]
            elif name in global_vars:
                value = global_vars[name]
            #pont vers les fonctions natives de Python (j'ai été aidé par l'IA pour celle là)
            elif hasattr(builtins, name): 
                value = getattr(builtins, name)
            else:
                raise NameError(f"name '{name}' is not defined")
            current_frame.stackAdd(value)
        elif inst[0] == "POP_TOP":
            current_frame.stackRem()

    if current_frame.stack.taille() > 0:
        res = current_frame.stackRem()
    return res


def coCodeToBytecode(code_object : CompilerToCodeObject):
    """Transforme le code objet en instructions de bytecode executable par ma vm"""
    bytecode = code_object.co_code
    varnames = code_object.co_varnames
    consts = code_object.co_consts
    names = code_object.co_names
    btc = Bytecode()
    
    for i in range(0, len(bytecode)):
        op = bytecode[i].op
        arg = bytecode[i].arg
        
        if op == "LOAD_CONST":
            btc.ajouter_instruction(op, consts[arg])
        #les operations qui utilisent "names"
        elif op in ("LOAD_NAME", "STORE_NAME", "LOAD_GLOBAL", "STORE_GLOBAL"):
            btc.ajouter_instruction(op, names[arg])
        #les operations qui utilisent "varnames"
        elif op in ("LOAD_FAST", "STORE_FAST"):
            btc.ajouter_instruction(op, varnames[arg])
        else:
            btc.ajouter_instruction(op, arg)
            
    return btc
        
#test pour mes closures (j'ai fait creer le bytecode par une IA)

#Cette fonction est la fonction que je teste :

# def outer():
#     x = 10
    
#     def inner():
#         return x
    
#     return inner

# f = outer()
# print(f())  → 10



# --- inner ---
inner_code = CodeObject(
    co_name="inner",
    co_argcount=0,
    co_varnames=[]
)

inner_code.co_names = ["x"]
inner_code.co_consts = []
inner_code.co_code = [
    Instr("LOAD_NAME", 0),   # x
    Instr("RETURN_VALUE", None)
]


# --- outer ---
outer_code = CodeObject(
    co_name="outer",
    co_argcount=0,
    co_varnames=[]
)

outer_code.co_names = ["x", "inner"]
outer_code.co_consts = [10, inner_code]

outer_code.co_code = [
    Instr("LOAD_CONST", 0),   # 10
    Instr("STORE_NAME", 0),   # x

    Instr("LOAD_CONST", 1),   # inner_code
    Instr("MAKE_FUNCTION", None),
    Instr("STORE_NAME", 1),   # inner

    Instr("LOAD_NAME", 1),    # inner
    Instr("RETURN_VALUE", None)
]


# --- module ---
module_code = CodeObject()

module_code.co_names = ["outer", "f", "print"]
module_code.co_consts = [outer_code, None]

module_code.co_code = [
    Instr("LOAD_CONST", 0),   # outer_code
    Instr("MAKE_FUNCTION", None),
    Instr("STORE_NAME", 0),   # outer

    Instr("LOAD_NAME", 0),    # outer
    Instr("CALL", 0),
    Instr("STORE_NAME", 1),   # f

    Instr("LOAD_NAME", 2),    # print
    Instr("LOAD_NAME", 1),    # f
    Instr("CALL", 0),
    Instr("CALL", 1),
    Instr("POP_TOP", None),

    Instr("LOAD_CONST", 1),   # None
    Instr("RETURN_VALUE", None)
]


btc = coCodeToBytecode(module_code)
print(miniVm(btc))