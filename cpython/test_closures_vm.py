import dis
from code_objet import CompilerToCodeObject, CodeObject, Instr
import builtins  #Sert a importer les fonctions de base de python pour la gestion des print
from mini_interpreteur import *

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