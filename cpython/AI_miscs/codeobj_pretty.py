
# IA PAS MOI QUI EST FAIT

from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Iterable, Optional, Set


def _is_codeobject(obj: Any) -> bool:
    # Duck-typing: your CodeObject has these attributes.
    return hasattr(obj, "co_name") and hasattr(obj, "co_code") and hasattr(obj, "co_consts")


def _safe_repr(x: Any, max_len: int = 80) -> str:
    try:
        s = repr(x)
    except Exception:
        s = f"<unreprable {type(x).__name__}>"
    if len(s) > max_len:
        s = s[: max_len - 3] + "..."
    return s


def _const_label(c: Any) -> str:
    if _is_codeobject(c):
        name = getattr(c, "co_name", "<code>")
        argc = getattr(c, "co_argcount", "?")
        return f"<CodeObject {name!r} argc={argc}>"
    return _safe_repr(c)


@dataclass
class DumpOptions:
    show_consts: bool = True
    show_names: bool = True
    show_varnames: bool = True
    recurse: bool = True
    max_const_items: int = 200
    max_code_items: int = 10_000


def dump_codeobject(codeobj: Any, *, indent: int = 0, opts: Optional[DumpOptions] = None, _seen: Optional[Set[int]] = None) -> None:
    """
    Pretty-print a CodeObject. Recurses into nested CodeObjects stored in co_consts.
    """
    if opts is None:
        opts = DumpOptions()
    if _seen is None:
        _seen = set()

    pad = " " * indent
    oid = id(codeobj)
    if oid in _seen:
        print(f"{pad}<CodeObject {getattr(codeobj, 'co_name', '?')!r} ... (already shown)>")
        return
    _seen.add(oid)

    co_name = getattr(codeobj, "co_name", "<unknown>")
    co_argcount = getattr(codeobj, "co_argcount", 0)
    co_firstlineno = getattr(codeobj, "co_firstlineno", 1)
    co_stacksize = getattr(codeobj, "co_stacksize", 0)

    print(f"{pad}=== CodeObject {co_name!r} ===")
    print(f"{pad}argcount={co_argcount} firstlineno={co_firstlineno} stacksize={co_stacksize}")

    if opts.show_varnames:
        varnames = getattr(codeobj, "co_varnames", [])
        print(f"{pad}varnames({len(varnames)}): {varnames}")

    if opts.show_names:
        names = getattr(codeobj, "co_names", [])
        print(f"{pad}names({len(names)}): {names}")

    if opts.show_consts:
        consts = getattr(codeobj, "co_consts", [])
        shown = consts[: opts.max_const_items]
        print(f"{pad}consts({len(consts)}):")
        for i, c in enumerate(shown):
            print(f"{pad}  [{i:>3}] {_const_label(c)}")
        if len(consts) > opts.max_const_items:
            print(f"{pad}  ... ({len(consts) - opts.max_const_items} more)")

    # Disassemble co_code
    co_code = getattr(codeobj, "co_code", [])
    print(f"{pad}bytecode({len(co_code)}):")
    if len(co_code) > opts.max_code_items:
        print(f"{pad}  <too many instructions to print: {len(co_code)}>")
    else:
        for ip, instr in enumerate(co_code):
            op = getattr(instr, "op", "?")
            arg = getattr(instr, "arg", None)

            # Nice formatting for const/name indices where possible
            extra = ""
            if op == "LOAD_CONST" and arg is not None:
                consts = getattr(codeobj, "co_consts", [])
                if isinstance(arg, int) and 0 <= arg < len(consts):
                    extra = f" ; const[{arg}]={_const_label(consts[arg])}"
            elif op in ("LOAD_NAME", "STORE_NAME") and arg is not None:
                names = getattr(codeobj, "co_names", [])
                if isinstance(arg, int) and 0 <= arg < len(names):
                    extra = f" ; name[{arg}]={names[arg]!r}"
            elif op in ("JUMP", "JUMP_IF_FALSE") and arg is not None:
                extra = f" ; -> {arg}"

            if arg is None:
                print(f"{pad}  {ip:>4}: {op}{extra}")
            else:
                print(f"{pad}  {ip:>4}: {op:<14} {arg!r}{extra}")

    # Recurse into nested code objects found in consts
    if opts.recurse and opts.show_consts:
        consts = getattr(codeobj, "co_consts", [])
        nested = [c for c in consts if _is_codeobject(c)]
        if nested:
            print(f"{pad}--- nested code objects ({len(nested)}) ---")
            for c in nested:
                print()
                dump_codeobject(c, indent=indent + 2, opts=opts, _seen=_seen)
