from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

# =========================
# OPCODES (toy set)
# =========================
# Stack effects are shown like: (before -> after)

# LOAD_CONST idx        ([] -> [const])
# LOAD_NAME name        ([] -> [value])
# STORE_NAME name       ([value] -> [])
# POP_TOP               ([x] -> [])
# BINARY_ADD            ([a,b] -> [a+b])
# BINARY_SUB            ([a,b] -> [a-b])
# COMPARE_GT            ([a,b] -> [a>b])
# JUMP target           ([] -> [])        # ip = target
# JUMP_IF_FALSE target  ([cond] -> [])    # if not cond: ip = target
# CALL n                ([func, arg1..argn] -> [result])
# RETURN                ([value] -> stop) # returns value


@dataclass(frozen=True)
class Instr:
    op: str
    arg: Any = None


class VMError(Exception):
    pass


class MiniVM:
    def __init__(self, consts: list[Any], builtins: dict[str, Any] | None = None):
        self.consts = consts
        self.builtins = builtins or {}

    def run(self, program: list[Instr], env: dict[str, Any] | None = None) -> Any:
        env = {} if env is None else env
        stack: list[Any] = []
        ip = 0

        while ip < len(program):
            ins = program[ip]
            op, arg = ins.op, ins.arg

            if op == "LOAD_CONST":
                stack.append(self.consts[arg])
                ip += 1

            elif op == "LOAD_NAME":
                if arg in env:
                    stack.append(env[arg])
                elif arg in self.builtins:
                    stack.append(self.builtins[arg])
                else:
                    raise VMError(f"NameError: {arg!r} is not defined")
                ip += 1

            elif op == "STORE_NAME":
                if not stack:
                    raise VMError("Stack underflow on STORE_NAME")
                env[arg] = stack.pop()
                ip += 1

            elif op == "POP_TOP":
                if not stack:
                    raise VMError("Stack underflow on POP_TOP")
                stack.pop()
                ip += 1

            elif op == "BINARY_ADD":
                b = stack.pop(); a = stack.pop()
                stack.append(a + b)
                ip += 1

            elif op == "BINARY_SUB":
                b = stack.pop(); a = stack.pop()
                stack.append(a - b)
                ip += 1

            elif op == "COMPARE_GT":
                b = stack.pop(); a = stack.pop()
                stack.append(a > b)
                ip += 1

            elif op == "JUMP":
                ip = int(arg)

            elif op == "JUMP_IF_FALSE":
                cond = stack.pop()
                ip = int(arg) if not cond else ip + 1

            elif op == "CALL":
                n = int(arg)
                # stack: ... func, arg1, arg2, ... argn
                # so we pop args in reverse, then func
                if len(stack) < n + 1:
                    raise VMError("Stack underflow on CALL")
                args = [stack.pop() for _ in range(n)][::-1]
                func = stack.pop()
                if not callable(func):
                    raise VMError(f"TypeError: object {func!r} is not callable")
                stack.append(func(*args))
                ip += 1

            elif op == "RETURN":
                return stack.pop() if stack else None

            else:
                raise VMError(f"Unknown opcode: {op!r}")

        # If program falls off the end, return top-of-stack or None
        return stack[-1] if stack else None


# =========================
# EXAMPLES
# =========================

def example_add_and_store():
    # Python-ish:
    # x = 10
    # y = x + 1
    # return y
    consts = [10, 1]
    prog = [
        Instr("LOAD_CONST", 0),
        Instr("STORE_NAME", "x"),
        Instr("LOAD_NAME", "x"),
        Instr("LOAD_CONST", 1),
        Instr("BINARY_ADD"),
        Instr("STORE_NAME", "y"),
        Instr("LOAD_NAME", "y"),
        Instr("RETURN"),
    ]
    vm = MiniVM(consts)
    return vm.run(prog)

def example_if():
    # Python-ish:
    # x = 5
    # if x > 0: y = 1
    # else:     y = -1
    # return y
    consts = [5, 0, 1, -1]
    # labels (targets are instruction indices):
    # 0: x=5
    # 2..5: compute x>0
    # 6: JUMP_IF_FALSE else_block
    # 7..8: then y=1
    # 9: JUMP end
    # 10..11: else y=-1
    # 12..13: return y
    prog = [
        Instr("LOAD_CONST", 0),          # 0
        Instr("STORE_NAME", "x"),        # 1
        Instr("LOAD_NAME", "x"),         # 2
        Instr("LOAD_CONST", 1),          # 3 (0)
        Instr("COMPARE_GT"),             # 4 (x > 0)
        Instr("JUMP_IF_FALSE", 10),      # 5 -> else at 10
        Instr("LOAD_CONST", 2),          # 6 (1)
        Instr("STORE_NAME", "y"),        # 7
        Instr("JUMP", 12),               # 8 -> end at 12
        # else:
        Instr("LOAD_CONST", 3),          # 9 (-1)   (actually index 9 is unreachable due to jump; keep mapping clean)
        Instr("STORE_NAME", "y"),        # 10
        # end:
        Instr("LOAD_NAME", "y"),         # 11
        Instr("RETURN"),                 # 12
    ]
    # Fix indices to match comments precisely (clean version):
    prog = [
        Instr("LOAD_CONST", 0),          # 0
        Instr("STORE_NAME", "x"),        # 1
        Instr("LOAD_NAME", "x"),         # 2
        Instr("LOAD_CONST", 1),          # 3
        Instr("COMPARE_GT"),             # 4
        Instr("JUMP_IF_FALSE", 9),       # 5
        Instr("LOAD_CONST", 2),          # 6
        Instr("STORE_NAME", "y"),        # 7
        Instr("JUMP", 11),               # 8
        Instr("LOAD_CONST", 3),          # 9  else:
        Instr("STORE_NAME", "y"),        # 10
        Instr("LOAD_NAME", "y"),         # 11 end:
        Instr("RETURN"),                 # 12
    ]
    vm = MiniVM(consts)
    return vm.run(prog)

def example_call_builtin():
    # Python-ish:
    # return add(2, 3)
    consts = [2, 3]
    builtins = {"add": lambda a, b: a + b}
    prog = [
        Instr("LOAD_NAME", "add"),
        Instr("LOAD_CONST", 0),
        Instr("LOAD_CONST", 1),
        Instr("CALL", 2),
        Instr("RETURN"),
    ]
    vm = MiniVM(consts, builtins=builtins)
    return vm.run(prog)

if __name__ == "__main__":
    print("add_and_store:", example_add_and_store())
    print("if_example   :", example_if())
    print("call_builtin :", example_call_builtin())
