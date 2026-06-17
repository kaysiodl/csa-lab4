import logging
from collections import deque

from alu import ALU, ALU_OP
from signals_cpu import (
    JUMP,
    ARLatch,
    DRLatch,
    IOLatch,
    IRLatch,
    MEMSignal,
    NOSLatch,
    PCLatch,
    RSLatch,
    TOSLatch,
)


class DataStack:
    def __init__(self):
        self.stack: list[int] = []

    def push(self, val: int):
        self.stack.append(val)

    def pop(self):
        if not self.stack:
            raise IndexError("Data stack underflow")
        return self.stack.pop()

    def peek(self):
        return self.stack[-1] if self.stack else 0


class ReturnStack:
    def __init__(self):
        self.return_stack: list[int] = []

    def push(self, addr: int):
        self.return_stack.append(addr)

    def pop(self):
        if not self.return_stack:
            raise IndexError("Return stack underflow")
        return self.return_stack.pop()

    def peek(self):
        return self.return_stack[-1] if self.return_stack else 0

    def __repr__(self):
        return str(self.return_stack)


class Memory:
    def __init__(self, size=65536):
        self.memory = bytearray(size)
        self.data_out = 0

    def read_byte(self, addr: int):
        return self.memory[addr % len(self.memory)]

    def read_word(self, addr: int):
        """Читаем 4 байта little-endian,знаковый"""
        b = [self.memory[(addr + i) % len(self.memory)] for i in range(4)]
        val = b[0] | (b[1] << 8) | (b[2] << 16) | (b[3] << 24)
        if val >= 0x80000000:
            val -= 0x100000000
        return val

    def write_word(self, addr: int, val: int):
        """Пишем 4 байта little-endian."""
        val = val & 0xFFFFFFFF
        for i in range(4):
            self.memory[(addr + i) % len(self.memory)] = (val >> (8 * i)) & 0xFF


class IOUnit:
    def __init__(self, input_buffer: deque):
        self._input_buffer = input_buffer
        self._output_buffer: deque = deque()

    def read(self):
        if not self._input_buffer:
            raise OSError("No input to read")
        return self._input_buffer.popleft()

    def write(self, value: int):
        self._output_buffer.append(value)

    def get_list_output(self) -> list:
        return list(self._output_buffer)


class IOController:
    def __init__(self):
        self._connected_units: dict[int, IOUnit] = {}

    def connect(self, port: int, unit: IOUnit):
        self._connected_units[port] = unit

    def read(self, port: int):
        if port not in self._connected_units:
            raise Exception(f"No device on port {port}")
        return self._connected_units[port].read()

    def write(self, port: int, value: int):
        if port not in self._connected_units:
            raise Exception(f"No device on port {port}")
        if 32 <= value <= 126:
            logging.debug("Output: `%s` (%d) on port %d", chr(value), value, port)
        else:
            logging.debug("Output: %d on port %d", value, port)
        self._connected_units[port].write(value)


class DataPath:
    def __init__(self, mem_size, io_controller: IOController):
        self.pc = 0
        self.ar = 0
        self.tos = 0
        self.ir = 0
        self.dr = 0
        self.memory = Memory(mem_size)
        self.data_stack = DataStack()
        self.return_stack = ReturnStack()
        self.alu = ALU()
        self.io_controller = io_controller

    def signal_latch_ir(self, sel: IRLatch):
        if sel == IRLatch.MEM:
            self.ir = self.memory.data_out

    def signal_latch_dr(self, sel: DRLatch):
        if sel == DRLatch.MEM:
            self.dr = self.memory.data_out

    def signal_latch_ar(self, sel: ARLatch):
        if sel == ARLatch.PC:
            self.ar = self.pc
        elif sel == ARLatch.TOS:
            self.ar = self.tos
        elif sel == ARLatch.DR:
            self.ar = self.dr

    def signal_latch_pc(self, sel: PCLatch):
        match sel:
            case PCLatch.INC:
                self.pc += 1
            case PCLatch.INC4:
                self.pc += 4
            case PCLatch.DR:
                self.pc = self.dr
            case PCLatch.RS:
                self.pc = self.return_stack.pop()

    def signal_latch_tos(self, sel: TOSLatch):
        if sel == TOSLatch.ALU:
            self.tos = self.alu.result
        elif sel == TOSLatch.NOS:
            self.tos = self.data_stack.pop()
        elif sel == TOSLatch.INPUT:
            self.tos = self.io_controller.read(self.tos)
        elif sel == TOSLatch.DR:
            self.tos = self.dr
        elif sel == TOSLatch.RS:
            self.tos = self.return_stack.pop()

    def signal_stack_ops(self, sel: NOSLatch):
        if sel == NOSLatch.TOS:
            self.data_stack.push(self.tos)
        elif sel == NOSLatch.RS:
            self.data_stack.push(self.return_stack.pop())

    def signal_return_stack(self, sel: RSLatch):
        if sel == RSLatch.PC:
            self.return_stack.push(self.pc)
        elif sel == RSLatch.TOS:
            self.return_stack.push(self.tos)

    def signal_alu_op(self, op: ALU_OP):
        unary = {ALU_OP.NOT, ALU_OP.NEG, ALU_OP.INC}
        if op not in unary:
            self.alu.first = self.data_stack.peek()
            self.alu.second = self.tos
        else:
            self.alu.first = self.tos
            self.alu.second = 0
        self.alu.compute(op)
        if op not in unary and self.data_stack.stack and op != ALU_OP.CMP:
            self.data_stack.pop()

    def signal_mem(self, sel: MEMSignal):
        match sel:
            case MEMSignal.READ_BYTE:
                self.memory.data_out = self.memory.read_byte(self.ar)
            case MEMSignal.READ_WORD:
                self.memory.data_out = self.memory.read_word(self.ar)
            case MEMSignal.WRITE_WORD:
                self.memory.write_word(self.ar, self.tos)

    def signal_io(self, sel: IOLatch):
        if sel == IOLatch.OUT:
            port = self.tos
            value = self.data_stack.pop()
            self.io_controller.write(port, value)

    def signal_jump(self, sel: JUMP):
        if sel == JUMP.JMP:
            self.pc = self.dr
        elif sel == JUMP.JZ:
            if self.alu.zero_flag:
                self.pc = self.dr
        elif sel == JUMP.JN:
            if self.alu.neg_flag:
                self.pc = self.dr
        elif sel == JUMP.NEXT:
            self.return_stack.return_stack[-1] -= 1
            if self.return_stack.peek() == 0:
                self.return_stack.pop()
            else:
                self.pc = self.dr
