from typing import List
import struct

class MoneroVM:
    def __init__(self, initial_gas: int, memory_limit: int = 1024 * 1024):
        self.gas = initial_gas
        self.pc = 0  # Program counter
        self.stack = []  # The VM stack
        self.memory = bytearray()  # Memory for the VM
        self.memory_limit = memory_limit

    def push(self, value: int):
        if len(self.stack) >= 1024:
            raise RuntimeError("Stack overflow")
        self.stack.append(value)

    def pop(self) -> int:
        if not self.stack:
            raise RuntimeError("Stack underflow")
        return self.stack.pop()

    def peek(self, index: int) -> int:
        if index >= len(self.stack):
            raise RuntimeError("Stack index out of bounds")
        return self.stack[-(index + 1)]

    def mem_store(self, offset: int, value: int):
        # Ensure memory is large enough, expanding with gas cost if necessary
        while len(self.memory) <= offset + 31:
            self.memory.extend(b'\x00')  # Extend with null bytes
            self.consume_gas(3)  # Example cost for memory expansion

        # Store the value in big-endian format
        for i in range(32):
            self.memory[offset + i] = (value >> (8 * (31 - i))) & 0xFF

        # Check for memory usage limit
        if len(self.memory) > self.memory_limit:
            raise RuntimeError("Memory limit exceeded")

    def mem_load(self, offset: int) -> int:
        if offset + 31 >= len(self.memory):
            raise RuntimeError("Memory access out of bounds")
        result = 0
        for i in range(32):
            result |= self.memory[offset + i] << (8 * (31 - i))
        return result

    def consume_gas(self, amount: int):
        if self.gas < amount:
            raise RuntimeError("Insufficient gas")
        self.gas -= amount

    def execute(self, bytecode: List[int]) -> bool:
        while self.pc < len(bytecode):
            if self.gas == 0:
                raise RuntimeError("Out of gas")

            op = bytecode[self.pc]
            self.pc += 1
            if op == 0x00:  # STOP
                print("Execution stopped.")
                return True
            elif op == 0x01:  # ADD
                self.consume_gas(3)
                a, b = self.pop(), self.pop()
                self.push(a + b)
            elif op == 0x02:  # MUL
                self.consume_gas(5)
                a, b = self.pop(), self.pop()
                self.push(a * b)
            elif op == 0x03:  # SUB
                self.consume_gas(3)
                a, b = self.pop(), self.pop()
                self.push(a - b)
            elif op == 0x04:  # DIV
                self.consume_gas(5)
                a, b = self.pop(), self.pop()
                if b == 0:
                    raise RuntimeError("Division by zero")
                self.push(a // b)
            elif op == 0x05:  # MLOAD
                self.consume_gas(3)
                offset = self.pop()
                self.push(self.mem_load(offset))
            elif op == 0x06:  # MSTORE
                self.consume_gas(3)
                value = self.pop()
                offset = self.pop()
                self.mem_store(offset, value)
            else:
                raise RuntimeError(f"Unknown opcode: {op}")

            print(f"Remaining gas: {self.gas}")

        return True

    def validate_bytecode(self, bytecode: List[int]) -> bool:
        pc = 0
        max_stack_size = 0
        current_stack_size = 0

        while pc < len(bytecode):
            op = bytecode[pc]
            pc += 1
            if op in [0x01, 0x02, 0x03, 0x04]:  # ADD, MUL, SUB, DIV
                current_stack_size -= 1
            elif op == 0x06:  # MSTORE
                current_stack_size -= 2
            elif op in [0x00, 0x05]:  # STOP, MLOAD - no change to stack
                pass
            else:
                print(f"Validation: Unknown opcode at position {pc - 1}")
                return False

            if current_stack_size < 0:
                print(f"Validation: Stack underflow at opcode position {pc - 1}")
                return False

            max_stack_size = max(max_stack_size, current_stack_size)
            if max_stack_size > 1024:
                print("Validation: Maximum stack size exceeded during validation")
                return False

        if current_stack_size != 0:
            print("Validation: Stack not empty at end of bytecode")
            return False

        print(f"Bytecode validation successful. Max stack size was {max_stack_size}")
        return True

    def get_remaining_gas(self) -> int:
        return self.gas

    def set_memory_limit(self, new_memory_limit: int):
        self.memory_limit = new_memory_limit
