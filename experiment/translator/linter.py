from dataclasses import dataclass

from nodes import (
    Const, Str, Name, BinOp, Compare, Var, Set, If, While, Def, Call,
    Print, Read, ReadStr, Len,
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

    def alloc_var(name):
        nonlocal var_next
        variables[name] = var_next
        var_next += 4

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
        if isinstance(node, Var):
            raise LintError("'var' is only allowed at top level")
        if isinstance(node, Def):
            raise LintError("'def' is only allowed at top level")
        raise LintError(f"Unexpected node: {node!r}")

    for node in ast:
        if isinstance(node, Def):
            if node.name in functions:
                raise LintError(f"Function '{node.name}' already declared")
            functions[node.name] = node.param

    for node in ast:
        if isinstance(node, Var):
            if node.name in variables:
                raise LintError(f"Variable '{node.name}' already declared")
            if node.name in functions:
                raise LintError(f"'{node.name}' already declared as function")
            alloc_var(node.name)
            check(node.expr, None)
            var_types[node.name] = type_of(node.expr, var_types, None)
        elif isinstance(node, Def):
            if node.name in variables:
                raise LintError(f"'{node.name}' already declared as variable")
            for expr in node.body:
                check(expr, node.param)
        else:
            check(node, None)

    return Symbols(variables, var_types, functions, strings)


if __name__ == "__main__":
    from parser import tokenize, parse

    source = """
    (var x 5)
    (var y 10)
    (def factorial (n)
        (if (= n 0)
            1
            (* n (call factorial (- n 1)))))
    (print (call factorial x))
    (print "hello")
    (var s "world")
    (print s)
    """

    ast = parse(tokenize(source))
    sym = lint(ast)
    print("variables:", {k: hex(v) for k, v in sym.variables.items()})
    print("var_types:", sym.var_types)
    print("functions:", sym.functions)
    print("strings:", {k: hex(v) for k, v in sym.strings.items()})
