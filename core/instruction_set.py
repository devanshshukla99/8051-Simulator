import warnings
from core.flags import flags
from core.util import decompose_byte, twos_complement


class Instructions:
    def __init__(self, op) -> None:
        self.op = op
        self._jump_flag = False
        self._jump_instructions = []  # Add later
        self._base = 16
        pass

    def _is_jump_opcode(self, opcode) -> bool:
        opcode = opcode.upper()
        if opcode not in self._jump_instructions:
            return False
        return True

    def _next_addr(self, addr) -> str:
        return format(int(str(addr), 16) + 1, "#06x")

    def _check_carry(self, data_1, data_2, og2, add=True, _AC=True, _CY=True) -> None:
        """
        Method to check both `CY` and `AC` flags.

        `aux_data` are the LSB of the two data to be added
        For example: for `0x11` and `0xae`, `aux_data=["0x1", "0xe"]`
        """
        decomposed_data_1 = decompose_byte(data_1, nibble=True)
        decomposed_data_2 = decompose_byte(data_2, nibble=True)
        carry_data, aux_data = list(zip(decomposed_data_1, decomposed_data_2))

        if _AC:
            flags.AC = False
            if (int(aux_data[0], 16) + int(aux_data[1], 16)) >= 16:
                print("AUX FLAG")
                flags.AC = True

        if not _CY:
            return

        if not add:
            flags.C = False
            if int(str(data_1), 16) < int(str(og2), 16):
                print("CARRY FLAG-")
                flags.CY = True
        return

    def _check_parity(self, data_bin: str) -> None:
        flags.P = False
        _count_1s = data_bin.count("1")
        if not _count_1s % 2:
            flags.P = True
            print("PARITY")
        return

    def _check_overflow(self, data_bin: str) -> None:
        flags.OV = False
        if int(data_bin[0]):
            flags.OV = True
            print("SIGN")
        return

    def _check_flags(self, data_bin, _P=True, _OV=True) -> bool:
        if _P:
            self._check_parity(data_bin)
        if _OV:
            self._check_overflow(data_bin)
        return True

    def _check_flags_and_compute(self, data_1, data_2, add=True, _AC=True, _CY=True, _P=True, _OV=True):
        og2 = data_2
        if not add:
            data_2 = twos_complement(str(data_2))

        result = int(str(data_1), 16) + int(str(data_2), 16)
        if result > 255:
            if _CY:
                flags.CY = True
                print("CARRY FLAG+")
            result -= 256
        result_hex = format(result, "#04x")
        data_bin = format(result, "08b")

        self._check_carry(data_1, data_2, og2, add=add, _AC=_AC, _CY=_CY)
        self._check_flags(data_bin, _P=_P, _OV=_OV)
        return result_hex

    def mov(self, addr, data) -> bool:
        if data[0] != "#":  # Direct addressing
            data = self.op.memory_read(data)
        else:
            data = data[1:]
        return self.op.memory_write(addr, data)
