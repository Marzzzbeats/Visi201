
####################################
##        FICHIER PRINCIPAL       ##
####################################

## Ce fichier permet de faire le lien entre tous les fichiers .py 
## qui représentent chaque étape du lexer au runtime



from cpython.lexer import lex
from cpython.parser import *
from cpython.scope import *
from cpython.code_objet import *
from cpython.mini_interpreteur import miniVm, coCodeToBytecode
from cpython.AI_miscs.display import dump
from cpython.AI_miscs.codeobj_pretty import dump_codeobject



# Executé seulement si ce fichier est run
if __name__ == "__main__":
    
    # On récupere le contenu du fichier .py source voulu
    ## AIDE
    # src1 -> affectation et addition
    # src2 -> fonctions
    # src3 -> closures
    # src4 -> boucle while
    # src5 -> condition if
    # src6 -> listes et subscript
    # src7 -> try / except
    # src8 -> classe
    
    src: int  = 2
    with open(f"sources/src{src}.py", "r") as f:
        SOURCE = f.readlines()

    
    # Etape 1 : Lexer
    lexed_source = lex(SOURCE)
    
    # Etape 2 : Le parser/AST
    parser = Parser(lexed_source)
    ast = parser.parse()

    # Etape 3 : Analise du scope
    analyzer = ScopeAnalyzer()
    scope_map = analyzer.analyze(ast)

    # Etape 4 : Compilation de notre AST en code objet
    code_object = CompilerToCodeObject(ast, scope_map)
    module_code_object = code_object.compile()


    # Paramattre de debug/affichage en console
    params_debug = {
        "lexer" : False,
        "AST" : False,
        "ScopeMap" : False,
        "CodeObject" : True,
        "Runtime" : True
    }


    # Gestion de l'affichage en console
    for key, value in params_debug.items():
        if (key == "lexer") and value:
            for elm in lex(SOURCE):
                print(elm)
        elif (key == "AST") and value:  
            print(dump(ast, indent=2))
        elif (key == "ScopeMap") and value:
            for key, value in scope_map.items():
                print(f"========{key.name}==========\n{dump_scope(value)}\n")
            print()
        elif (key == "CodeObject") and value:
            dump_codeobject(module_code_object)
        elif (key == "Runtime") and value:
            print("\n================ CONSOLE ===================")
            miniVm(coCodeToBytecode(module_code_object))


