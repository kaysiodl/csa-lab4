from isa import Opcode
from signals_cpu import *


def op2microcode(op: Opcode) -> int:
    return {
        Opcode.PUSHC: 1,

        Opcode.PUSH: 2,
        Opcode.POP: 4,

        Opcode.ADD: 6,
        Opcode.SUB: 7,
        Opcode.MUL: 8,
        Opcode.DIV: 9,
        Opcode.MOD: 10,

        Opcode.AND: 11,
        Opcode.OR: 12,
        Opcode.NOT: 13,
        Opcode.NEG: 14,

        Opcode.DUP: 15,
        Opcode.DROP: 16,

        Opcode.CMP: 17,

        Opcode.JMP: 18,
        Opcode.JZ: 19,
        Opcode.JN: 20,

        Opcode.IN: 21,
        Opcode.OUT: 22,

        Opcode.HALT: 24,

        Opcode.CALL: 25,
        Opcode.RET: 27,
        Opcode.NEXT: 28,
        Opcode.TORS: 29,
        Opcode.FROMRS: 30,
        Opcode.SWAP: 31,
    }[op]


def encode_mc(signals: list) -> int:
    SHIFTS = {
        RSLatch: 23,
        ARLatch: 21,
        MEMSignal: 19,
        NOSLatch: 17,
        ALULatch: 13,
        TOSLatch: 10,
        IOLatch: 8,
        PCLatch: 6,
        JUMP: 3,
        MCAdrLatch: 1,
        PROG: 0
    }

    control_word = 0
    for s in signals:
        signal_type = type(s)
        if signal_type in SHIFTS:
            control_word |= (s.value << SHIFTS[signal_type])

    return control_word


def decode_mc(mc: int) -> list:
    FIELNOS = [
        (RSLatch, 23, 0b11),
        (ARLatch, 21, 0b11),
        (MEMSignal, 19, 0b11),
        (NOSLatch, 17, 0b11),
        (ALULatch, 13, 0b1111),
        (TOSLatch, 10, 0b111),
        (IOLatch, 8, 0b11),
        (PCLatch, 6, 0b11),
        (JUMP, 3, 0b111),
        (MCAdrLatch, 1, 0b11),
        (PROG, 0, 0b1),
    ]
    result = []
    for cls, shift, mask in FIELNOS:
        val = (mc >> shift) & mask
        if val != 0:
            result.append(cls(val))

    return result


microcode = [
    # FETCH: 0
    [ARLatch.PC, MEMSignal.READ_CR, PCLatch.INC, MCAdrLatch.INPUT],

    # PUSHC: 1
    [NOSLatch.TOS, TOSLatch.CR, MCAdrLatch.ZERO],

    # PUSH addr: 2
    [ARLatch.CR, MEMSignal.READ_TOS, MCAdrLatch.INC],
    [NOSLatch.TOS, TOSLatch.MEM, MCAdrLatch.ZERO],

    # POP: 4
    [ARLatch.CR, MEMSignal.WRITE, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.ZERO],

    # ADD: 6
    [ALULatch.ADD, TOSLatch.ALU, MCAdrLatch.ZERO],

    # SUB: 7
    [ALULatch.SUB, TOSLatch.ALU, MCAdrLatch.ZERO],

    # MUL: 8
    [ALULatch.MUL, TOSLatch.ALU, MCAdrLatch.ZERO],

    # DIV: 9
    [ALULatch.DIV, TOSLatch.ALU, MCAdrLatch.ZERO],

    # MOD: 10
    [ALULatch.MOD, TOSLatch.ALU, MCAdrLatch.ZERO],

    # AND: 11
    [ALULatch.AND, TOSLatch.ALU, MCAdrLatch.ZERO],

    # OR: 12
    [ALULatch.OR, TOSLatch.ALU, MCAdrLatch.ZERO],

    # NOT: 13
    [ALULatch.NOT, TOSLatch.ALU, MCAdrLatch.ZERO],

    # NEG: 14
    [ALULatch.NEG, TOSLatch.ALU, MCAdrLatch.ZERO],

    # DUP: 15
    [NOSLatch.TOS, MCAdrLatch.ZERO],

    # DROP: 16
    [TOSLatch.NOS, MCAdrLatch.ZERO],

    # CMP: 17
    [ALULatch.SUB, TOSLatch.NOS, MCAdrLatch.ZERO],

    # JMP: 18
    [JUMP.JMP, MCAdrLatch.ZERO],

    # JZ: 19
    [JUMP.JZ, MCAdrLatch.ZERO],

    # JN: 20
    [JUMP.JN, MCAdrLatch.ZERO],

    # IN: 21
    [NOSLatch.TOS, TOSLatch.INPUT, MCAdrLatch.ZERO],

    # OUT: 22
    [IOLatch.OUT, MCAdrLatch.INC],
    [TOSLatch.NOS, TOSLatch.NOS, MCAdrLatch.ZERO],

    # HALT: 24
    [PROG.HALT],

    # CALL addr: 25
    [RSLatch.PC, MCAdrLatch.INC],
    [JUMP.JMP, MCAdrLatch.ZERO],

    # RET: 27
    [PCLatch.RS, MCAdrLatch.ZERO],

    # NEXT addr: 28
    [JUMP.NEXT, MCAdrLatch.ZERO],

    # TORS: 29
    [RSLatch.TOS, TOSLatch.NOS, MCAdrLatch.ZERO],

    # FROMRS: 30
    [NOSLatch.TOS, TOSLatch.RS, MCAdrLatch.ZERO],

    # SWAP: 31
    [RSLatch.TOS, TOSLatch.NOS, MCAdrLatch.INC],
    [NOSLatch.RS, MCAdrLatch.ZERO],
]

microcode = [encode_mc(step) for step in microcode]
