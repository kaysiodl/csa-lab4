import logging
import sys
from collections import deque

from control_unit import ControlUnit
from datapath import DataPath, IOController, IOUnit
from isa import Opcode, encode

logging.basicConfig(
    level=logging.DEBUG,
    format="%(message)s",
    stream=sys.stdout
)


def make_dp(program: list[int], input_data=None) -> tuple[DataPath, IOController]:
    io = IOController()
    if input_data:
        io.connect(0, IOUnit(deque(input_data)))
    io.connect(1, IOUnit(deque()))
    dp = DataPath(65536, io)
    for i, w in enumerate(program):
        dp.memory.memory[i] = w
    return dp, io


def run(program: list[int]) -> DataPath:
    dp, io = make_dp(program)
    ControlUnit(dp).run_machine()
    return dp


def get_abs_program(value: int):
    return [
        encode(Opcode.PUSHC, value),
        encode(Opcode.DUP),
        encode(Opcode.PUSHC, 0),
        encode(Opcode.CMP),
        encode(Opcode.JN, 6),
        encode(Opcode.HALT),
        encode(Opcode.NEG),
        encode(Opcode.HALT)
    ]


def get_sum_loop_program(n: int):
    return [
        encode(Opcode.PUSHC, 0),
        encode(Opcode.POP, 100),

        encode(Opcode.PUSHC, n),

        # --- loop start (3) ---
        encode(Opcode.DUP),
        encode(Opcode.PUSHC, 0),
        encode(Opcode.CMP),
        encode(Opcode.JZ, 14),

        encode(Opcode.DUP),
        encode(Opcode.PUSH, 100),
        encode(Opcode.ADD),
        encode(Opcode.POP, 100),

        encode(Opcode.PUSHC, 1),
        encode(Opcode.SUB),

        encode(Opcode.JMP, 3),

        encode(Opcode.PUSH, 100),
        encode(Opcode.HALT)
    ]


def get_square_call_program(val: int):
    return [
        encode(Opcode.PUSHC, val),  # [val]
        encode(Opcode.CALL, 4),  # [val] -> прыжок на 4, RS=[1]
        encode(Opcode.HALT),  # 2: Конец программы
        encode(Opcode.HALT),  # 3: пустая ячейка

        encode(Opcode.DUP),  # [x, x]
        encode(Opcode.MUL),  # [x*x]
        encode(Opcode.RET)  # Прыжок на адрес из RS (на 2)
    ]


def get_next_program(n: int):
    """Считает сумму 1+2+...+n через NEXT"""
    return [
        encode(Opcode.PUSHC, 0),    # 0: acc = 0
        encode(Opcode.PUSHC, n),
        encode(Opcode.DUP),
        encode(Opcode.DUP),
        encode(Opcode.TORS),        # 2: RS.push(n), TOS = acc
        encode(Opcode.PUSHC, -1),
        encode(Opcode.ADD),         # 4: acc + n
        encode(Opcode.NEXT, 3),     # 5: RS[-1]--, если != 0 -> 3, иначе pop RS
        encode(Opcode.HALT),        # 6
    ]


def get_stack_test():
    return [
        encode(Opcode.PUSHC, 1),
        encode(Opcode.PUSHC, 2),
        encode(Opcode.PUSHC, 3),
        encode(Opcode.ADD),  # 2+3=5
        encode(Opcode.DUP),  # 5,5
        encode(Opcode.ADD),  # 10
        encode(Opcode.HALT)
    ]


def get_memory_test():
    return [
        encode(Opcode.PUSHC, 42),
        encode(Opcode.POP, 200),  #MEM[200]=42

        encode(Opcode.PUSHC, 0),
        encode(Opcode.PUSH, 200),  #42
        encode(Opcode.HALT)
    ]

def get_swap():
    return [
        encode(Opcode.PUSHC, 5),
        encode(Opcode.PUSHC, 4),
        encode(Opcode.SWAP),
        encode(Opcode.SWAP),
        encode(Opcode.HALT)
    ]

def get_hello_program():
    return [
        #читаем длину
        encode(Opcode.PUSHC, 0),
        encode(Opcode.IN),
        encode(Opcode.TORS),

        encode(Opcode.PUSHC, 0),
        encode(Opcode.IN),          #TOS=char

        encode(Opcode.PUSHC, 1),    #TOS=ппорт, NOS=char

        encode(Opcode.OUT),

        encode(Opcode.NEXT, 3),

        encode(Opcode.HALT)
    ]

def get_recursive_factorial_program(n: int):
    return [
        # main
        encode(Opcode.PUSHC, n),      # 0
        encode(Opcode.CALL, 4),       # 1
        encode(Opcode.MUL),          # 2
        encode(Opcode.HALT),          # 3

        # fact(n)
        # stack: [n]

        encode(Opcode.DUP),           # 4
        encode(Opcode.PUSHC, 1),      # 5
        encode(Opcode.CMP),           # 6
        encode(Opcode.JZ, 16),        # 7

        # recursive case
        encode(Opcode.DUP),           # 8   keep n for multiply
        encode(Opcode.PUSHC, 1),      # 9
        encode(Opcode.SUB),           # 10  n-1

        encode(Opcode.CALL, 4),       # 11  fact(n-1)

        encode(Opcode.MUL),           # 12  n * fact(n-1)

        encode(Opcode.RET),           # 13

        encode(Opcode.HALT),          # 14
        encode(Opcode.HALT),          # 15

        # base case:
        encode(Opcode.PUSHC, 1),      # 16
        encode(Opcode.RET),           # 17
    ]


def run_program(str, program: list[int], result):
    print(str)
    result_dp = run(program)
    success = result_dp.tos == result
    print(f"\nРезультат TOS: {result_dp.tos}")
    print(f"ТЕСТ {'ПРОЙДЕН' if success else 'ПРОВАЛЕН'}")

hello_data = [
    5,
    ord('H'),
    ord('E'),
    ord('L'),
    ord('L'),
    ord('O')
]

dp, io = make_dp(get_hello_program(), hello_data)

# ControlUnit(dp).run_machine()
#
# print(io._connected_units[1].get_list_output())
# print("".join(map(chr, io._connected_units[1].get_list_output())))


# run_program("\n--- Запуск теста: Модуль числа ---", get_abs_program(0), 0)
# run_program("\n--- Запуск теста: Сумма чисел ---", get_sum_loop_program(5), 15)
# run_program("\n--- Запуск теста: Квадрат числа---", get_square_call_program(3), 9)
# run_program("\n--- Запуск теста: стек---", get_stack_test(), 10)
# run_program("\n---MEM: store/load---", get_memory_test(), 42)
# # run_program("\n--- Запуск теста: next---", get_next_program(5), 15)
# run_program("\n--- Запуск теста: swap---", get_swap(), 4)
run_program(
    "\n--- factorial recursion ---",
    get_recursive_factorial_program(5),
    120
)





