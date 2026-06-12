from dataclasses import dataclass

from translator.nodes import (
    Const, Str, Name, BinOp, Compare, Var, Set, If, While, Def, Call,
    Print, Read, ReadStr, Len, Array, ARef, ASet,
)

VAR_BASE = 0x1000
STR_BASE = 0x2000


class LintError(Exception):
    pass


@dataclass
class Symbols:
    variables: dict
    var_types: dict
    functions: dict
    strings: dict


def type_of(node, var_types: dict, param: str | None) -> str:
    if isinstance(node, (Str, ReadStr)):
        return "str"
    if isinstance(node, Name):
        if node.name == param:
            return "int"
        return var_types.get(node.name, "int")
    if isinstance(node, If):
        return type_of(node.then, var_types, param)
    if isinstance(node, (Set, Var, Print)):
        return type_of(node.expr if isinstance(node, (Set, Var)) else node.arg, var_types, param)
    return "int"


def lint(ast: list):
    variables = {}
    var_types = {}
    functions = {}
    strings = {}
    var_next = VAR_BASE
    str_next = STR_BASE

    def alloc_var(name, count=1):
        nonlocal var_next
        variables[name] = var_next
        var_next += 4 * count

    def alloc_string(value):
        nonlocal str_next
        if value not in strings:
            strings[value] = str_next
            str_next += 1 + len(value)
        return strings[value]

    def check(node, param):
        if isinstance(node, Const):
            return
        if isinstance(node, Str):
            alloc_string(node.value)
            return
        if isinstance(node, Name):
            if node.name == param or node.name in variables:
                return
            raise LintError(f"Undefined variable: '{node.name}'")
        if isinstance(node, (BinOp, Compare)):
            check(node.left, param)
            check(node.right, param)
            return
        if isinstance(node, If):
            check(node.cond, param)
            check(node.then, param)
            check(node.els, param)
            return
        if isinstance(node, While):
            check(node.cond, param)
            for expr in node.body:
                check(expr, param)
            return
        if isinstance(node, Set):
            if node.name not in variables:
                raise LintError(f"'set' on undefined variable: '{node.name}'")
            check(node.expr, param)
            return
        if isinstance(node, Call):
            if node.name not in functions:
                raise LintError(f"Undefined function: '{node.name}'")
            check(node.arg, param)
            return
        if isinstance(node, (Print, Len)):
            check(node.arg, param)
            return
        if isinstance(node, (Read, ReadStr)):
            return
        if isinstance(node, Array):
            raise LintError("'array' is only valid as the initializer of 'var'")
        if isinstance(node, ARef):
            if node.name not in variables:
                raise LintError(f"Undefined variable: '{node.name}'")
            if var_types.get(node.name) != "array":
                raise LintError(f"'{node.name}' is not an array")
            check(node.idx, param)
            return
        if isinstance(node, ASet):
            if node.name not in variables:
                raise LintError(f"Undefined variable: '{node.name}'")
            if var_types.get(node.name) != "array":
                raise LintError(f"'{node.name}' is not an array")
            check(node.idx, param)
            check(node.val, param)
            return
        if isinstance(node, Var):
            if node.name in variables:
                raise LintError(f"Variable '{node.name}' already declared")
            if node.name in functions:
                raise LintError(f"'{node.name}' already declared as function")
            if isinstance(node.expr, Array):
                alloc_var(node.name, node.expr.size)
                var_types[node.name] = "array"
            else:
                alloc_var(node.name)
                check(node.expr, param)
                var_types[node.name] = type_of(node.expr, var_types, param)
            return
        if isinstance(node, Def):
            raise LintError("'def' is only allowed at top level")
        raise LintError(f"Unexpected node: {node!r}")

    for node in ast:
        if isinstance(node, Def):
            if node.name in functions:
                raise LintError(f"Function '{node.name}' already declared")
            functions[node.name] = node.param

    for node in ast:
        if isinstance(node, Def):
            if node.name in variables:
                raise LintError(f"'{node.name}' already declared as variable")
            for expr in node.body:
                check(expr, node.param)
        else:
            check(node, None)

    return Symbols(variables, var_types, functions, strings)
