from enum import Enum


class Opcode(Enum):
    HALT = 0b00000
    PUSH = 0b00001
    POP = 0b00010
    PUSHC = 0b00011
    ADD = 0b00100
    SUB = 0b00101
    MUL = 0b00110
    DIV = 0b00111
    AND = 0b01000
    OR = 0b01001
    NOT = 0b01010
    MOD = 0b01011
    INC = 0b01100
    NEG = 0b01101
    SWAP = 0b01110
    CMP = 0b01111
    JMP = 0b10000
    JZ = 0b10001
    JN = 0b10010
    IN = 0b10011
    OUT = 0b10100
    DUP = 0b10101
    DROP = 0b10110
    CALL = 0b10111
    RET = 0b11000
    NEXT = 0b11001
    TORS = 0b11010
    FROMRS = 0b11011
    LOAD = 0b11100
    STORE = 0b11101


HAS_OPERAND = {
    Opcode.PUSH, Opcode.POP, Opcode.PUSHC,
    Opcode.JMP, Opcode.JZ, Opcode.JN,
    Opcode.CALL, Opcode.NEXT,
}


def encode(opcode: Opcode):
    return opcode.value


def decode(word: int):
    opcode_bits = word & 0x1F
    has_operand = True if Opcode(opcode_bits) in HAS_OPERAND else False
    return {"opcode": Opcode(opcode_bits), "has_operand": has_operand}
