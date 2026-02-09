import dis

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
            self.pile.pop()
        return new


class Bytecode():

    def __init__(self):
        self.bytecode = []
        self.pointeur = -1

    def ajouter_instruction(self, name, value=None):
        """Permet d'ajouter une instruction bytecode à la liste d'instruction. Selon l'instruction, la valeur peut être None"""
        self.bytecode.append((name, value))

    def est_vide(self):
        """Verifie si la liste est vide"""
        return len(self.bytecode) == 0
    
    def next(self):
        self.pointeur += 1
        return self.bytecode[self.pointeur]
    
def miniVm(instructions:Bytecode):
    """Fonction qui prend en entrée une liste d'instruction de bytecode et l'execute. Fait l'effet d'une "mini VM Python" ou un interprêteur de Bytecode créé pour des fonctions de base simples"""
    data_stack = Stack()
    values = []
    indConsts = 0
    fctstack = Stack()
    fct = False
    while not instructions.est_vide():
        inst = instructions.next()
        if inst[0] == "LOAD_CONST":
            if not fct:
                data_stack.empiler(inst[1])
            else :
                fctstack.empiler(inst[1])
        elif inst[0] == "STORE_FAST":
            if not fct:
                values.append((inst[1], data_stack.depiler()))
                indConsts += 1
            else : 
                values.append(fctstack.depiler())
                indConsts += 1
        elif inst[0] == "BINARY_ADD":
            addition = data_stack.depiler() + data_stack.depiler()
            data_stack.empiler(addition)
        elif inst[0] == "BINARY_SUBSTRACT":
            b = data_stack.depiler()
            a = data_stack.depiler()
            soustraction = a - b
            data_stack.empiler(soustraction)
        elif inst[0] == "BINARY_MULTIPLY":
            multiplication = data_stack.depiler() * data_stack.depiler()
            data_stack.empiler(multiplication)
        elif inst[0] == "BINARY_TRUE_DIVIDE":
            b = data_stack.depiler()
            a = data_stack.depiler()
            division = a / b
            data_stack.empiler(division)
        




