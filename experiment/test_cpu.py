import sys
import logging
from collections import deque
from isa import Opcode, encode
from datapath import DataPath, IOController, IOUnit
from control_unit import ControlUnit

# Настройка логов для отображения тиков в консоли
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
H = encode(Opcode.HALT)
print("\n--- Запуск теста: Сумма двух чисел ---")

# Программа: положить 10, положить 20, сложить, остановиться
program = [
    encode(Opcode.PUSHC, 10),
    encode(Opcode.PUSHC, 20),
    encode(Opcode.SUB),
    H
]

# Выполнение
result_dp = run(program)

# Проверка результата
success = result_dp.tos == -10
print(f"\nРезультат TOS: {result_dp.tos}")
print(f"ТЕСТ {'ПРОЙДЕН' if success else 'ПРОВАЛЕН'}")

sys.exit(0 if success else 1)