from isa import Opcode
from translator.linter import Symbols, type_of
from translator.nodes import (
    AddC,
    ARef,
    Array,
    ASet,
    BinOp,
    Call,
    Compare,
    Const,
    Def,
    If,
    Len,
    Name,
    Print,
    Read,
    ReadStr,
    Set,
    Str,
    Var,
    While,
)

PARAM_ADDR = 0x0F00
PTR_ADDR = 0x0F04
BUF_ADDR = 0x0F08
BUF_BASE = 0x3000
BUF_SIZE = 256

IN_PORT = 0
OUT_PORT = 1
BYTE_MASK = 0xFF

BINOPS = {"+": Opcode.ADD, "-": Opcode.SUB, "*": Opcode.MUL, "/": Opcode.DIV, "%": Opcode.MOD}


def codegen(ast: list, sym: Symbols) -> bytearray:
    variables = sym.variables
    var_types = sym.var_types
    strings = sym.strings

    code = bytearray()
    call_fixups = []
    func_addr = {}
    buffers: dict = {}
    state = {"buf_next": BUF_BASE, "print_str": False, "read_str": False}

    def emit(op):
        code.append(op.value)

    def word(value):
        return (value & 0xFFFFFFFF).to_bytes(4, "little")

    def emit_arg(op, operand):
        code.append(op.value)
        code.extend(word(operand))

    def emit_jump(op):
        code.append(op.value)
        offset = len(code)
        code.extend(b"\x00\x00\x00\x00")
        return offset

    def patch(offset, value):
        code[offset:offset + 4] = word(value)

    def here():
        return len(code)

    def gen(node, param):
        if isinstance(node, Const):
            emit_arg(Opcode.PUSHC, node.value)
        elif isinstance(node, Str):
            emit_arg(Opcode.PUSHC, strings[node.value])
        elif isinstance(node, Name):
            emit_arg(Opcode.PUSH, PARAM_ADDR if node.name == param else variables[node.name])
        elif isinstance(node, BinOp):
            gen(node.left, param)
            gen(node.right, param)
            emit(BINOPS[node.op])
        elif isinstance(node, AddC):
            gen(node.left, param)
            gen(node.right, param)
            emit(Opcode.ADC)
        elif isinstance(node, Compare):
            gen_compare(node, param)
        elif isinstance(node, If):
            gen_if(node, param)
        elif isinstance(node, While):
            gen_while(node, param)
        elif isinstance(node, Set):
            gen(node.expr, param)
            emit(Opcode.DUP)
            emit_arg(Opcode.POP, variables[node.name])
        elif isinstance(node, Var):
            if isinstance(node.expr, Array):
                emit_arg(Opcode.PUSHC, variables[node.name])
            else:
                gen(node.expr, param)
                emit(Opcode.DUP)
                emit_arg(Opcode.POP, variables[node.name])
        elif isinstance(node, ARef):
            emit_arg(Opcode.PUSHC, variables[node.name])
            gen(node.idx, param)
            emit_arg(Opcode.PUSHC, 4)
            emit(Opcode.MUL)
            emit(Opcode.ADD)
            emit(Opcode.LOAD)
        elif isinstance(node, ASet):
            gen(node.val, param)
            emit_arg(Opcode.PUSHC, variables[node.name])
            gen(node.idx, param)
            emit_arg(Opcode.PUSHC, 4)
            emit(Opcode.MUL)
            emit(Opcode.ADD)
            emit(Opcode.STORE)
        elif isinstance(node, Call):
            gen(node.arg, param)
            call_fixups.append((emit_jump(Opcode.CALL), node.name))
        elif isinstance(node, Print):
            gen_print(node, param)
        elif isinstance(node, Read):
            emit_arg(Opcode.PUSHC, IN_PORT)
            emit(Opcode.IN)
            emit(Opcode.SWAP)
            emit(Opcode.DROP)
        elif isinstance(node, ReadStr):
            gen_read_str(node)
        elif isinstance(node, Len):
            gen(node.arg, param)
            emit(Opcode.LOAD)
            emit_arg(Opcode.PUSHC, BYTE_MASK)
            emit(Opcode.AND)
        else:
            raise TypeError(f"Cannot generate {node!r}")

    def gen_to_flag(node, param):
        gen(node, param)
        emit(Opcode.NEG)
        emit(Opcode.DROP)

    def gen_if(node, param):
        gen_to_flag(node.cond, param)
        jz = emit_jump(Opcode.JZ)
        gen(node.then, param)
        jmp = emit_jump(Opcode.JMP)
        patch(jz, here())
        gen(node.els, param)
        patch(jmp, here())

    def gen_while(node, param):
        loop = here()
        gen_to_flag(node.cond, param)
        jz = emit_jump(Opcode.JZ)
        for expr in node.body:
            gen(expr, param)
            emit(Opcode.DROP)
        emit_arg(Opcode.JMP, loop)
        patch(jz, here())
        emit_arg(Opcode.PUSHC, 0)

    def gen_compare(node, param):
        if node.op == ">":
            gen(node.right, param)
            gen(node.left, param)
        else:
            gen(node.left, param)
            gen(node.right, param)
        emit(Opcode.CMP)
        emit(Opcode.DROP)
        emit(Opcode.DROP)
        if node.op == "!=":
            jz = emit_jump(Opcode.JZ)
            emit_arg(Opcode.PUSHC, 1)
            jmp = emit_jump(Opcode.JMP)
            patch(jz, here())
            emit_arg(Opcode.PUSHC, 0)
            patch(jmp, here())
        else:
            test = Opcode.JZ if node.op == "=" else Opcode.JN
            j = emit_jump(test)
            emit_arg(Opcode.PUSHC, 0)
            jmp = emit_jump(Opcode.JMP)
            patch(j, here())
            emit_arg(Opcode.PUSHC, 1)
            patch(jmp, here())

    def gen_print(node, param):
        gen(node.arg, param)
        if type_of(node.arg, var_types, param) == "str":
            state["print_str"] = True
            call_fixups.append((emit_jump(Opcode.CALL), "__print_str"))
        else:
            emit(Opcode.DUP)
            emit_arg(Opcode.PUSHC, OUT_PORT)
            emit(Opcode.OUT)

    def gen_read_str(node):
        buf = buffers.get(id(node))
        if buf is None:
            buf = state["buf_next"]
            buffers[id(node)] = buf
            state["buf_next"] += BUF_SIZE
        state["read_str"] = True
        emit_arg(Opcode.PUSHC, buf)
        call_fixups.append((emit_jump(Opcode.CALL), "__read_str"))

    def emit_print_str():
        emit(Opcode.DUP)
        emit(Opcode.DUP)
        emit(Opcode.LOAD)
        emit_arg(Opcode.PUSHC, BYTE_MASK)
        emit(Opcode.AND)
        emit(Opcode.DUP)
        emit(Opcode.NEG)
        emit(Opcode.DROP)
        jz_empty = emit_jump(Opcode.JZ)
        emit(Opcode.TORS)
        loop = here()
        emit_arg(Opcode.PUSHC, 1)
        emit(Opcode.ADD)
        emit(Opcode.DUP)
        emit(Opcode.LOAD)
        emit_arg(Opcode.PUSHC, BYTE_MASK)
        emit(Opcode.AND)
        emit_arg(Opcode.PUSHC, OUT_PORT)
        emit(Opcode.OUT)
        emit_arg(Opcode.NEXT, loop)
        emit(Opcode.DROP)
        jmp_done = emit_jump(Opcode.JMP)
        patch(jz_empty, here())
        emit(Opcode.DROP)
        emit(Opcode.DROP)
        patch(jmp_done, here())
        emit(Opcode.RET)

    def emit_read_str():
        emit(Opcode.DUP)
        emit_arg(Opcode.POP, BUF_ADDR)
        emit(Opcode.DUP)
        emit_arg(Opcode.POP, PTR_ADDR)
        emit_arg(Opcode.PUSHC, IN_PORT)
        emit(Opcode.IN)
        emit(Opcode.SWAP)
        emit(Opcode.DROP)
        emit(Opcode.SWAP)
        emit(Opcode.STORE)
        emit(Opcode.DUP)
        emit(Opcode.NEG)
        emit(Opcode.DROP)
        jz_empty = emit_jump(Opcode.JZ)
        emit(Opcode.TORS)
        loop = here()
        emit_arg(Opcode.PUSH, PTR_ADDR)
        emit_arg(Opcode.PUSHC, 1)
        emit(Opcode.ADD)
        emit(Opcode.DUP)
        emit_arg(Opcode.POP, PTR_ADDR)
        emit_arg(Opcode.PUSHC, IN_PORT)
        emit(Opcode.IN)
        emit(Opcode.SWAP)
        emit(Opcode.DROP)
        emit(Opcode.SWAP)
        emit(Opcode.STORE)
        emit(Opcode.DROP)
        emit_arg(Opcode.NEXT, loop)
        jmp_done = emit_jump(Opcode.JMP)
        patch(jz_empty, here())
        emit(Opcode.DROP)
        patch(jmp_done, here())
        emit_arg(Opcode.PUSH, BUF_ADDR)
        emit(Opcode.RET)

    def emit_prologue():
        emit_arg(Opcode.PUSH, PARAM_ADDR)
        emit(Opcode.TORS)
        emit_arg(Opcode.POP, PARAM_ADDR)

    def emit_epilogue():
        emit(Opcode.FROMRS)
        emit_arg(Opcode.POP, PARAM_ADDR)
        emit(Opcode.RET)

    for node in ast:
        if isinstance(node, Def):
            continue
        gen(node, None)
        emit(Opcode.DROP)
    emit(Opcode.HALT)

    for node in ast:
        if not isinstance(node, Def):
            continue
        func_addr[node.name] = here()
        emit_prologue()
        for i, expr in enumerate(node.body):
            gen(expr, node.param)
            if i < len(node.body) - 1:
                emit(Opcode.DROP)
        emit_epilogue()

    if state["print_str"]:
        func_addr["__print_str"] = here()
        emit_print_str()
    if state["read_str"]:
        func_addr["__read_str"] = here()
        emit_read_str()

    for offset, name in call_fixups:
        patch(offset, func_addr[name])

    return code


def build_memory(code: bytearray, sym: Symbols, size: int = 65536) -> bytearray:
    mem = bytearray(size)
    mem[0:len(code)] = code
    for text, addr in sym.strings.items():
        mem[addr] = len(text) & 0xFF
        for i, ch in enumerate(text):
            mem[addr + 1 + i] = ord(ch) & 0xFF
    return mem
