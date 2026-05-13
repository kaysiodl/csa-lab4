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

        Opcode.CMP: 18,

        Opcode.JMP: 19,
        Opcode.JZ: 20,
        Opcode.JN: 21,

        Opcode.IN: 22,
        Opcode.OUT: 23,

        Opcode.HALT: 25,

        Opcode.CALL: 26,
        Opcode.RET: 28,
    }[op]


def encode_mc(signals: list) -> int:
    SHIFTS = {
        RSLatch: 23,
        ARLatch: 21,
        MEMSignal: 19,
        DSLatch: 17,
        ALULatch: 13,
        TOSLatch: 10,
        IOLatch: 8,
        PCLatch: 6,
        JUMP: 4,
        MCAdrLatch: 2,
        Instruction: 1,
        PROG: 0
    }

    control_word = 0
    for s in signals:
        signal_type = type(s)
        if signal_type in SHIFTS:
            control_word |= (s.value << SHIFTS[signal_type])

    return control_word


def decode_mc(mc: int) -> list:
    FIELDS = [
        (RSLatch, 23, 0b11),
        (ARLatch, 21, 0b11),
        (MEMSignal, 19, 0b11),
        (DSLatch, 17, 0b11),
        (ALULatch, 13, 0b1111),
        (TOSLatch, 10, 0b111),
        (IOLatch, 8, 0b11),
        (PCLatch, 6, 0b11),
        (JUMP, 4, 0b11),
        (MCAdrLatch, 2, 0b11),
        (Instruction, 1, 0b1),
        (PROG, 0, 0b1),
    ]
    result = []
    for cls, shift, mask in FIELDS:
        val = (mc >> shift) & mask
        if val != 0:
            result.append(cls(val))

    return result


microcode = [
    # FETCH: 0
    [ARLatch.PC, MEMSignal.READ_CR, PCLatch.INC, MCAdrLatch.INPUT],

    # PUSHC: 1
    [DSLatch.PUSH, TOSLatch.CR, Instruction.INC, MCAdrLatch.ZERO],

    # PUSH addr: 2
    [ARLatch.CR, MEMSignal.READ_TOS, MCAdrLatch.INC],
    [DSLatch.PUSH, TOSLatch.MEM, Instruction.INC, MCAdrLatch.ZERO],

    # POP: 4
    [ARLatch.CR, MEMSignal.WRITE, MCAdrLatch.INC],
    [TOSLatch.NOS, Instruction.INC, MCAdrLatch.ZERO],

    # ADD: 6
    [ALULatch.ADD, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # SUB: 7
    [ALULatch.SUB, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # MUL: 8
    [ALULatch.MUL, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # DIV: 9
    [ALULatch.DIV, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # MOD: 10
    [ALULatch.MOD, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # AND: 11
    [ALULatch.AND, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # OR: 12
    [ALULatch.OR, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # NOT: 13
    [ALULatch.NOT, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # NEG: 14
    [ALULatch.NEG, TOSLatch.ALU, Instruction.INC, MCAdrLatch.ZERO],

    # DUP: 15
    [DSLatch.PUSH, Instruction.INC, MCAdrLatch.ZERO],

    # DROP: 16
    [TOSLatch.NOS, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # SWAP:
    # [BRLatch.TOS, TOSLatch.NOS, MCAdrLatch.INC],
    # [DSLatch.PUSH_BR, Instruction.INC, MCAdrLatch.ZERO],

    # CMP: 18
    [ALULatch.SUB, TOSLatch.NOS, Instruction.INC, MCAdrLatch.ZERO],

    # JMP: 19
    [JUMP.JMP, Instruction.INC, MCAdrLatch.ZERO],

    # JZ: 20
    [JUMP.JZ, Instruction.INC, MCAdrLatch.ZERO],

    # JN: 21
    [JUMP.JN, Instruction.INC, MCAdrLatch.ZERO],

    # IN: 22
    [DSLatch.PUSH, TOSLatch.INPUT, Instruction.INC, MCAdrLatch.ZERO],

    # OUT: 23
    [IOLatch.OUT, TOSLatch.NOS, MCAdrLatch.INC],
    [TOSLatch.NOS, Instruction.INC, MCAdrLatch.ZERO],

    # HALT: 25
    [PROG.HALT],

    # CALL addr: 26
    [RSLatch.PC, MCAdrLatch.INC],
    [JUMP.JMP, Instruction.INC, MCAdrLatch.ZERO],

    # RET: 28
    [PCLatch.RS, Instruction.INC, MCAdrLatch.ZERO],
]

microcode = [encode_mc(step) for step in microcode]
print(microcode)
