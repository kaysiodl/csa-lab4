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

class RSLatch(Enum): #из pc и в pc
    PUSH = auto()
    POP = auto()

class DSLatch(Enum):
    PUSH = auto()
    POP = auto()
    PUSH_BR = auto()

class MEMSignal(Enum):
    READ = auto()
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

class BRLatch(Enum):
    TOS = auto()
    NOS = auto()
    MEM = auto()

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

class IOLatch(Enum):
    IN = auto()
    OUT = auto()

class CheckFlag(Enum):
    Z = auto
    N = auto
    V = auto
    C = auto

class Instruction(Enum):
    INC = auto()

class MCAdrLatch(Enum):
    ZERO = auto()
    INC = auto()
    INPUT = auto()

class PROG(Enum):
    HALT = auto()