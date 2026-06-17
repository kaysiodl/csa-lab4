from __future__ import annotations

import dataclasses
import logging
from collections import deque
from pathlib import Path

import pytest
import yaml
from codegen import build_memory, codegen
from control_unit import ControlUnit
from datapath import DataPath, IOController, IOUnit
from isa import disasm
from linter import lint
from parser import parse, tokenize

GOLDEN_DIR = Path(__file__).resolve().parent / "golden"
LOG_LIMIT = 10_000


class LogCollector(logging.Handler):
    def __init__(self):
        super().__init__()
        self.records: list[str] = []

    def emit(self, record):
        self.records.append(self.format(record))


def translate(source: str):
    ast = parse(tokenize(source))
    sym = lint(ast)
    code = codegen(ast, sym)
    memory = build_memory(code, sym)
    return ast, sym, code, memory


def simulate(memory: bytearray, input_buffer: list[int]):
    io = IOController()
    io.connect(0, IOUnit(deque(input_buffer)))
    out = IOUnit(deque())
    io.connect(1, out)
    dp = DataPath(len(memory), io)
    dp.memory.memory = memory

    logger = logging.getLogger()
    handler = LogCollector()
    handler.setFormatter(logging.Formatter("%(message)s"))
    prev_level = logger.level
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    try:
        instr, ticks = ControlUnit(dp).run_machine()
    finally:
        logger.removeHandler(handler)
        logger.setLevel(prev_level)

    return out.get_list_output(), instr, ticks, handler.records


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


def render_ast(ast: list) -> str:
    lines = ["Program"]
    for i, node in enumerate(ast):
        _render(node, lines, "", i == len(ast) - 1, f"top_levels[{i}]")
    return "\n".join(lines)


def _render(value, lines, prefix, last, label):
    branch = "└─ " if last else "├─ "
    cont = "   " if last else "│  "
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        scalars, kids = [], []
        for field in dataclasses.fields(value):
            inner = getattr(value, field.name)
            if isinstance(inner, list):
                for j, item in enumerate(inner):
                    kids.append((f"{field.name}[{j}]", item))
            elif dataclasses.is_dataclass(inner) and not isinstance(inner, type):
                kids.append((field.name, inner))
            else:
                scalars.append(f"{field.name}={inner!r}")
        head = f"{label}: {type(value).__name__}"
        if scalars:
            head += "  " + " ".join(scalars)
        lines.append(prefix + branch + head)
        for j, (name, inner) in enumerate(kids):
            _render(inner, lines, prefix + cont, j == len(kids) - 1, name)
    else:
        lines.append(prefix + branch + f"{label}: {value!r}")


class FlowList(list):
    pass


class LiteralStr(str):
    pass


def _flow_list_repr(dumper, data):
    return dumper.represent_sequence("tag:yaml.org,2002:seq", data, flow_style=True)


def _literal_repr(dumper, data):
    return dumper.represent_scalar("tag:yaml.org,2002:str", str(data), style="|")


yaml.add_representer(FlowList, _flow_list_repr, Dumper=yaml.SafeDumper)
yaml.add_representer(LiteralStr, _literal_repr, Dumper=yaml.SafeDumper)


def _format_stdout(output: list[int], instr: int, ticks: int) -> str:
    return (
        f"ticks: {ticks}\n"
        f"instr: {instr}\n"
        f"output_words: {len(output)}\n"
        f"output_hex: {['0x' + format(v & 0xFFFFFFFF, 'x') for v in output]}\n"
        f"output_num: {output}\n"
        f"output_text: {decode_text(output)!r}\n"
    )


CASES = sorted(p.stem for p in GOLDEN_DIR.glob("*.yaml"))


@pytest.mark.parametrize("case", CASES)
def test_golden(case: str, request) -> None:
    regen = request.config.getoption("--regen")
    path = GOLDEN_DIR / f"{case}.yaml"
    spec = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    src = spec["in_source"]
    raw_buf = spec.get("in_buffer") or []
    buf = [ord(t) if isinstance(t, str) else int(t) for t in raw_buf]
    limit = int(spec.get("in_limit", 100_000))

    ast_nodes, sym, code, memory = translate(src)
    output, instr, ticks, log = simulate(memory, buf)

    if ticks >= limit:
        raise AssertionError(f"{case}: did not halt within {limit} ticks (last={ticks})")

    out_stdout = _format_stdout(output, instr, ticks)
    out_ast = render_ast(ast_nodes)
    out_code_hex = disasm(code)
    out_log = "\n".join(log[:LOG_LIMIT])

    if regen:
        new_spec = {
            "in_source": LiteralStr(src.rstrip("\n")),
            "in_buffer": FlowList(buf),
            "in_limit": limit,
            "out_stdout": LiteralStr(out_stdout.rstrip("\n")),
            "out_ast": LiteralStr(out_ast.rstrip("\n")),
            "out_code_hex": LiteralStr(out_code_hex.rstrip("\n")),
            "out_log": LiteralStr(out_log.rstrip("\n")),
        }
        with path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(new_spec, f, sort_keys=False, allow_unicode=True, width=120)
        return

    def _norm(s: str | None) -> str:
        return (s or "").rstrip("\n")

    assert _norm(spec.get("out_stdout")) == _norm(out_stdout), f"{case}: out_stdout mismatch"
    assert _norm(spec.get("out_ast")) == _norm(out_ast), f"{case}: out_ast mismatch"
    assert _norm(spec.get("out_code_hex")) == _norm(out_code_hex), f"{case}: out_code_hex mismatch"
    assert _norm(spec.get("out_log")) == _norm(out_log), f"{case}: out_log mismatch"
