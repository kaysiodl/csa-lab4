from alu import ALU_OP
from isa import Opcode
from signals_cpu import (
    JUMP,
    PROG,
    ARLatch,
    DRLatch,
    IOLatch,
    IRLatch,
    MCAdrLatch,
    MEMSignal,
    NOSLatch,
    PCLatch,
    RSLatch,
    TOSLatch,
)


def op2microcode(op: Opcode) -> int:
    return {
        Opcode.PUSHC:  1,
        Opcode.PUSH:   3,
        Opcode.POP:    6,
        Opcode.ADD:    9,
        Opcode.SUB:    10,
        Opcode.MUL:    11,
        Opcode.DIV:    12,
        Opcode.MOD:    13,
        Opcode.AND:    14,
        Opcode.OR:     15,
        Opcode.NOT:    16,
        Opcode.NEG:    17,
        Opcode.DUP:    18,
        Opcode.DROP:   19,
        Opcode.CMP:    20,
        Opcode.JMP:    21,
        Opcode.JZ:     23,
        Opcode.JN:     25,
        Opcode.IN:     27,
        Opcode.OUT:    28,
        Opcode.HALT:   30,
        Opcode.CALL:   31,
        Opcode.RET:    34,
        Opcode.NEXT:   35,
        Opcode.TORS:   37,
        Opcode.FROMRS: 38,
        Opcode.SWAP:   39,
        Opcode.LOAD:   42,
        Opcode.STORE:  43,
        Opcode.ADC:    45,
    }[op]


def encode_mc(signals: list) -> int:
    SHIFTS = {
        JUMP:       0,
        PCLatch:    3,
        IOLatch:    6,
        TOSLatch:   7,
        ALU_OP:     10,
        NOSLatch:   14,
        DRLatch:    16,
        IRLatch:    17,
        MEMSignal:  18,
        ARLatch:    20,
        RSLatch:    22,
        PROG:       24,
        MCAdrLatch: 25,
    }
    control_word = 0
    for s in signals:
        if type(s) in SHIFTS:
            control_word |= (s.value << SHIFTS[type(s)])
    return control_word


def decode_mc(mc: int) -> list:
    FIELDS = [
        (ARLatch, 20, 0b11),
        (MEMSignal, 18, 0b11),
        (IRLatch, 17, 0b1),
        (DRLatch, 16, 0b1),
        (ALU_OP, 10, 0b1111),
        (RSLatch, 22, 0b11),
        (NOSLatch, 14, 0b11),
        (TOSLatch, 7, 0b111),
        (IOLatch, 6, 0b1),
        (PCLatch, 3, 0b111),
        (JUMP, 0, 0b111),
        (PROG, 24, 0b1),
        (MCAdrLatch, 25, 0b11),
    ]
    result = []
    for cls, shift, mask in FIELDS:
        val = (mc >> shift) & mask
        if val != 0:
            result.append(cls(val))
    return result


FETCH_TAIL = [ARLatch.PC, MEMSignal.READ_BYTE, IRLatch.MEM, PCLatch.INC, MCAdrLatch.INPUT]


_steps: list[list] = [
    # FETCH: 0, читаем байт опкода (старт + после переходов/LOAD/STORE)
    [ARLatch.PC, MEMSignal.READ_BYTE, IRLatch.MEM, PCLatch.INC, MCAdrLatch.INPUT],

    # PUSHC: 1, читаем 4-байтный операнд, кладём его на стек
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [NOSLatch.TOS, TOSLatch.DR, *FETCH_TAIL],

    # PUSH: 3, читаем адрес, потом читаем слово по адресу
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [ARLatch.DR, MEMSignal.READ_WORD, DRLatch.MEM, MCAdrLatch.INC],
    [NOSLatch.TOS, TOSLatch.DR, *FETCH_TAIL],

    # POP: 6, читаем адрес, пишем TOS по адресу
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [ARLatch.DR, MEMSignal.WRITE_WORD, MCAdrLatch.INC],
    [TOSLatch.NOS, *FETCH_TAIL],

    # ADD: 9
    [ALU_OP.ADD, TOSLatch.ALU, *FETCH_TAIL],
    # SUB: 10
    [ALU_OP.SUB, TOSLatch.ALU, *FETCH_TAIL],
    # MUL: 11
    [ALU_OP.MUL, TOSLatch.ALU, *FETCH_TAIL],
    # DIV: 12
    [ALU_OP.DIV, TOSLatch.ALU, *FETCH_TAIL],
    # MOD: 13
    [ALU_OP.MOD, TOSLatch.ALU, *FETCH_TAIL],
    # AND: 14
    [ALU_OP.AND, TOSLatch.ALU, *FETCH_TAIL],
    # OR: 15
    [ALU_OP.OR, TOSLatch.ALU, *FETCH_TAIL],
    # NOT: 16
    [ALU_OP.NOT, TOSLatch.ALU, *FETCH_TAIL],
    # NEG: 17
    [ALU_OP.NEG, TOSLatch.ALU, *FETCH_TAIL],
    # DUP: 18
    [NOSLatch.TOS, *FETCH_TAIL],
    # DROP: 19
    [TOSLatch.NOS, *FETCH_TAIL],
    # CMP: 20
    [ALU_OP.CMP, *FETCH_TAIL],

    # JMP: 21 (без префетча — меняем PC)
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.JMP, MCAdrLatch.ZERO],

    # JZ: 23
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.JZ, MCAdrLatch.ZERO],

    # JN: 25
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.JN, MCAdrLatch.ZERO],

    # IN: 27
    [NOSLatch.TOS, TOSLatch.INPUT, *FETCH_TAIL],

    # OUT: 28
    [IOLatch.OUT, MCAdrLatch.INC],
    [TOSLatch.NOS, *FETCH_TAIL],

    # HALT: 30
    [PROG.HALT],

    # CALL: 31 (без префетча — меняем PC)
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [RSLatch.PC, MCAdrLatch.INC],
    [JUMP.JMP, MCAdrLatch.ZERO],

    # RET: 34 (без префетча — меняем PC)
    [PCLatch.RS, MCAdrLatch.ZERO],

    # NEXT: 35 (без префетча — может менять PC)
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.NEXT, MCAdrLatch.ZERO],

    # TORS: 37
    [RSLatch.TOS, TOSLatch.NOS, *FETCH_TAIL],
    # FROMRS: 38
    [NOSLatch.TOS, TOSLatch.RS, *FETCH_TAIL],

    # SWAP: 39
    [RSLatch.TOS, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.INC],
    [NOSLatch.RS, *FETCH_TAIL],

    # LOAD: 42 (без префетча — лезет в память)
    [ARLatch.TOS, MEMSignal.READ_WORD, DRLatch.MEM, TOSLatch.DR, MCAdrLatch.ZERO],

    # STORE: 43 (без префетча — лезет в память)
    [ARLatch.TOS, TOSLatch.NOS, MCAdrLatch.INC],
    [MEMSignal.WRITE_WORD, MCAdrLatch.ZERO],

    # ADC: 45, NOS + TOS + C
    [ALU_OP.ADC, TOSLatch.ALU, *FETCH_TAIL],
]

microcode: list[int] = [encode_mc(step) for step in _steps]
