

# 100% IA G RIEN FAIT SUR CETTE FILE

from __future__ import annotations

import ast
import dis
import inspect
import sys
import textwrap
import tokenize
from types import CodeType, FrameType
from typing import Any


# =========================
# 1) SOURCE (le "fichier")
# =========================

SOURCE = textwrap.dedent(
    """
    def f(x):
        if x%2==0:
            return x
        else:
            return x+1

    y = f(10)
    """
).lstrip()


# =========================
# 2) TOKENS (lexer)
# =========================

def show_tokens(src: str) -> None:
    print("\n" + "=" * 80)
    print("TOKENS (tokenize)")
    print("=" * 80)

    # tokenize attend des bytes via readline
    src_bytes = src.encode("utf-8")
    tokgen = tokenize.tokenize(iter([src_bytes]).__iter__().__next__)

    for tok in tokgen:
        # Ignore l'encodage et les fin de fichier trop verbeuses
        if tok.type in (tokenize.ENCODING, tokenize.ENDMARKER):
            continue
        # tok: TokenInfo(type, string, start, end, line)
        print(
            f"{tokenize.tok_name[tok.type]:<12} "
            f"{tok.string!r:<12} "
            f"start={tok.start} end={tok.end}"
        )


# =========================
# 3) AST (parser -> arbre)
# =========================

def show_ast(src: str) -> ast.AST:
    print("\n" + "=" * 80)
    print("AST (ast.parse + ast.dump)")
    print("=" * 80)

    tree = ast.parse(src, mode="exec")
    print(ast.dump(tree, indent=2))
    return tree


# =========================
# 4) COMPILATION -> CODE OBJECT(S)
# =========================

def describe_code_object(co: CodeType, indent: str = "") -> None:
    print(f"{indent}Code object: {co.co_name!r}")
    print(f"{indent}  co_filename   : {co.co_filename!r}")
    print(f"{indent}  co_firstlineno: {co.co_firstlineno}")
    print(f"{indent}  co_argcount   : {co.co_argcount}")
    print(f"{indent}  co_varnames   : {co.co_varnames}")
    print(f"{indent}  co_names      : {co.co_names}")
    print(f"{indent}  co_consts     : {co.co_consts}")
    print(f"{indent}  co_freevars   : {co.co_freevars}")
    print(f"{indent}  co_cellvars   : {co.co_cellvars}")

    print(f"{indent}  BYTECODE (dis):")
    # dis.dis accepte CodeType
    dis.dis(co)

    # Repère d'éventuels code objects imbriqués dans co_consts
    nested = [c for c in co.co_consts if isinstance(c, CodeType)]
    if nested:
        print(f"\n{indent}  Nested code objects found in co_consts:")
        for nco in nested:
            print()
            describe_code_object(nco, indent=indent + "    ")


def compile_to_code_objects(src: str) -> CodeType:
    print("\n" + "=" * 80)
    print("COMPILATION (compile -> code object module + nested code objects)")
    print("=" * 80)

    module_code = compile(src, filename="<demo>", mode="exec")
    describe_code_object(module_code)
    return module_code


# =========================
# 5) EXECUTION + FRAMES (sys.settrace)
# =========================

def tracer(frame: FrameType, event: str, arg: Any):
    """
    Traceur minimal :
    - 'call' : entrée dans une fonction
    - 'line' : exécution d'une ligne
    - 'return' : retour d'une fonction
    """
    # Filtrage : on ne veut tracer que notre "<demo>" (code compilé ci-dessus)
    co = frame.f_code
    if co.co_filename != "<demo>":
        return tracer

    if event == "call":
        print("\n[CALL ]", co.co_name, "line", frame.f_lineno)
        print("        locals:", dict(frame.f_locals))
    elif event == "line":
        print("[LINE ]", co.co_name, "line", frame.f_lineno, "locals:", dict(frame.f_locals))
    elif event == "return":
        print("[RET  ]", co.co_name, "line", frame.f_lineno, "->", arg, "locals:", dict(frame.f_locals))

    return tracer


def run_with_trace(module_code: CodeType) -> None:
    print("\n" + "=" * 80)
    print("EXECUTION (VM runs bytecode) + FRAMES (trace)")
    print("=" * 80)

    # Namespace d'exécution (globals du module)
    ns: dict[str, Any] = {}

    sys.settrace(tracer)
    try:
        exec(module_code, ns, ns)
    finally:
        sys.settrace(None)

    print("\nFinal module globals (ns) keys:", sorted(k for k in ns.keys() if not k.startswith("__")))
    print("y =", ns.get("y"))


# =========================
# MAIN
# =========================

def main() -> None:
    print("=" * 80)
    print("SOURCE")
    print("=" * 80)
    print(SOURCE)

    show_tokens(SOURCE)
    show_ast(SOURCE)
    module_code = compile_to_code_objects(SOURCE)
    run_with_trace(module_code)


if __name__ == "__main__":
    main()
