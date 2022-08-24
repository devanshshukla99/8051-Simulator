import re
import textwrap

from core.exceptions import InvalidMemoryAddress, MemoryLimitExceeded

"""
8051 has

4kB ROM = 000-FFF
128B RAM = 00-7F
4 Register Banks = R0-R7 = 32 general purpose registers = 32Bytes
16 bit timers
16 bit PC and DPTR
"""


class Hex:
    def __init__(self, data: str = "0x00", _bytes: str = 1, *args, **kwargs) -> None:
        self._bytes = _bytes
        self._base = 16
        self._format_spec = f"#0{2 + _bytes * 2}x"
        self._format_spec_bin = f"#0{2 + _bytes * 8}b"
        self._memory_limit_hex = "FF" * _bytes
        self._memory_limit = int(self._memory_limit_hex, self._base)
        self.data = data
        return

    def __call__(self, value: str) -> None:
        self.data = value

    def __str__(self) -> str:
        return self._data

    def __repr__(self) -> str:
        return self._data

    def __int__(self) -> int:
        return int(self._data, self._base)

    def __index__(self) -> int:
        return int(self._data, self._base)

    def __format__(self, format_spec: str = None) -> str:
        if not format_spec:
            format_spec = self._format_spec
        return format(int(self._data, self._base), format_spec)

    def __next__(self):
        self._data = format(int(self._data, self._base) + 1, self._format_spec)
        return self._data

    def __add__(self, val: int):
        return Hex(format(int(self._data, self._base) + val, self._format_spec), _bytes=self._bytes)

    def __sub__(self, val: int):
        return Hex(format(int(self._data, self._base) - val, self._format_spec), _bytes=self._bytes)

    def __len__(self):
        return self._bytes

    def _verify(self, value: str):
        if not re.fullmatch("^0[x|X][0-9a-fA-F]+", str(value)):
            raise InvalidMemoryAddress()
        if int(str(value), self._base) > self._memory_limit:
            raise MemoryLimitExceeded()

    def bin(self) -> str:
        return format(int(self._data, self._base), self._format_spec_bin)

    @property
    def data(self) -> str:
        return self._data

    @data.setter
    def data(self, val: str) -> None:
        self._verify(val)
        self._data = format(int(str(val), self._base), self._format_spec)
        return

    def read(self, *args, **kwargs) -> str:
        return self

    def write(self, val: str, *args, **kwargs) -> bool:
        self.data = val
        return True

    def update(self, val: str, *args, **kwargs) -> bool:
        return self.write(val, *args, **kwargs)

    def replace(self, *args, **kwargs) -> None:
        return self._data.replace(*args, **kwargs)

    def lower(self, *args, **kwargs):
        return self._data.lower(*args, **kwargs)

    def upper(self, *args, **kwargs):
        return self._data.upper(*args, **kwargs)

    pass


class Byte(Hex):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    pass


class Memory(dict):
    def __init__(self, memory_size=65535, starting_address="0x0000", _bytes=2, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._bytes = 1
        self._base = 16
        self._memory_size = memory_size
        self._starting_address = starting_address

        self._default_mem = "0x00"
        self._format_spec = f"#0{2 + _bytes * 2}x"
        self._format_spec_bin = f"#0{2 + _bytes * 4}b"
        self._memory_limit = int(starting_address, 16) + memory_size
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
        self.memory_rom = Memory(4095, "0x000")
        self.memory_ram = Memory(127, "0x00")

        self.A = Byte()
        self.PSW = Byte()
        self.SP = StackPointer(self.memory_ram, "0x07", _bytes=1)
        self.PC = ProgramCounter(self.memory_rom)
        # setattr(self.M.__func__, "read", lambda *args: self.memory[self.HL.read_pair()])
        # setattr(self.M.__func__, "write", lambda data, *args: self.memory.write(self.HL.read_pair(), data))

    def __repr__(self) -> str:
        return "<SuperMemory>"

    # def M(self):
    #     return

    def _reg_inspect(self):
        return textwrap.dedent(
            f"""
            Registers
            ---------
            A/PSW = {self.A} {self.PSW}
            B = {self.B}
            SP = {self.SP}
            PC = {self.PC}
            """
        )

    def _registers_todict(self):
        return {
            "A/PSW": f"{self.A} {self.PSW}",
            "B": f"{self.B}",
            "SP": f"{self.SP}",
            "PC": f"{self.PC}",
        }

    def inspect(self):
        return "\n\n".join([self._reg_inspect(), str(self.memory.sort())])

    pass
