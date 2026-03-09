

from mini_interpreteur import miniVm, coCodeToBytecode
from lexer import lex
from parser import *
from code_objet import CompilerToCodeObject
from AI_miscs.display import dump
from AI_miscs.codeobj_pretty import dump_codeobject


# tests
if __name__ == "__main__":
    with open("SOURCE.py", "r") as f:
        SOURCE = f.readlines()

    # for elm in lex(SOURCE):
    #     print(elm)

    lexed_source = lex(SOURCE)
    parser = Parser(lexed_source)
    ast = parser.parse()

    # print(dump(ast, indent=2))


    code_object = CompilerToCodeObject(ast)

    module_code_object = code_object.compile()

    new_bytecode = coCodeToBytecode(module_code_object)

    result = miniVm(new_bytecode)

    print(result)

    #dump_codeobject(module_code_object)

