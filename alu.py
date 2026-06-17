from enum import Enum


class ALU_OP(Enum):
    ADD = 1
    SUB = 2
    MUL = 3
    DIV = 4
    AND = 5
    OR = 6
    NOT = 7
    NEG = 8
    INC = 9
    MOD = 10
    CMP = 11
    ADC = 12


class ALU:
    def __init__(self):
        self.result = 0
        self.zero_flag = False
        self.neg_flag = False
        self.carry_flag = False
        self.first = 0
        self.second = 0

    def compute(self, op: ALU_OP) -> int:
        carry_in = 1 if self.carry_flag else 0
        match op:
            case ALU_OP.ADD:
                self.result = self.first + self.second
            case ALU_OP.ADC:
                self.result = self.first + self.second + carry_in
            case ALU_OP.SUB:
                self.result = self.first - self.second
            case ALU_OP.MUL:
                self.result = self.first * self.second
            case ALU_OP.DIV:
                if self.second == 0:
                    raise ZeroDivisionError("division by zero")
                self.result = int(self.first / self.second)
            case ALU_OP.AND:
                self.result = self.first & self.second
            case ALU_OP.OR:
                self.result = self.first | self.second
            case ALU_OP.NOT:
                self.result = ~self.first
            case ALU_OP.NEG:
                self.result = 0 - self.first
            case ALU_OP.INC:
                self.result = self.first + 1
            case ALU_OP.MOD:
                self.result = self.first % self.second
            case ALU_OP.CMP:
                self.result = self.first - self.second
        self.zero_flag = False
        self.neg_flag = False
        if op == ALU_OP.ADC:
            self.carry_flag = (self.first & 0xFFFFFFFF) + (self.second & 0xFFFFFFFF) + carry_in > 0xFFFFFFFF
        if self.result == 0:
            self.zero_flag = True
        if self.result < 0:
            self.neg_flag = True
        self.result = self._to_int32(self.result)
        return self.result

    @staticmethod
    def _to_int32(val):
        val = val & 0xFFFFFFFF
        if val >= 0x80000000:
            val -= 0x100000000
        return val
