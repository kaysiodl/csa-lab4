from alu import ALU_OP
from isa import Opcode
from signals_cpu import *


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


microcode = [
    # FETCH: 0, читаем байт опкода
    [ARLatch.PC, MEMSignal.READ_BYTE, IRLatch.MEM, PCLatch.INC, MCAdrLatch.INPUT],

    # PUSHC: 1, читаем 4-байтный операнд, кладём его на стек
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [NOSLatch.TOS, TOSLatch.DR, MCAdrLatch.ZERO],

    # PUSH: 3, читаем адрес, потом читаем слово по адресу
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [ARLatch.DR, MEMSignal.READ_WORD, DRLatch.MEM, MCAdrLatch.INC],
    [NOSLatch.TOS, TOSLatch.DR, MCAdrLatch.ZERO],

    # POP: 6, читаем адрес, пишем TOS по адресу
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [ARLatch.DR, MEMSignal.WRITE_WORD, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.ZERO],

    # ADD: 9
    [ALU_OP.ADD, TOSLatch.ALU, MCAdrLatch.ZERO],
    # SUB: 10
    [ALU_OP.SUB, TOSLatch.ALU, MCAdrLatch.ZERO],
    # MUL: 11
    [ALU_OP.MUL, TOSLatch.ALU, MCAdrLatch.ZERO],
    # DIV: 12
    [ALU_OP.DIV, TOSLatch.ALU, MCAdrLatch.ZERO],
    # MOD: 13
    [ALU_OP.MOD, TOSLatch.ALU, MCAdrLatch.ZERO],
    # AND: 14
    [ALU_OP.AND, TOSLatch.ALU, MCAdrLatch.ZERO],
    # OR: 15
    [ALU_OP.OR, TOSLatch.ALU, MCAdrLatch.ZERO],
    # NOT: 16
    [ALU_OP.NOT, TOSLatch.ALU, MCAdrLatch.ZERO],
    # NEG: 17
    [ALU_OP.NEG, TOSLatch.ALU, MCAdrLatch.ZERO],
    # DUP: 18
    [NOSLatch.TOS, MCAdrLatch.ZERO],
    # DROP: 19
    [TOSLatch.NOS, MCAdrLatch.ZERO],
    # CMP: 20
    [ALU_OP.CMP, MCAdrLatch.ZERO],

    # JMP: 21
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.JMP, MCAdrLatch.ZERO],

    # JZ: 23
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.JZ, MCAdrLatch.ZERO],

    # JN: 25
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.JN, MCAdrLatch.ZERO],

    # IN: 27
    [NOSLatch.TOS, TOSLatch.INPUT, MCAdrLatch.ZERO],

    # OUT: 28
    [IOLatch.OUT, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.ZERO],

    # HALT: 30
    [PROG.HALT],

    # CALL: 31
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [RSLatch.PC, MCAdrLatch.INC],
    [JUMP.JMP, MCAdrLatch.ZERO],

    # RET: 34
    [PCLatch.RS, MCAdrLatch.ZERO],

    # NEXT: 35
    [ARLatch.PC, MEMSignal.READ_WORD, DRLatch.MEM, PCLatch.INC4, MCAdrLatch.INC],
    [JUMP.NEXT, MCAdrLatch.ZERO],

    # TORS: 37
    [RSLatch.TOS, TOSLatch.NOS, MCAdrLatch.ZERO],
    # FROMRS: 38
    [NOSLatch.TOS, TOSLatch.RS, MCAdrLatch.ZERO],

    # SWAP: 39
    [RSLatch.TOS, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.INC],
    [NOSLatch.RS,  MCAdrLatch.ZERO],

    # LOAD: 42
    [ARLatch.TOS, MEMSignal.READ_WORD, DRLatch.MEM, TOSLatch.DR, MCAdrLatch.ZERO],

    # STORE: 43
    [ARLatch.TOS, TOSLatch.NOS, MCAdrLatch.INC],
    [MEMSignal.WRITE_WORD, MCAdrLatch.ZERO],
]

microcode = [encode_mc(step) for step in microcode]