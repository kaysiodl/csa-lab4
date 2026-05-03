MEMORY_SIZE = 2**16

class DataPath:
    def __init__(self):
        self.memory = [0] * MEMORY_SIZE
        self.stack = []
        self.pc = 0
        self.ir = 0
        self.z_flag = False
        self.n_flag = False
        self.input_ports = {}
        self.output_ports = {}
    def push(self, value): self.stack.append(value)
    def pop(self): return self.stack.pop()
    def tos(self): return self.stack[-1]