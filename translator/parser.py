from dataclasses import dataclass
from enum import Enum, auto

from translator.nodes import (
    AddC,
    ARef,
    Array,
    ASet,
    BinOp,
    Call,
    Compare,
    Const,
    Def,
    If,
    Len,
    Name,
    Print,
    Read,
    ReadStr,
    Set,
    Str,
    Var,
    While,
)


class TokenType(Enum):
    LEFT = auto()
    RIGHT = auto()
    NUMBER = auto()
    STRING = auto()
    SYMBOL = auto()


@dataclass
class Token:
    type: TokenType
    value: object
    line: int


OPERATORS = {"+", "-", "*", "/", "%"}
COMPARISONS = {">", "<", "=", "!="}


def tokenize(source: str):
    tokens = []
    i = 0
    line = 1
    while i < len(source):
        char = source[i]
        if char == '\n':
            line += 1
            i += 1
        elif char in ' \t\r':
            i += 1
        elif char == ';':
            while i < len(source) and source[i] != '\n':
                i += 1
        elif char == '(':
            tokens.append(Token(TokenType.LEFT, '(', line))
            i += 1
        elif char == ')':
            tokens.append(Token(TokenType.RIGHT, ')', line))
            i += 1
        elif char == '"':
            j = i + 1
            while j < len(source) and source[j] != '"':
                if source[j] == '\n':
                    line += 1
                j += 1
            tokens.append(Token(TokenType.STRING, source[i + 1:j], line))
            i = j + 1
        else:
            j = i
            while j < len(source) and source[j] not in ' \t\r\n()"':
                j += 1
            atom = source[i:j]
            try:
                tokens.append(Token(TokenType.NUMBER, int(atom), line))
            except ValueError:
                tokens.append(Token(TokenType.SYMBOL, atom, line))
            i = j
    return tokens


def _require(args, n, name, line):
    if len(args) != n:
        raise SyntaxError(f"'{name}' expects {n} argument(s) at line {line}, got {len(args)}")


def _require_min(args, n, name, line):
    if len(args) < n:
        raise SyntaxError(f"'{name}' expects at least {n} argument(s) at line {line}, got {len(args)}")


def _as_name(node, ctx, line):
    if isinstance(node, Name):
        return node.name
    raise SyntaxError(f"{ctx} expects an identifier at line {line}")


def _build(head, args, line):
    if head in OPERATORS:
        _require(args, 2, head, line)
        return BinOp(head, args[0], args[1])
    if head in COMPARISONS:
        _require(args, 2, head, line)
        return Compare(head, args[0], args[1])
    if head == "var":
        _require(args, 2, "var", line)
        return Var(_as_name(args[0], "'var'", line), args[1])
    if head == "set":
        _require(args, 2, "set", line)
        return Set(_as_name(args[0], "'set'", line), args[1])
    if head == "if":
        _require(args, 3, "if", line)
        return If(args[0], args[1], args[2])
    if head == "while":
        _require_min(args, 2, "while", line)
        return While(args[0], args[1:])
    if head == "call":
        _require(args, 2, "call", line)
        return Call(_as_name(args[0], "'call'", line), args[1])
    if head == "print":
        _require(args, 1, "print", line)
        return Print(args[0])
    if head == "read":
        _require(args, 0, "read", line)
        return Read()
    if head == "read_str":
        _require(args, 0, "read_str", line)
        return ReadStr()
    if head == "len":
        _require(args, 1, "len", line)
        return Len(args[0])
    if head == "addc":
        _require(args, 2, "addc", line)
        return AddC(args[0], args[1])
    if head == "array":
        _require(args, 1, "array", line)
        if not isinstance(args[0], Const):
            raise SyntaxError(f"'array' size must be a constant at line {line}")
        return Array(args[0].value)
    if head == "aref":
        _require(args, 2, "aref", line)
        return ARef(_as_name(args[0], "'aref'", line), args[1])
    if head == "aset":
        _require(args, 3, "aset", line)
        return ASet(_as_name(args[0], "'aset'", line), args[1], args[2])
    raise SyntaxError(f"Unknown form '{head}' at line {line}")


def parse(tokens: list[Token]):
    pos = 0

    def at_end():
        return pos >= len(tokens)

    def parse_expr():
        nonlocal pos
        token = tokens[pos]
        if token.type == TokenType.LEFT:
            return parse_form()
        if token.type == TokenType.RIGHT:
            raise SyntaxError(f"Unexpected ')' at line {token.line}")
        pos += 1
        if token.type == TokenType.NUMBER:
            return Const(token.value)
        if token.type == TokenType.STRING:
            return Str(token.value)
        return Name(token.value)

    def expect_symbol(line):
        nonlocal pos
        if at_end() or tokens[pos].type != TokenType.SYMBOL:
            raise SyntaxError(f"Expected identifier at line {line}")
        value = tokens[pos].value
        pos += 1
        return value

    def parse_def(line):
        nonlocal pos
        name = expect_symbol(line)
        if at_end() or tokens[pos].type != TokenType.LEFT:
            raise SyntaxError(f"'def' expects a parameter list at line {line}")
        pos += 1
        params = []
        while not at_end() and tokens[pos].type != TokenType.RIGHT:
            params.append(expect_symbol(line))
        if at_end():
            raise SyntaxError(f"Unclosed parameter list at line {line}")
        pos += 1
        body = []
        while not at_end() and tokens[pos].type != TokenType.RIGHT:
            body.append(parse_expr())
        if at_end():
            raise SyntaxError(f"Unclosed '(' at line {line}")
        pos += 1
        if len(params) != 1:
            raise SyntaxError(f"Function '{name}' must have exactly 1 parameter at line {line}")
        if len(body) < 1:
            raise SyntaxError(f"Function '{name}' has an empty body at line {line}")
        return Def(name, params[0], body)

    def parse_form():
        nonlocal pos
        line = tokens[pos].line
        pos += 1
        if at_end():
            raise SyntaxError(f"Unclosed '(' at line {line}")
        if tokens[pos].type != TokenType.SYMBOL:
            raise SyntaxError(f"Expected a form name at line {line}")
        head = tokens[pos].value
        pos += 1
        if head == "def":
            return parse_def(line)
        args = []
        while not at_end() and tokens[pos].type != TokenType.RIGHT:
            args.append(parse_expr())
        if at_end():
            raise SyntaxError(f"Unclosed '(' at line {line}")
        pos += 1
        return _build(head, args, line)

    results = []
    while not at_end():
        results.append(parse_expr())
    return results

