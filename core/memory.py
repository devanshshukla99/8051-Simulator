import re
import textwrap

from core.flags import flags
from core.basic_memory import Byte
from core.exceptions import InvalidMemoryAddress, MemoryLimitExceeded

"""
8051 has

4kB ROM = 000-FFF
128B RAM = 00-7F
4 Register Banks = R0-R7 = 32 general purpose registers = 32Bytes
16 bit timers
16 bit PC and DPTR
"""


class Memory(dict):
    def __init__(self, memory_size=65536, starting_address="0x0000", _bytes=2, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._bytes = 1
        self._base = 16
        self._memory_size = memory_size - 1
        self._starting_address = starting_address

        self._default_mem = "0x00"
        self._format_spec = f"#0{2 + _bytes * 2}x"
        self._format_spec_bin = f"#0{2 + _bytes * 4}b"
        self._memory_limit = int(starting_address, 16) + self._memory_size
        self._memory_limit_hex = format(self._memory_limit, self._format_spec)
        return

    def __getitem__(self, addr: str) -> str:
        addr = self._verify(addr)
        if addr not in self:
            super().__setitem__(addr, Byte(self._default_mem))
        return super().__getitem__(addr)

    def __setitem__(self, addr: str, value: str) -> None:
        addr = self._verify(addr)
        if addr not in self:
            super().__setitem__(addr, Byte(value))
        return super().__getitem__(addr).write(value)

    def _verify(self, value: str) -> None:
        if not re.fullmatch("^0[x|X][0-9a-fA-F]+", str(value)):
            raise InvalidMemoryAddress()
        if int(str(value), self._base) > self._memory_limit:
            raise MemoryLimitExceeded()
        return format(int(value, self._base), self._format_spec)

    def sort(self):
        return dict(sorted(self.items(), key=lambda x: int(str(x[0]), 16)))

    def read(self, *args, **kwargs):
        return self.__getitem__(*args, **kwargs)

    def write(self, *args, **kwargs):
        return self.__setitem__(*args, **kwargs)

    pass


class RegisterPair:
    def __init__(self, reg_1, reg_2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reg_1 = reg_1
        self._reg_2 = reg_2
        self._registers = {
            reg_1: Byte(),
            reg_2: Byte(),
        }
        self._bytes = 2
        self._base = 16
        self.keys = self._registers.keys
        self.values = self._registers.values
        self.items = self._registers.items
        return

    def __getitem__(self, key):
        return self._registers.get(key).read()

    def __setitem__(self, key, value):
        return self._registers.get(key).write(value)

    def __repr__(self):
        return f"{self._registers.get(self._reg_1)} {self._registers.get(self._reg_2)}"

    def read(self, addr) -> Byte:
        return self._registers.get(str(addr).upper())

    def read_pair(self) -> str:
        bin1 = format(int(str(self._registers.get(self._reg_1).read()), self._base), f"0{self._bytes * 4}b")
        bin2 = format(int(str(self._registers.get(self._reg_2).read()), self._base), f"0{self._bytes * 4}b")
        bin_total = "".join(["0b", bin1, bin2])
        return f'0x{format(int(bin_total, 2), f"0{self._bytes * 2}x")}'

    def write(self, data, addr) -> bool:
        return self._registers.get(str(addr).upper()).__call__(data)

    def write_pair(self, data) -> bool:
        mem_size = 8
        binary_data = format(int(str(data), self._base), f"0{self._bytes*8}b")
        data_1, data_2 = [
            format(int(binary_data[mem_size * x : mem_size * (x + 1)], 2), f"#0{int(mem_size/2)}x")
            for x in range(0, int(len(binary_data) / mem_size))
        ]
        self._registers.get(str(self._reg_1).upper()).__call__(data_1)
        self._registers.get(str(self._reg_2).upper()).__call__(data_2)
        return True


class FProgramCounter:
    def __init__(self, _bytes=2, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._bytes = _bytes
        self._base = 16
        self._registers = Byte(_bytes=self._bytes)
        return

    def __getitem__(self) -> str:
        return str(self._registers)

    def __setitem__(self, value: str) -> None:
        return self._registers(value)

    def __repr__(self) -> str:
        return str(self._registers)

    def read(self) -> Byte:
        return self._registers.upper()

    def write(self, data: str) -> bool:
        return self._registers(str(data).upper())

    pass


class StackPointer(Byte):
    def __init__(self, memory, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.memory = memory

    def __add__(self, val: int, *args, **kwargs) -> str:
        """
        val: `int`
        """
        data_int = int(self._data, self._base) + val
        if data_int > self._memory_limit:
            data_int -= self._memory_limit
        elif data_int < 0:
            data_int += self._memory_limit
        self._data = format(data_int, self._format_spec)
        return self._data

    def __sub__(self, val: int, *args, **kwargs) -> str:
        """
        val: `int`
        """
        data_int = int(self._data, self._base) - val
        if data_int > self._memory_limit:
            data_int -= self._memory_limit
        elif data_int < 0:
            data_int += self._memory_limit
        self._data = format(data_int, self._format_spec)
        return self._data

    def __next__(self):
        return self.__add__(1)

    def read(self, *args, **kwargs) -> Byte:
        """
        POP rp
        """
        bin1 = format(int(str(self.memory[self.__add__(1)]), self._base), f"0{8}b")  # single byte
        bin2 = format(int(str(self.memory[self.__add__(1)]), self._base), f"0{8}b")  # single byte
        bin_total = "".join(["0b", bin2, bin1])
        return f'0x{format(int(bin_total, 2), f"0{4}x")}'

    def write(self, data, *args) -> Byte:
        """
        PUSH rp
        rp = BC, DE, HL, or PSW
        """
        mem_size = 8
        binary_data = format(int(str(data), self._base), f"0{self._bytes*8}b")
        data_1, data_2 = [
            format(int(binary_data[mem_size * x : mem_size * (x + 1)], 2), f"#0{int(mem_size/2)}x")
            for x in range(0, int(len(binary_data) / mem_size))
        ]
        self.memory.write(self._data, data_1)
        _ = self.__sub__(1)
        self.memory.write(self._data, data_2)
        _ = self.__sub__(1)
        return True


class ProgramCounter(Byte):
    def __init__(self, memory, _bytes=2, *args, **kwargs) -> None:
        super().__init__(_bytes=2, *args, **kwargs)
        self.memory = memory
        return

    def write(self, data):
        self.memory[self._data] = data
        self.__next__()
        return True


class SuperMemory:
    def __init__(self) -> None:
        self.memory_rom = Memory(4096, "0x000")
        self.memory_ram = Memory(128, "0x00")

        self.A = Byte()
        self.B = Byte()
        self.SP = StackPointer(self.memory_ram, "0x07", _bytes=1)
        self.PC = ProgramCounter(self.memory_rom)

    def __repr__(self) -> str:
        return "<SuperMemory>"

    def _reg_inspect(self):
        return textwrap.dedent(
            f"""
            Registers
            ---------
            A/PSW = {self.A} {flags.PSW}
            B = {self.B}
            SP = {self.SP}
            PC = {self.PC}
            """
        )

    def _registers_todict(self):
        return {
            "A/PSW": f"{self.A} {flags.PSW}",
            "B": f"{self.B}",
            "SP": f"{self.SP}",
            "PC": f"{self.PC}",
        }

    def inspect(self):
        return "\n\n".join([self._reg_inspect(), str(self.memory.sort())])

    pass
