from enum import Enum


class ALU_OP(Enum):
    ADD = 1
    SUB = 2
    MUL = 3
    DIV = 4
    AND = 5
    OR = 6
    NOT = 7
    PASS_FIRST = 8

class ALU:
    def __init__(self):
        self.result = 0
        self.zero_flag = False
        self.neg_flag = False
        self.carry_flag = False

        self.first = 0
        self.second = 0

    def compute(self, op: ALU_OP) -> int:
        match op:
            case ALU_OP.ADD:
                self.result = self.first + self.second
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
            case ALU_OP.PASS_FIRST:
                self.result = self.first

        if self.result > 0x7FF:
            self.carry_flag = True
        elif self.result == 0:
            self.zero_flag = True
        elif self.result < 0:
            self.neg_flag = True

        self.result = self._to_int32(self.result)
        return self.result

    @staticmethod
    def _to_int32(val: int) -> int:
        val = val & 0xFFFFFFFF
        if val >= 0x80000000:
            val -= 0x100000000
        return val
