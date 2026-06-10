# import os
# import subprocess
# import pytest
#
# GOLDEN_DIR = os.path.join(os.path.dirname(__file__), "golden")
#
#
# def get_tests():
#     return [d for d in os.listdir(GOLDEN_DIR)
#             if os.path.isdir(os.path.join(GOLDEN_DIR, d))]
#
#
# @pytest.mark.parametrize("test_name", get_tests())
# def test_golden(test_name, tmp_path):
#     test_dir = os.path.join(GOLDEN_DIR, test_name)
#     source = os.path.join(test_dir, "source.lisp")
#     stdin_file = os.path.join(test_dir, "stdin.txt")
#     expected_code = open(os.path.join(test_dir, "out_code.txt")).read().strip()
#     expected_stdout = open(os.path.join(test_dir, "out_stdout.txt")).read().strip()
#     expected_log = open(os.path.join(test_dir, "out_log.txt")).read().strip()
#
#     binary = str(tmp_path / "out.bin")
#
#     # транслятор
#     result = subprocess.run(
#         ["python", "codegencodegen.py", source, binary],
#         capture_output=True, text=True
#     )
#     assert result.returncode == 0, result.stderr
#     assert result.stdout.strip() == expected_code
#
#     # симулятор
#     cmd = ["python", "machine.py", binary]
#     if os.path.exists(stdin_file):
#         cmd.append(stdin_file)
#
#     result = subprocess.run(cmd, capture_output=True, text=True)
#     assert result.returncode == 0, result.stderr
#
#     lines = result.stdout.strip().split("\n")
#     log_lines = [l for l in lines if l.startswith("TICK")]
#     out_lines = [l for l in lines if not l.startswith("TICK")]
#
#     assert "\n".join(out_lines) == expected_stdout
#     assert "\n".join(log_lines[:20]) == expected_log  # первые 20 строк лога