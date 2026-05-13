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
        encode(Opcode.PUSHC, value),  # [x]
        encode(Opcode.DUP),  # [x, x]
        encode(Opcode.PUSHC, 0),  # [x, x, 0]
        encode(Opcode.CMP),  # Сравниваем x и 0. NOS=x, TOS=0. NOS < TOS -> N=1
        encode(Opcode.JN, 6),  # Если N=1 (x < 0), прыгаем на 6-й адрес (к NEG)
        encode(Opcode.HALT),  # 4: Если x >= 0, стоп.
        encode(Opcode.NEG),  # 5: Делаем NEG
        encode(Opcode.HALT)  # 6: Стоп
    ]


def get_sum_loop_program(n: int):
    return [
        encode(Opcode.PUSHC, 0),
        encode(Opcode.POP, 100),      # sum = 0

        encode(Opcode.PUSHC, n),      # N

        # --- loop start (3) ---
        encode(Opcode.DUP),           # N N
        encode(Opcode.PUSHC, 0),
        encode(Opcode.CMP),
        encode(Opcode.JZ, 14),

        encode(Opcode.DUP),           # N N
        encode(Opcode.PUSH, 100),    # N N sum
        encode(Opcode.ADD),          # N (N+sum)
        encode(Opcode.POP, 100),     # сохранить сумму

        encode(Opcode.PUSHC, 1),
        encode(Opcode.SUB),          # N-1

        encode(Opcode.JMP, 3),

        # --- end ---
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

def get_easy(val: int):
    return [

    ]

def run_program(str, program: list[int], result):
    print(str)
    result_dp = run(program)
    success = result_dp.tos == result
    print(f"\nРезультат TOS: {result_dp.tos}")
    print(f"ТЕСТ {'ПРОЙДЕН' if success else 'ПРОВАЛЕН'}")


# run_program("\n--- Запуск теста: Модуль числа ---", get_abs_program(-5), 5)
# run_program("\n--- Запуск теста: Хуйня числа ---", get_easy(-5), 5)
run_program("\n--- Запуск теста: Сумма чисел ---", get_sum_loop_program(5), 15)
# run_program("\n--- Запуск теста: Квадрат числа---", get_square_call_program(3), 9)
