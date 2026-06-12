from dataclasses import dataclass


class Node:
    pass


@dataclass
class Const(Node):
    value: int


@dataclass
class Str(Node):
    value: str


@dataclass
class Name(Node):
    name: str


@dataclass
class BinOp(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Compare(Node):
    op: str
    left: Node
    right: Node


@dataclass
class Var(Node):
    name: str
    expr: Node


@dataclass
class Set(Node):
    name: str
    expr: Node


@dataclass
class If(Node):
    cond: Node
    then: Node
    els: Node


@dataclass
class While(Node):
    cond: Node
    body: list[Node]


@dataclass
class Def(Node):
    name: str
    param: str
    body: list[Node]


@dataclass
class Call(Node):
    name: str
    arg: Node


@dataclass
class Print(Node):
    arg: Node


@dataclass
class Read(Node):
    pass


@dataclass
class ReadStr(Node):
    pass


@dataclass
class Len(Node):
    arg: Node


@dataclass
class Array(Node):
    size: int


@dataclass
class ARef(Node):
    name: str
    idx: Node


@dataclass
class ASet(Node):
    name: str
    idx: Node
    val: Node
