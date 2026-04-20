

from cpython.mini_interpreteur import miniVm, coCodeToBytecode
from cpython.lexer import lex
from cpython.parser import *
from cpython.code_objet import CompilerToCodeObject
from cpython.AI_miscs.display import dump
from cpython.AI_miscs.codeobj_pretty import dump_codeobject


# tests
if __name__ == "__main__":
    with open("SOURCE.py", "r") as f:
        SOURCE = f.readlines()

    # for elm in lex(SOURCE):
    #     print(elm)

    lexed_source = lex(SOURCE) #lexer
    parser = Parser(lexed_source) #parser
    ast = parser.parse() #Création de l'arbre 

    # print(dump(ast, indent=2))


    code_object = CompilerToCodeObject(ast) 

    module_code_object = code_object.compile() #transformation en code objet

    new_bytecode = coCodeToBytecode(module_code_object) #Création du bytecode

    result = miniVm(new_bytecode) #Execution du bytecode par la VM

    #dump_codeobject(module_code_object)

