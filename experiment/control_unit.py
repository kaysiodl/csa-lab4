import logging
from typing import ClassVar

from alu import ALU_OP
from datapath import DataPath
from isa import Opcode
from microcode import microcode, op2microcode, decode_mc
from signals_cpu import (
    ARLatch, NOSLatch, IOLatch, DRLatch, IRLatch,
    JUMP, MCAdrLatch, MEMSignal, PCLatch, PROG, RSLatch, TOSLatch,
)

class InvalidSignalError(Exception):
    pass


class ControlUnit:
    mc_adr: int
    datapath: DataPath
    tick: int
    instruction_count: int
    signal_handlers: ClassVar[dict]

    def __init__(self, datapath: DataPath):
        self.mc_adr = 0
        self.datapath = datapath
        self.tick = 0
        self.instruction_count = 0
        dp = self.datapath
        self.signal_handlers: dict[type] = {
            RSLatch: dp.signal_return_stack,
            ARLatch: dp.signal_latch_ar,
            MEMSignal: dp.signal_mem,
            IRLatch: dp.signal_latch_ir,
            DRLatch: dp.signal_latch_dr,
            NOSLatch: dp.signal_stack_ops,
            ALU_OP: dp.signal_alu_op,
            TOSLatch: dp.signal_latch_tos,
            IOLatch: dp.signal_io,
            PCLatch: dp.signal_latch_pc,
            JUMP: dp.signal_jump,
            MCAdrLatch: self._latch_mc_adr,
        }

    def _latch_mc_adr(self, signal: MCAdrLatch):
        match signal:
            case MCAdrLatch.ZERO:
                self.mc_adr = 0
                self.instruction_count += 1
            case MCAdrLatch.INC:
                self.mc_adr += 1
            case MCAdrLatch.INPUT:
                opcode = Opcode(self.datapath.ir)
                self.mc_adr = op2microcode(opcode)

    def execute_micro(self, mc_word: int):
        signals = decode_mc(mc_word)
        for signal in signals:
            if signal == PROG.HALT:
                raise StopIteration("HALT")
            handler = self.signal_handlers.get(type(signal))
            if handler is None:
                raise InvalidSignalError(f"Unknown signal: {signal!r}")
            handler(signal)
        logging.debug("%s", self._repr_state(mc_word))
        self.tick += 1

    def run_machine(self):
        try:
            while True:
                self.execute_micro(microcode[self.mc_adr])
        except StopIteration:
            pass
        except OSError:
            pass
        return self.instruction_count, self.tick

    def _repr_state(self, mc_word: int):
        dp = self.datapath
        signals = decode_mc(mc_word)
        sig_str = ", ".join(f"{type(s).__name__}.{s.name}" for s in signals)
        try:
            opcode_s = Opcode(dp.ir).name
        except ValueError:
            opcode_s = f"0x{dp.ir:02x}"
        return (
            "TICK:{:4d} | PC:{:3d} | AR:{:3d} | mc:{:2d} | "
            "mc=0x{:07x} | IR:{:10s} | DR:{:6} | TOS:{:6} | "
            "Z:{} N:{} | DS:{} | RS:{} | [{}]"
        ).format(
            self.tick, dp.pc, dp.ar, self.mc_adr,
            mc_word, opcode_s, str(dp.dr), str(dp.tos),
            int(dp.alu.zero_flag), int(dp.alu.neg_flag),
            dp.data_stack.stack[-2:] + [dp.tos],
            dp.return_stack.return_stack[-3:],
            sig_str,
        )
