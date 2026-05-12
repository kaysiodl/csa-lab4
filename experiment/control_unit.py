import logging
from typing import ClassVar

from datapath import DataPath
from isa import decode
from microcode import microcode, op2microcode, decode_mc
from signals_cpu import (
    ALULatch, ARLatch, BRLatch, DSLatch, Instruction, IOLatch,
    JUMP, MCAdrLatch, MEMSignal, PCLatch, PROG, RSLatch, TOSLatch,
)

INSTRUCTION_LIMIT = 100_000


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
        self.signal_handlers: dict[type, tuple] = {
            RSLatch:     (dp.signal_return_stack, True),
            ARLatch:     (dp.signal_latch_ar,     True),
            MEMSignal:   (dp.signal_mem,          True),
            BRLatch:     (dp.signal_latch_br,     True),
            DSLatch:     (dp.signal_stack_ops,    True),
            ALULatch:    (dp.signal_alu_op,       True),
            TOSLatch:    (dp.signal_latch_tos,    True),
            IOLatch:     (dp.signal_io,           True),
            PCLatch:     (dp.signal_latch_pc,     True),
            JUMP:        (dp.signal_jump,         True),
            MCAdrLatch:  (self._latch_mc_adr,     True),
            Instruction: (self._inc_instruction,  False),
        }

    def _latch_mc_adr(self, signal: MCAdrLatch):
        match signal:
            case MCAdrLatch.ZERO:  self.mc_adr = 0
            case MCAdrLatch.INC:   self.mc_adr += 1
            case MCAdrLatch.INPUT:
                opcode = decode(self.datapath.cr)["opcode"]
                self.mc_adr = op2microcode(opcode)

    def _inc_instruction(self):
        self.instruction_count += 1

    def execute_micro(self, mc_word: int):
        signals = decode_mc(mc_word)
        for signal in signals:
            if isinstance(signal, PROG):
                raise StopIteration("HALT")
            handler_entry = self.signal_handlers.get(type(signal))
            if handler_entry is None:
                raise InvalidSignalError(f"Unknown signal: {signal!r}")
            method, needs_arg = handler_entry
            method(signal) if needs_arg else method()
        logging.debug("%s", self._repr_state(mc_word))
        self.tick += 1

    def run_machine(self):
        try:
            while self.instruction_count < INSTRUCTION_LIMIT:
                self.execute_micro(microcode[self.mc_adr])
        except StopIteration:
            pass
        except OSError:
            pass
        return self.instruction_count, self.tick

    def _repr_state(self, mc_word: int) -> str:
        dp = self.datapath
        signals = decode_mc(mc_word)
        sig_str  = ", ".join(f"{type(s).__name__}.{s.name}" for s in signals)
        cr_info  = decode(dp.cr) if dp.cr else {}
        opcode_s = str(cr_info.get("opcode", "?"))
        return (
            "TICK:{:4d} | PC:{:3d} AR:{:3d} mc:{:2d} | "
            "mc=0x{:07x} | CR:{:10s} | TOS:{:6} | "
            "Z:{} N:{} | DS:{} RS:{} | [{}]"
        ).format(
            self.tick, dp.pc, dp.ar, self.mc_adr,
            mc_word, opcode_s, str(dp.tos),
            int(dp.alu.zero_flag), int(dp.alu.neg_flag),
            dp.data_stack.stack[-3:],
            dp.return_stack.return_stack[-3:],
            sig_str,
        )