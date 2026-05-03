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
    CMP = 0b01011
    JMP = 0b10000
    JZ = 0b10001
    JN = 0b10010
    IN = 0b10011
    OUT = 0b10100
    DUP = 0b10101
    DROP = 0b10110


def encode(opcode: Opcode, arg: int = 0) -> int:
    arg_27 = arg & 0x07FF_FFFF
    return (opcode.value << 27) | arg_27


def decode(word: int) -> dict:
    opcode_bits = (word >> 27) & 0x1F
    arg_bits = word & 0x07FF_FFFF
    if arg_bits >= (1 << 26):
        arg_bits -= (1 << 27)
    return {"opcode": Opcode(opcode_bits), "arg": arg_bits, "raw": word}
