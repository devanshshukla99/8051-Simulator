from rich.console import Console

from core.exceptions import OPCODENotFound, SyntaxError
from core.memory import Byte, SuperMemory
from core.opcodes import opcodes_lookup
from core.util import decompose_byte, tohex


class Operations:
    def __init__(self) -> None:
        self.console = Console()
        self.super_memory = SuperMemory()
        self.memory_rom = self.super_memory.memory_rom
        self.memory_ram = self.super_memory.memory_ram
        self.flags = self.super_memory.PSW
        self.flags.reset()
        self.super_memory.PC("0x0000")
        self._registers_list = {
            "A": self.super_memory.A,  # Accumulator
            "ACC": self.super_memory.A,  # Accumulator
            "PSW": self.flags._PSW,  # Program Status Word
            "B": self.super_memory.B,  # Register B
            "C": self.super_memory.C,
            "SP": self.super_memory.SP,  # Stack Pointer
            "PC": self.super_memory.PC,  # Program Counter
            "DPL": self.super_memory.DPTR,  # Data pointer low
            "DPH": self.super_memory.DPTR,  # Data pointer high
            "DPTR": self.super_memory.DPTR,  # Data pointer
            "R0": self.super_memory.R0,
            "R1": self.super_memory.R1,
            "R2": self.super_memory.R2,
            "R3": self.super_memory.R3,
            "R4": self.super_memory.R4,
            "R5": self.super_memory.R5,
            "R6": self.super_memory.R6,
            "R7": self.super_memory.R7,
        }
        # General purpose registers
        self._register_banks = self.super_memory._general_purpose_registers
        self._lookup_opcodes_dir = opcodes_lookup

        self._keywords = []
        self._generate_keywords()
        self._assembler = {}
        self._internal_PC = []

        # Jump instructions
        self._jump_instructions = [
            "SJMP",
            "AJMP",
            "LJMP",
            "JMP",
            "JC",
            "JNC",
            "JB",
            "JNB",
            "JBC",
            "JZ",
            "JNZ",
            "DJNZ",
            "CJNE",
        ]  # Add later
        pass

    def _generate_keywords(self):
        _keywords = [*self._lookup_opcodes_dir.keys(), *self._registers_list.keys()]
        for key in _keywords:
            self._keywords.extend(key.split(" "))
        self._keywords = set(self._keywords)
        return

    def iskeyword(self, arg):
        """
        opcodes + registers
        """
        if arg.upper() in self._keywords:
            return True
        return False

    def inspect(self):
        return self.super_memory.inspect()

    def _parse_addr(self, addr):
        addr = addr.upper()
        return self._registers_list.get(addr, None)

    def _get_register(self, addr):
        addr = addr.upper()
        _register = self._registers_list.get(addr, None)
        if _register:
            return _register
        raise SyntaxError(msg="next link not found; check the instruction")

    def _opcode_fetch(self, opcode, *args, **kwargs) -> None:
        # _args_params = [x for x in args if self.iskeyword(x)]
        _args_params = []
        _args_hexs = []
        for x in args:
            if self.iskeyword(x) or self.iskeyword(x[1:]):
                if x[0] == "@":
                    print("Register indirect")
                    _args_params.append(x)
                elif x == "B":
                    print("B")
                    _args_params.append("DIRECT")
                    _args_hexs.append(["0xF0"])  # memory location for `B`
                else:
                    _args_params.append(x)
            else:
                print(f"`{x}` not a key word")
                if x[0] == "#":  # immediate
                    x = x[1:]
                    print("#immed")
                    _args_params.append("#IMMED")
                    _args_hexs.append(decompose_byte(tohex(x)))
                elif "." in x:
                    print("bit")
                    _args_params.append("BIT")
                else:
                    print("direct")
                    _args_params.append("DIRECT")
                    if opcode not in self._jump_instructions:
                        _args_hexs.append(decompose_byte(tohex(x)))

        print(_args_params)
        print(_args_hexs)

        _opcode_search_params = " ".join([opcode, *_args_params]).upper()
        _opcode_hex = self._lookup_opcodes_dir.get(_opcode_search_params)
        self.console.log(f"OPCODE: {_opcode_search_params} = {_opcode_hex}")
        if _opcode_hex:
            if _opcode_hex == "0xFFFFFFDB":  # trick to accomodate database directives
                _opcode_hex = None
            return _opcode_hex, _args_hexs
        raise OPCODENotFound(" ".join([opcode, *args]))

    def prepare_operation(self, command: str, opcode: str, *args, **kwargs) -> bool:
        _opcode_hex, _args_hex = self._opcode_fetch(opcode, *args)
        if not _opcode_hex:
            """Database directive"""
            self.console.log("Database directive")
            self._internal_PC.append([])
            return True

        self._internal_PC.append([[_opcode_hex], *_args_hex])
        _assembler = [_opcode_hex]
        for x in _args_hex:
            for y in x[::-1]:
                _assembler.append(y)
        self._assembler[command] = " ".join(_assembler).lower()
        return True

    def memory_read(self, addr: str, RAM: bool = True) -> Byte:
        print(f"memory read {addr}")
        _parsed_addr = self._parse_addr(addr)
        if _parsed_addr:
            return _parsed_addr.read(addr)
        if RAM:
            return self.memory_ram.read(addr)
        return self.memory_rom.read(addr)

    def memory_write(self, addr: str, data, RAM: bool = True) -> bool:
        addr = str(addr)
        print(f"memory write {addr}|{data}")
        _parsed_addr = self._parse_addr(addr)
        if _parsed_addr:
            if addr == "SP":
                return _parsed_addr._SP.write(data)
            return _parsed_addr.write(data, addr)
        if RAM:
            return self.memory_ram.write(addr, data)
        return self.memory_rom.write(addr, data)

    def bit_read(self, addr: str) -> bool:
        bit = None
        if "." in addr:
            addr, bit = addr.split(".")
        _parsed_addr = self._parse_addr(addr)
        if _parsed_addr:
            print(addr, _parsed_addr)
            if bit:
                return _parsed_addr.bit_get(bit)
            return _parsed_addr.bit_get()
        return False

    def bit_write(self, addr: str, val: str) -> bool:
        bit = None
        if "." in addr:
            addr, bit = addr.split(".")
        _parsed_addr = self._parse_addr(addr)
        if _parsed_addr:
            print(addr, _parsed_addr)
            if bit:
                return _parsed_addr.bit_set(bit, val)
            return _parsed_addr.bit_set(val)
        return False

    def register_pair_read(self, addr) -> Byte:
        print(f"register pair read {addr}")
        _register = self._get_register(addr)
        data = _register.read_pair()
        # self._write_opcode(data)
        return data

    def register_pair_write(self, addr, data) -> bool:
        print(f"register pair write {addr}|{data}")
        _register = self._get_register(addr)
        _register.write_pair(data)
        return True

    pass
