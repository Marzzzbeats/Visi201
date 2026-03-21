
# 100% IA G RIEN FAIT SUR CETTE FILE

def dump(node, *, indent: int = 2) -> str:
    """
    Pretty-print a custom AST in a style similar to Python's ast.dump(..., indent=2).
    Assumes nodes are simple objects with __dict__ fields and lists for sequences.
    """

    def is_node(x) -> bool:
        return hasattr(x, "__dict__") and x.__class__.__name__ not in ("TokenStream", "Token")

    def fmt(x, level: int) -> str:
        pad = " " * (indent * level)

        if is_node(x):
            cls = x.__class__.__name__
            fields = list(getattr(x, "__dict__", {}).items())

            if not fields:
                return f"{cls}()"

            parts = []
            for k, v in fields:
                parts.append(f"{k}={fmt(v, level + 1)}")

            if indent <= 0:
                return f"{cls}({', '.join(parts)})"

            inner_pad = " " * (indent * (level + 1))
            return (
                f"{cls}(\n"
                + ",\n".join(f"{inner_pad}{p}" for p in parts)
                + f"\n{pad})"
            )

        if isinstance(x, list):
            if not x:
                return "[]"
            if indent <= 0:
                return "[" + ", ".join(fmt(i, level) for i in x) + "]"
            inner_pad = " " * (indent * (level + 1))
            return (
                "[\n"
                + ",\n".join(f"{inner_pad}{fmt(i, level + 1)}" for i in x)
                + f"\n{pad}]"
            )

        if isinstance(x, str):
            return repr(x)
        return str(x)

    return fmt(node, 0)