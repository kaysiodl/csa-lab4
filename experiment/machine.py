import argparse
import logging
from collections import deque
from pathlib import Path

from control_unit import ControlUnit
from datapath import DataPath, IOController, IOUnit

MEM_SIZE = 65536
DEFAULT_LIMIT = 10_000_000


def parse_input(text: str) -> list[int]:
    tokens: list[int] = []
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == '"':
            j = i + 1
            while j < len(text) and text[j] != '"':
                j += 1
            literal = text[i + 1:j]
            tokens.append(len(literal))
            tokens.extend(ord(c) for c in literal)
            i = j + 1
        else:
            j = i
            while j < len(text) and not text[j].isspace():
                j += 1
            tokens.append(int(text[i:j]))
            i = j
    return tokens


def decode_text(values: list[int]) -> str:
    out = []
    for v in values:
        if v == 10:
            out.append("\\n")
        elif 32 <= v <= 126:
            out.append(chr(v))
        else:
            out.append(f"\\x{v & 0xFF:02x}")
    return "".join(out)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run binary machine code on the processor model")
    ap.add_argument("program", help="binary machine code file (.bin)")
    ap.add_argument("input", nargs="?", help="input data file (token stream)")
    ap.add_argument("--log", help="write the tick-level journal to this file")
    ap.add_argument("--limit", type=int, default=DEFAULT_LIMIT, help="max ticks before giving up")
    args = ap.parse_args()

    image = Path(args.program).read_bytes()
    buffer = parse_input(Path(args.input).read_text(encoding="utf-8-sig")) if args.input else []

    io = IOController()
    io.connect(0, IOUnit(deque(buffer)))
    out = IOUnit(deque())
    io.connect(1, out)

    dp = DataPath(MEM_SIZE, io)
    dp.memory.memory[:len(image)] = image

    handler = None
    if args.log:
        handler = logging.FileHandler(args.log, mode="w", encoding="utf-8")
        handler.setFormatter(logging.Formatter("%(message)s"))
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        instr, ticks = ControlUnit(dp).run_machine(limit=args.limit)
    finally:
        if handler is not None:
            logging.getLogger().removeHandler(handler)
            handler.close()

    output = out.get_list_output()
    print("output (num) :", output)
    print("output (text):", repr(decode_text(output)))
    print("instructions :", instr)
    print("ticks        :", ticks)
    if ticks >= args.limit:
        print(f"WARNING: did not halt within {args.limit} ticks")
    if args.log:
        print("journal      :", args.log)


if __name__ == "__main__":
    main()
