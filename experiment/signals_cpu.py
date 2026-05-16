from enum import Enum, auto

class ARLatch(Enum):
    PC = auto()
    TOS = auto()
    CR = auto()

class TOSLatch(Enum):
    INPUT = auto()
    NOS = auto()
    MEM = auto()
    ALU = auto()
    BR = auto()
    CR = auto()
    RS = auto()

class RSLatch(Enum):
    PC = auto()
    TOS = auto()


class NOSLatch(Enum):
    TOS = auto()
    RS = auto()

class MEMSignal(Enum):
    READ_CR = auto()
    READ_TOS = auto()
    WRITE = auto()

class ALUValues(Enum):
    TOS_NOS = auto()
    TOS = auto()

class ALULatch(Enum):
    ADD = auto()
    SUB = auto()
    MUL = auto()
    DIV = auto()
    MOD = auto()
    NOT = auto()
    AND = auto()
    OR = auto()
    NEG = auto()
    INC = auto()

class MemDataLatch(Enum):
    NOS = auto()

class PCLatch(Enum):
    INC = auto()
    CR = auto()
    RS = auto()

class JUMP(Enum):
    JMP = auto()
    JZ = auto()
    JN = auto()
    NEXT = auto()

class IOLatch(Enum):
    IN = auto()
    OUT = auto()

class CheckFlag(Enum):
    Z = auto
    N = auto
    V = auto
    C = auto


class MCAdrLatch(Enum):
    ZERO = auto()
    INC = auto()
    INPUT = auto()

class PROG(Enum):
    HALT = auto()