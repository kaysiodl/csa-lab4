from isa import Opcode
from signals_cpu import *


def op2microcode(op: Opcode) -> int:
    return {
        Opcode.PUSHC: 2, Opcode.PUSH: 5, Opcode.POP: 8,
        Opcode.ADD: 12, Opcode.SUB: 14, Opcode.MUL: 16,
        Opcode.DIV: 18, Opcode.MOD: 20, Opcode.AND: 22,
        Opcode.OR: 24, Opcode.NOT: 26, Opcode.NEG: 28,
        Opcode.DUP: 30, Opcode.DROP: 32, Opcode.SWAP: 34,
        Opcode.CMP: 38, Opcode.JMP: 41, Opcode.JZ: 44,
        Opcode.JN: 47, Opcode.IN: 50, Opcode.OUT: 52,
        Opcode.HALT: 54, Opcode.CALL: 55, Opcode.RET: 58,
    }[op]


def encode_mc(signals: list) -> int:
    SHIFTS = {
        RSLatch: 25,
        ARLatch: 23,
        MEMSignal: 21,
        BRLatch: 19,
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
        (RSLatch, 25, 0b11),
        (ARLatch, 23, 0b11),
        (MEMSignal, 21, 0b11),
        (BRLatch, 19, 0b11),
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
    [ARLatch.PC, MEMSignal.READ, MCAdrLatch.INC],
    [PCLatch.INC, MCAdrLatch.INPUT],

    # PUSHC: 2
    [DSLatch.PUSH, TOSLatch.CR, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # PUSH addr: 5
    [ARLatch.CR, MEMSignal.READ, MCAdrLatch.INC],
    [DSLatch.PUSH, TOSLatch.MEM, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # POP: 8
    [ARLatch.TOS, MEMSignal.WRITE, MCAdrLatch.INC],
    [DSLatch.POP, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # ADD: 12
    [ALULatch.ADD, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # SUB: 14
    [ALULatch.SUB, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # MUL: 16
    [ALULatch.MUL, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # DIV: 18
    [ALULatch.DIV, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # MOD: 20
    [ALULatch.MOD, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # AND: 22
    [ALULatch.AND, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # OR: 24
    [ALULatch.OR, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # NOT: 26
    [ALULatch.NOT, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # NEG: 28
    [ALULatch.NEG, TOSLatch.ALU, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # DUP: 30
    [DSLatch.PUSH, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # DROP: 32
    [DSLatch.POP, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # SWAP: 34
    [BRLatch.TOS, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.INC],
    [DSLatch.PUSH_BR, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # CMP: 38
    [ALULatch.SUB, MCAdrLatch.INC],
    [DSLatch.POP, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # JMP: 41
    [JUMP.JMP, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # JZ: 44
    [JUMP.JZ, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # JN: 47
    [JUMP.JN, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # IN: 50
    [DSLatch.PUSH, TOSLatch.INPUT, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # OUT: 52
    [IOLatch.OUT, DSLatch.POP, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # HALT: 54
    [PROG.HALT],

    # CALL addr: 55
    [RSLatch.PUSH, MCAdrLatch.INC],
    [JUMP.JMP, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # RET: 58
    [PCLatch.RS, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],
]

microcode = [encode_mc(step) for step in microcode]
print(microcode)
