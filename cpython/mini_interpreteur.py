import dis
from code_objet import CompilerToCodeObject

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
    def __init__(self, code_obj):
        self.code = code_obj
        self.argcount = code_obj.co_argcount


class Frame():

    def __init__(self, bytecode:Bytecode, locals:dict): #chaque frame à ses propres variables locales, son propre bytecode, et donc son propre stack
        self.btc = bytecode
        self.loc = locals
        self.stack = Stack()
        self.pointeur = 0

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
            elif inst[i] == "PERCENT":
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
            func = Function(code_obj)
            current_frame.stackAdd(func)
        elif inst[0] == "CALL":
            arg_count = inst[1]
            args = []

            call_stack.empiler(current_frame)

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
                new_locals = {}

                #Passe les arguments aux fonctions
                for i, val in enumerate(func.code.co_varnames[:func.argcount]): #slice pour prendre uniquement les arguments de la fonction, et eviter un index error
                    new_locals[val] = args[i]

                current_frame = Frame(func_code, new_locals)

        elif inst[0] == "RETURN_VALUE":
            value = current_frame.stackRem()
            current_frame = call_stack.depiler()
            current_frame.stackAdd(value)
        elif inst[0] == "STORE_NAME":
            current_frame.loc[inst[1]] = current_frame.stackRem()
        elif inst[0] == "LOAD_NAME":
            current_frame.stack.empiler(current_frame.loc[inst[1]])
        elif inst[0] == "POP_TOP":
            current_frame.stackRem()

    if current_frame.stack.taille() > 0:
        res = current_frame.stackRem()
    return res


def coCodeToBytecode(code_object : CompilerToCodeObject):
    """Transforme le code objet en instructions de bytecode executable par ma vm"""
    bytecode = code_object.code.co_code
    varnames = code_object.code.co_varnames
    consts = code_object.code.co_consts
    names = code_object.code.co_names
    btc = Bytecode()
    for i in range(0, len(bytecode)):
        if bytecode[i].op == "LOAD_CONST":
            btc.ajouter_instruction(bytecode[i].op, consts[bytecode[i].arg])
        elif bytecode[i].op == "LOAD_NAME":
            btc.ajouter_instruction(bytecode[i].op, names[bytecode[i].arg])
        elif bytecode[i].op == "STORE_FAST":
            btc.ajouter_instruction(bytecode[i].op, varnames[bytecode[i].arg])
        else :
            btc.ajouter_instruction(bytecode[i].op, bytecode[i].arg)
    return btc


        
