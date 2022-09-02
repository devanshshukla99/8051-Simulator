import re
from copy import copy


def twos_complement(num, _base=16):
    """
    Helper method to compure 2's complement of a hex value
    """
    _bytes = int(len(format(int(num, _base), "x")) / 2) or 1
    return format((1 << 8 * _bytes) - int(num, _base), f"#0{2 + _bytes*2}x")


def comparehex(hex1, hex2):
    """
    Helper method to compare two hex values
    """
    if int(str(hex1), 16) == int(str(hex2), 16):
        return True
    return False


def tohex(data):
    """
    Helper method to convert multiple patterns (`0x12`, `0X12`, `12H` and `12h`) into
    a single standard pattern
    """
    match = re.fullmatch(r"^0[x|X][0-9a-fA-F]+", data)
    if match:
        return data.lower()
    match = re.fullmatch(r"^[0-9a-fA-F]+[h|H]$", data)
    if match:
        return f"0x{match.group().lower()[:-1]}"
        # raise ValueError(f"Required hex of the form `0x` or `H` found {data}")
    match = re.match(r"^[0-9a-fA-F]+", data)
    return f"0x{match.group().lower()}"


def ishex(data):
    """
    Helper method to check if the value is hex or not
    """
    if (
        bool(re.fullmatch(r"^0[x|X][0-9a-fA-F]+", data))
        or bool(re.fullmatch(r"^[0-9a-fA-F]+[h|H]$", data))
        or bool(re.fullmatch(r"^[0-9a-fA-F]+", data))
    ):
        return True
    return False


def sanatize_hex(data):
    """
    Helper method to sanatize hex value
    """
    return data.replace("0x", "").replace("0X", "")


def decompose_byte(data, nibble=False):
    """
    Helper method to decompose hex into bytes/nibbles
    """
    _bytes = int(len(sanatize_hex(data)) / 2)
    mem_size = 8
    if nibble:
        mem_size = 4
    binary_data = format(int(str(data), 16), f"0{_bytes*8}b")
    return [
        format(int(binary_data[mem_size * x : mem_size * (x + 1)], 2), f"#0{int(mem_size/2)}x")
        for x in range(0, int(len(binary_data) / mem_size))
    ]


def get_bytes(data):
    """
    Helper method to get the no. of bytes in the hex"""
    data = str(data)
    return int(len(sanatize_hex(data)) / 2)


def construct_hex(hex1, hex2, _bytes=2):
    """
    Helper method to construct hex from two decomposed hex values
    """
    bin1 = format(int(str(hex1), 16), f"0{_bytes * 4}b")
    bin2 = format(int(str(hex2), 16), f"0{_bytes * 4}b")
    bin_total = "".join(["0b", bin1, bin2])
    return f'0x{format(int(bin_total, 2), f"0{_bytes * 2}x")}'


def get_byte_sequence(start, size, _bytes=1) -> list:
    _ret_array = []
    _hex_val = start
    for _ in range(0, size):
        _ret_array.append(_hex_val)
        _hex_val = format(int(_hex_val, 16) + 1, f"#0{_bytes * 2 + 2}x")
    return _ret_array


def fill_memory(memory, size) -> dict:
    copied_memory = copy(memory)
    for i in range(0, size):
        iH = format(i, "#06x")
        if iH not in copied_memory:
            copied_memory.get(iH)
    return copied_memory


def hexconvert(value: str) -> str:
    if re.fullmatch(r"^[0-9a-fA-F]+[h|H]$", str(value)):
        new_val = "0x" + str(value)[:-1]
        print(f"converted: {value} -> {new_val}")
        return new_val
    return value
