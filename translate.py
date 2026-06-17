import argparse
from pathlib import Path

from isa import disasm
from translator.codegen import build_memory, codegen
from translator.linter import lint
from translator.parser import parse, tokenize


def translate(source: str):
    ast = parse(tokenize(source))
    sym = lint(ast)
    code = codegen(ast, sym)
    image = build_memory(code, sym)
    return code, image


def trim(image: bytearray, min_len: int) -> bytes:
    end = len(image)
    while end > min_len and image[end - 1] == 0:
        end -= 1
    return bytes(image[:end])


def main() -> None:
    ap = argparse.ArgumentParser(description="Translate lisp source into binary machine code")
    ap.add_argument("source", help="input source file (.lisp)")
    ap.add_argument("output", help="output binary file (.bin)")
    ap.add_argument("--debug", help="path for the <addr> - <hex> - <mnemonic> dump (default: <output>.dbg)")
    args = ap.parse_args()

    source = Path(args.source).read_text(encoding="utf-8-sig")
    code, image = translate(source)
    binary = trim(image, len(code))

    Path(args.output).write_bytes(binary)
    debug_path = args.debug or args.output + ".dbg"
    Path(debug_path).write_text(disasm(code) + "\n", encoding="utf-8")

    print(f"source : {args.source}")
    print(f"binary : {args.output} ({len(binary)} bytes)")
    print(f"debug  : {debug_path}")
    print(f"code   : {len(code)} bytes")


if __name__ == "__main__":
    main()
