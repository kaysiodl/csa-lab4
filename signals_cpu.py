from enum import Enum, auto


class ARLatch(Enum):
    PC = auto()
    TOS = auto()
    DR = auto()


class TOSLatch(Enum):
    INPUT = auto()
    NOS = auto()
    ALU = auto()
    DR = auto()
    RS = auto()


class RSLatch(Enum):
    PC = auto()
    TOS = auto()


class NOSLatch(Enum):
    TOS = auto()
    RS = auto()


class MEMSignal(Enum):
    READ_BYTE = auto()
    READ_WORD = auto()
    WRITE_WORD = auto()


class PCLatch(Enum):
    INC = auto()
    INC4 = auto()
    DR = auto()
    RS = auto()


class IRLatch(Enum):
    MEM = auto()


class DRLatch(Enum):
    MEM = auto()


class JUMP(Enum):
    JMP = auto()
    JZ = auto()
    JN = auto()
    NEXT = auto()


class IOLatch(Enum):
    OUT = auto()


class MCAdrLatch(Enum):
    ZERO = auto()
    INC = auto()
    INPUT = auto()


class PROG(Enum):
    HALT = auto()
