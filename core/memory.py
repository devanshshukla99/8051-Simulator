import re
import textwrap

# from core.flags import flags
from core.basic_memory import Byte
from core.exceptions import InvalidMemoryAddress, MemoryLimitExceeded
from core.util import decompose_byte, get_byte_sequence

"""
8051 has

4kB ROM = 0000-0FFF
128 Bytes RAM = 00-7F
Another 128 Bytes RAM for accumulator and SFR = 7f-FF
4 Register Banks = R0-R7 = 32 general purpose registers = 32 Bytes
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
        return format(int(str(value), self._base), self._format_spec)

    def get(self, addr: str) -> Byte:
        return self.__getitem__(addr)

    def sort(self):
        return dict(sorted(self.items(), key=lambda x: int(str(x[0]), 16)))

    def read(self, *args, **kwargs):
        return self.__getitem__(*args, **kwargs)

    def write(self, *args, **kwargs):
        return self.__setitem__(*args, **kwargs)

    pass


class RegisterPair:
    def __init__(self, reg_1, addr_1, reg_2, addr_2, memory_ram, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._reg_1 = reg_1
        self._reg_2 = reg_2
        self._registers = {
            reg_1: LinkedRegister(memory_ram, addr_1),
            reg_2: LinkedRegister(memory_ram, addr_2),
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


class ProgramCounter(Byte):
    def __init__(self, memory, _bytes=2, *args, **kwargs) -> None:
        super().__init__(_bytes=_bytes, *args, **kwargs)
        self.memory = memory
        return

    def write(self, data):
        self.memory.write(self._data, data)
        self.__next__()
        return True


class LinkedRegister:
    def __init__(self, memory_ram: dict, addr: str) -> None:
        self._base = 16
        self.memory_ram = memory_ram
        setattr(
            self,
            "read",
            lambda *args: self.memory_ram.get(addr),
        )
        setattr(
            self,
            "write",
            lambda data, *args: self.memory_ram.get(addr).update(data),
        )
        pass

    def __repr__(self) -> str:
        return f"{self.read()}"

    def __str__(self) -> str:
        return self.__repr__()

    def bin(self) -> str:
        return self.read().bin()

    def bit_get(self, bit: str) -> bool:
        _binary_data = format(self.read(), "08b")
        bit = len(_binary_data) - int(bit) - 1
        _data = bool(int(_binary_data[int(bit)]))
        print(f"Getting {_binary_data[int(bit)]} / {_data} from {_binary_data}")
        return _data

    def bit_set(self, bit: str, val: str) -> bool:
        val = str(int(val))
        _binary_data = format(self.read(), "08b")
        bit = len(_binary_data) - int(bit) - 1
        print(f"Setting {_binary_data[int(bit)]} -> {val}")
        _new_binary_data = _binary_data[: int(bit)] + val + _binary_data[int(bit) + 1 :]
        print(f"Setting {_binary_data} -> {_new_binary_data}")
        _hex_data = format(int(_new_binary_data, 2), "#04x")
        return self.write(_hex_data)

    pass


class DataPointer:
    def __init__(self, memory_ram: dict, addr: list, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.memory_ram = memory_ram
        self._DPL = LinkedRegister(memory_ram, addr[0])
        self._DPH = LinkedRegister(memory_ram, addr[1])
        self._bytes = 2
        self._base = 16
        return

    def __repr__(self) -> str:
        return f"{self.read()}"

    def __str__(self) -> str:
        return self.__repr__()

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
        bin1 = format(int(str(self._DPL.read()), self._base), f"0{8*self._bytes}b")  # single byte
        bin2 = format(int(str(self._DPH.read()), self._base), f"0{8*self._bytes}b")  # single byte
        bin_total = "".join(["0b", bin2, bin1])
        return format(int(bin_total, 2), f"#0{self._bytes*2 + 2}x")

    def write(self, data, *args) -> Byte:
        data = decompose_byte(data)
        if len(data) != 2:
            raise InvalidMemoryAddress
        self._DPL.write(data[0])
        self._DPH.write(data[1])
        return True


class ProgramStatusWord:
    """
    "P": False,  # D0
    "_UD": False,  # D1 = UserDefined
    "OV": False,  # D2 = Overflow
    "RS0": False,  # D3 = Register bank selector
    "RS1": False,  # D4 = Register bank selector
    "F0": False,  # D5 = available for general purpose
    "AC": False,  # D6 = Aux Carry
    "CY": False,  # D7 = Carry
    """

    def __init__(self, memory_ram: dict, addr: str) -> None:
        self._PSW = LinkedRegister(memory_ram, addr)
        self._placeholder_flags = {
            "P": False,
            "_UD": False,
            "OV": False,
            "RS0": False,
            "RS1": False,
            "F0": False,
            "AC": False,
            "CY": False,
        }
        self._flag_keys = list(self._placeholder_flags.keys())
        pass

    def __repr__(self):
        return self.inspect()

    def __getitem__(self, key):
        return self.flags()[key]

    def _update_PSW(self, flags) -> bool:
        binary_data = "0b" + "".join([str(int(x)) for x in list(flags.values())[::-1]])
        print(f"flags binary data: {binary_data}")
        hex_data = format(int(binary_data, 2), "#04x")
        print(f"flags hex data: {hex_data}")
        return self._PSW.write(hex_data)

    def flags(self) -> dict:
        binary_data = self._PSW.bin()
        return {
            "P": bool(int(binary_data[9])),
            "_UD": bool(int(binary_data[8])),
            "OV": bool(int(binary_data[7])),
            "RS0": bool(int(binary_data[6])),
            "RS1": bool(int(binary_data[5])),
            "F0": bool(int(binary_data[4])),
            "AC": bool(int(binary_data[3])),
            "CY": bool(int(binary_data[2])),
        }

    def read(self) -> str:
        return self._PSW.read()

    def write(self, data: str) -> bool:
        self._PSW.write(data)
        return True

    def inspect(self) -> str:
        binary_data = self._PSW.bin()
        return textwrap.dedent(
            f"""
            Flags
            -----
            "P" \t: {bool(int(binary_data[9]))}
            "_UD" \t: {bool(int(binary_data[8]))}
            "OV" \t: {bool(int(binary_data[7]))}
            "RS0" \t: {bool(int(binary_data[6]))}
            "RS1" \t: {bool(int(binary_data[5]))}
            "F0" \t: {bool(int(binary_data[4]))}
            "AC" \t: {bool(int(binary_data[3]))}
            "CY" \t: {bool(int(binary_data[2]))}
            """
        )

    def get(self, _flag):
        return self.flags()[_flag]

    def items(self):
        return self.flags().items()

    def reset(self):
        return self._PSW.write("0x00")

    def set_flags(self, flags):
        return self._update_PSW(flags)

    def _setitem_flag(self, flag, val):
        _flags = self.flags()
        _flags.__setitem__(flag, bool(val))
        return self._update_PSW(_flags)

    def bit(self, value) -> str:
        _binary_data = self._PSW.bin()[2:]
        value = len(_binary_data) - value - 1
        if value < 0:
            raise MemoryError("Invalid bit address")
        return _binary_data[value]

    P = property(fget=lambda self: self.flags().get("P"), fset=lambda self, val: self._setitem_flag("P", val))
    _UD = property(fget=lambda self: self.flags().get("_UD"), fset=lambda self, val: self._setitem_flag("_UD", val))
    OV = property(fget=lambda self: self.flags().get("OV"), fset=lambda self, val: self._setitem_flag("OV", val))
    RS0 = property(fget=lambda self: self.flags().get("RS0"), fset=lambda self, val: self._setitem_flag("RS0", val))
    RS1 = property(fget=lambda self: self.flags().get("RS1"), fset=lambda self, val: self._setitem_flag("RS1", val))
    F0 = property(fget=lambda self: self.flags().get("F0"), fset=lambda self, val: self._setitem_flag("F0", val))
    AC = property(fget=lambda self: self.flags().get("AC"), fset=lambda self, val: self._setitem_flag("AC", val))
    CY = property(fget=lambda self: self.flags().get("CY"), fset=lambda self, val: self._setitem_flag("CY", val))

    pass


class StackPointer:
    def __init__(self, memory, addr, _bytes=1, _default="0x07", *args, **kwargs) -> None:
        self.memory = memory
        self._SP = LinkedRegister(memory, addr)
        self._SP.write(_default)
        self._memory_limit = 256
        self._base = 16
        self._bytes = _bytes
        self._format_spec = f"#0{2 + _bytes * 2}x"
        self._format_spec_bin = f"#0{2 + _bytes * 4}b"

    def __repr__(self) -> str:
        return str(self._SP)

    def __add__(self, val: int, *args, **kwargs) -> str:
        """
        val: `int`
        """
        data_int = int(str(self._SP), self._base) + val
        if data_int >= self._memory_limit:
            data_int -= self._memory_limit
        elif data_int < 0:
            data_int += self._memory_limit
        self._SP.write(format(data_int, self._format_spec))
        return self._SP

    def __sub__(self, val: int, *args, **kwargs) -> str:
        """
        val: `int`
        """
        data_int = int(str(self._SP), self._base) - val
        if data_int > self._memory_limit:
            data_int -= self._memory_limit
        elif data_int < 0:
            data_int += self._memory_limit
        self._SP.write(format(data_int, self._format_spec))
        return self._SP

    def __next__(self):
        return self.__add__(1)

    def read(self, *args, **kwargs) -> Byte:
        """POP rp"""
        data = self.memory.read(self._SP)
        self.__sub__(1)
        return data

    def write(self, data, *args) -> Byte:
        """PUSH DIRECT"""
        self.__next__()
        return self.memory.write(self._SP, data)


class SuperMemory:
    def __init__(self) -> None:
        self.memory_rom = Memory(4096, "0x0000")
        self.memory_ram = Memory(256, "0x00")

        self.A = LinkedRegister(self.memory_ram, "0xE0")
        self.B = LinkedRegister(self.memory_ram, "0xF0")
        self.SP = StackPointer(self.memory_ram, "0x81", _bytes=1)
        self.PC = ProgramCounter(self.memory_rom)
        self.DPTR = DataPointer(self.memory_ram, ["0x82", "0x83"])
        self.DPL = self.DPTR._DPL
        self.DPH = self.DPTR._DPH
        self.PSW = ProgramStatusWord(self.memory_ram, "0x0D0")
        self._define_general_purpose_registers()
        self._define_flag_bits()

    def __repr__(self) -> str:
        return "<SuperMemory>"

    def _define_flag_bits(self):
        """Method to define the `C` bit for the `CY` flag."""
        # Define `C` carry flag
        setattr(self.C.__func__, "bit_get", lambda *args: self.PSW.get("CY"))
        setattr(self.C.__func__, "bit_set", lambda val, *args: self.PSW._setitem_flag("CY", val))

    def _define_general_purpose_registers(self):
        self._general_purpose_registers = {
            "00": {f"R{i}": self.memory_ram[x] for i, x in enumerate(get_byte_sequence("0x00", 8))},
            "01": {f"R{i}": self.memory_ram[x] for i, x in enumerate(get_byte_sequence("0x08", 8))},
            "10": {f"R{i}": self.memory_ram[x] for i, x in enumerate(get_byte_sequence("0x10", 8))},
            "11": {f"R{i}": self.memory_ram[x] for i, x in enumerate(get_byte_sequence("0x18", 8))},
        }
        setattr(
            self.R0.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R0"),
        )
        setattr(
            self.R1.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R1"),
        )
        setattr(
            self.R2.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R2"),
        )
        setattr(
            self.R3.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R3"),
        )
        setattr(
            self.R4.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R4"),
        )
        setattr(
            self.R5.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R5"),
        )
        setattr(
            self.R6.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R6"),
        )
        setattr(
            self.R7.__func__,
            "read",
            lambda *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            ).get("R7"),
        )

        setattr(
            self.R0.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R0")
            .update(data),
        )
        setattr(
            self.R1.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R1")
            .update(data),
        )
        setattr(
            self.R2.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R2")
            .update(data),
        )
        setattr(
            self.R3.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R3")
            .update(data),
        )
        setattr(
            self.R4.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R4")
            .update(data),
        )
        setattr(
            self.R5.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R5")
            .update(data),
        )
        setattr(
            self.R6.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R6")
            .update(data),
        )
        setattr(
            self.R7.__func__,
            "write",
            lambda data, *args: self._general_purpose_registers.get(
                "".join([str(int(self.PSW.RS1)), str(int(self.PSW.RS0))])
            )
            .__getitem__("R7")
            .update(data),
        )

    def _reg_inspect(self):
        return textwrap.dedent(
            f"""
            Registers
            ---------
            A/PSW \t= {self.A} {self.PSW._PSW}
            B \t= {self.B}
            SP \t= {self.SP}
            PC \t= {self.PC}
            DPTR \t= {self.DPTR}

            Registers Bank
            --------------
            00 \t 01 \t 10 \t 11
            -- \t -- \t -- \t --
            {self._general_purpose_registers["00"]["R0"]} \t {self._general_purpose_registers["01"]["R0"]} \t {self._general_purpose_registers["10"]["R0"]} \t {self._general_purpose_registers["11"]["R0"]}
            {self._general_purpose_registers["00"]["R1"]} \t {self._general_purpose_registers["01"]["R1"]} \t {self._general_purpose_registers["10"]["R1"]} \t {self._general_purpose_registers["11"]["R1"]}
            {self._general_purpose_registers["00"]["R2"]} \t {self._general_purpose_registers["01"]["R2"]} \t {self._general_purpose_registers["10"]["R2"]} \t {self._general_purpose_registers["11"]["R2"]}
            {self._general_purpose_registers["00"]["R3"]} \t {self._general_purpose_registers["01"]["R3"]} \t {self._general_purpose_registers["10"]["R3"]} \t {self._general_purpose_registers["11"]["R3"]}
            {self._general_purpose_registers["00"]["R4"]} \t {self._general_purpose_registers["01"]["R4"]} \t {self._general_purpose_registers["10"]["R4"]} \t {self._general_purpose_registers["11"]["R4"]}
            {self._general_purpose_registers["00"]["R5"]} \t {self._general_purpose_registers["01"]["R5"]} \t {self._general_purpose_registers["10"]["R5"]} \t {self._general_purpose_registers["11"]["R5"]}
            {self._general_purpose_registers["00"]["R6"]} \t {self._general_purpose_registers["01"]["R6"]} \t {self._general_purpose_registers["10"]["R6"]} \t {self._general_purpose_registers["11"]["R6"]}
            {self._general_purpose_registers["00"]["R7"]} \t {self._general_purpose_registers["01"]["R7"]} \t {self._general_purpose_registers["10"]["R7"]} \t {self._general_purpose_registers["11"]["R7"]}

            """
        )

    def _registers_todict(self):
        return {
            "A/PSW": f"{self.A} {self.PSW._PSW}",
            "B": f"{self.B}",
            "SP": f"{self.SP}",
            "PC": f"{self.PC}",
            "DPTR": f"{self.DPTR}",
        }

    def A(self):
        pass

    def B(self):
        pass

    def R0(self):
        pass

    def R1(self):
        pass

    def R2(self):
        pass

    def R3(self):
        pass

    def R4(self):
        pass

    def R5(self):
        pass

    def R6(self):
        pass

    def R7(self):
        pass

    def C(self):
        pass

    def inspect(self):
        return "\n\n".join(
            [
                self.PSW.inspect(),
                self._reg_inspect(),
                "\nRAM",
                str(self.memory_ram.sort()),
                "\nROM",
                str(self.memory_rom.sort()),
            ]
        )

    pass
