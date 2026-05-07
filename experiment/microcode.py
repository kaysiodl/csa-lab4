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
        Opcode.HALT: 54,
    }[op]


microcode = [
    # FETCH: 0
    [ARLatch.PC, MEMSignal.READ, MCAdrLatch.INC],
    [PCLatch.INC, MCAdrLatch.INPUT],

    # PUSHC: 2  — аргумент уже в CR после FETCH
    [DSLatch.PUSH, TOSLatch.CR, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # PUSH addr: 5  — загрузить MEM[addr] на стек
    [ARLatch.CR, MEMSignal.READ, MCAdrLatch.INC],  # AR←CR.arg, читаем MEM
    [DSLatch.PUSH, TOSLatch.MEM, MCAdrLatch.INC],  # TOS←MEM, старый TOS в DS
    [Instruction.INC, MCAdrLatch.ZERO],

    # POP: 8  — TOS=addr, NOS=value; MEM[addr]←NOS, снять оба
    [ARLatch.TOS, MEMSignal.WRITE, MCAdrLatch.INC],  # AR=TOS(addr), MEM[AR]←DS.peek()=NOS
    [DSLatch.POP, MCAdrLatch.INC],  # TOS←DS.pop()
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

    # NOT: 26  — унарная
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

    # SWAP: 34  — обменять TOS и NOS
    [BRLatch.TOS, MCAdrLatch.INC],
    [TOSLatch.NOS, MCAdrLatch.INC],
    [DSLatch.PUSH_BR, MCAdrLatch.INC],  # DS.push(BR=старый TOS)
    [Instruction.INC, MCAdrLatch.ZERO],

    # CMP: 36  — SUB, флаги, оба операнда снимаем
    [ALULatch.SUB, MCAdrLatch.INC],
    [DSLatch.POP, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # JMP: 39  — аргумент уже в CR
    [JUMP.JMP, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # JZ: 42
    [JUMP.JZ, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # JN: 45
    [JUMP.JN, MCAdrLatch.INC],
    [MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # IN: 48  — TOS = port_addr уже на стеке
    [DSLatch.PUSH, TOSLatch.INPUT, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # OUT: 50  — TOS=port, NOS=value
    [IOLatch.OUT, DSLatch.POP, MCAdrLatch.INC],
    [Instruction.INC, MCAdrLatch.ZERO],

    # HALT: 52
    [PROG.HALT],
]
