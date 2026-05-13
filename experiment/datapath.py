import logging
from collections import deque

from alu import ALU, ALU_OP
from isa import decode
from signals_cpu import *


class DataStack:
    def __init__(self):
        self.stack: list[int] = []

    def push(self, val: int): self.stack.append(val)

    def pop(self) -> int:
        if not self.stack: raise IndexError("Data stack underflow")
        return self.stack.pop()

    def peek(self) -> int: return self.stack[-1] if self.stack else 0


class ReturnStack:
    def __init__(self):
        self.return_stack: list[int] = []

    def push(self, addr: int): self.return_stack.append(addr)

    def pop(self) -> int:
        if not self.return_stack: raise IndexError("Return stack underflow")
        return self.return_stack.pop()

    def peek(self) -> int: return self.return_stack[-1] if self.return_stack else 0

    def __repr__(self): return str(self.return_stack)


class Memory:
    def __init__(self, size=65536):
        self.memory = [0] * size
        self.data_out = 0

    def read(self, addr: int): self.data_out = self.memory[addr % len(self.memory)]

    def write(self, addr: int, val: int): self.memory[addr % len(self.memory)] = val


class IOUnit:
    def __init__(self, input_buffer: deque):
        self._input_buffer = input_buffer
        self._output_buffer: deque = deque()

    def read(self) -> int:
        if not self._input_buffer: raise IOError("No input to read")
        return self._input_buffer.popleft()

    def write(self, value: int): self._output_buffer.append(value)

    def get_list_output(self) -> list: return list(self._output_buffer)


class IOController:
    def __init__(self):
        self._connected_units: dict[int, IOUnit] = {}

    def connect(self, port: int, unit: IOUnit):
        self._connected_units[port] = unit

    def read(self, port: int) -> int:
        if port not in self._connected_units: raise Exception(f"No device on port {port}")
        return self._connected_units[port].read()

    def write(self, port: int, value: int):
        if port not in self._connected_units: raise Exception(f"No device on port {port}")
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
        self.cr = 0
        self.memory = Memory(mem_size)
        self.data_stack = DataStack()
        self.return_stack = ReturnStack()
        self.alu = ALU()
        self.io_controller = io_controller

    def signal_latch_ar(self, sel: ARLatch):
        if sel == ARLatch.PC:
            self.ar = self.pc
        elif sel == ARLatch.TOS:
            self.ar = self.tos
        elif sel == ARLatch.CR:
            decoded = decode(self.cr)
            self.ar = decoded["arg"] & 0x07FF_FFFF

    def signal_latch_pc(self, sel: PCLatch):
        if sel == PCLatch.INC:
            self.pc = (self.pc + 1) & 0x07FF_FFFF
        elif sel == PCLatch.CR:
            decoded = decode(self.cr)
            self.pc = decoded["arg"] & 0x07FF_FFFF
        elif sel == PCLatch.RS:
            self.pc = self.return_stack.pop()

    def signal_latch_tos(self, sel: TOSLatch):
        if sel == TOSLatch.MEM:
            self.tos = self.memory.data_out
        elif sel == TOSLatch.ALU:
            self.tos = self.alu.result
        elif sel == TOSLatch.NOS:
            self.tos = self.data_stack.pop()
        elif sel == TOSLatch.INPUT:
            port_address = self.tos
            self.tos = self.io_controller.read(port_address)
        elif sel == TOSLatch.CR:
            decoded = decode(self.cr)
            self.tos = decoded["arg"]
        elif sel == TOSLatch.RS:
            self.tos = self.return_stack.pop()

    def signal_stack_ops(self, sel: DSLatch):
        if sel == DSLatch.PUSH:
            self.data_stack.push(self.tos)

    def signal_return_stack(self, sel: RSLatch):
        if sel == RSLatch.PC:
            self.return_stack.push(self.pc)
        elif sel == RSLatch.TOS:
            self.return_stack.push(self.tos)

    def signal_alu_op(self, op: ALULatch):
        try:
            op = ALU_OP(op.value)
        except ValueError:
            return
        unary = {ALU_OP.NOT, ALU_OP.NEG, ALU_OP.INC}
        if op not in unary:
            self.alu.first = self.data_stack.peek()
            self.alu.second = self.tos
        else:
            self.alu.first = self.tos
            self.alu.second = 0
        if op in ALU_OP:
            self.alu.compute(op)
        if op not in unary and self.data_stack.stack:
            self.data_stack.pop()

    def signal_mem(self, sel: MEMSignal):
        if sel == MEMSignal.READ_CR:
            self.memory.read(self.ar)
            self.cr = self.memory.data_out
        if sel == MEMSignal.READ_TOS:
            self.memory.read(self.ar)
        elif sel == MEMSignal.WRITE:
            self.memory.write(self.ar, self.tos)

    def signal_io(self, sel: IOLatch):
        if sel == IOLatch.OUT:
            port = self.tos
            value = self.data_stack.peek()
            self.io_controller.write(port, value)

    def signal_jump(self, sel: JUMP):
        decoded = decode(self.cr)
        if sel == JUMP.JMP:
            self.pc = decoded["arg"] & 0x07FF_FFFF
        elif sel == JUMP.JZ:
            if self.alu.zero_flag:
                self.pc = decoded["arg"] & 0x07FF_FFFF
        elif sel == JUMP.JN:
            if self.alu.neg_flag:
                self.pc = decoded["arg"]

    def check_zero(self):
        return self.alu.zero_flag or self.tos == 0

    def check_negative(self):
        return self.alu.neg_flag or self.tos < 0
