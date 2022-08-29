import textwrap

from core.basic_memory import Hex


class JumpFlag:
    def __init__(self, label: str, counter: str, command, *args, **kwargs) -> None:
        self._label = label.upper()
        self._counter = Hex(str(counter), _bytes=2)
        self._command = command
        self._endpoint = ""

    def __repr__(self) -> str:
        return f"<command:{self._command} label:{self._label} counter:{self._counter} endpoint:{self._endpoint}>"

    def __eq__(self, val: object) -> bool:
        return self._label == val.upper()

    def __bool__(self) -> bool:
        return bool(self._label)

    def match(self, label: str) -> bool:
        return label.upper() == self._label

    def upper(self) -> str:
        return self._label.upper()

    pass


class Flags:
    def __init__(self) -> None:
        raise DeprecationWarning("USE core.memory.ProgramStatusWord instead")
        self._flags = {
            "P": False,  # D0
            "_UD": False,  # D1 = UserDefined
            "OV": False,  # D2 = Overflow
            "RS0": False,  # D3 = Register bank selector
            "RS1": False,  # D4 = Register bank selector
            "F0": False,  # D5 = available for general purpose
            "AC": False,  # D6 = Aux Carry
            "CY": False,  # D7 = Carry
        }

    def __repr__(self):
        return self.inspect()

    def __getitem__(self, key):
        return self._flags[key]

    def __setitem__(self, key, val):
        self._flags[key] = val

    def set_flags(self, flags_dict):
        for key, val in flags_dict.items():
            self._flags.__setitem__(key, val)
        return True

    def todict(self):
        return self._flags

    def items(self):
        return self._flags.items()

    def reset(self):
        for _k in self._flags.keys():
            self._flags.__setitem__(_k, False)
        return True

    def inspect(self):
        return textwrap.dedent(
            f"""
            Flags
            -----
            "P" \t: {self.P}
            "_UD" \t: {self._UD}
            "OV" \t: {self.OV}
            "RS0" \t: {self.RS0}
            "RS1" \t: {self.RS1}
            "F0" \t: {self.F0}
            "AC" \t: {self.AC}
            "CY" \t: {self.CY}
            """
        )

    @property
    def PSW(self):
        _psw_binary = ""
        for _, value in self._flags.items():
            _psw_binary += format(value, "0b")
        print(f"bin={_psw_binary}")
        return format(int(_psw_binary, 2), "#04x")

    @PSW.setter
    def PSW(self, val):
        print(f"settings psw {val}")
        _psw_binary = format(int(val, 16), "08b")
        print(f"bin={_psw_binary}")
        for i, keys in enumerate(self._flags.keys()):
            self._flags[keys] = _psw_binary[7 - i]
        return True

    P = property(fget=lambda self: self._flags.get("P"), fset=lambda self, val: self._flags.__setitem__("P", val))
    _UD = property(fget=lambda self: self._flags.get("_UD"), fset=lambda self, val: self._flags.__setitem__("_UD", val))
    OV = property(fget=lambda self: self._flags.get("OV"), fset=lambda self, val: self._flags.__setitem__("OV", val))
    RS0 = property(fget=lambda self: self._flags.get("RS0"), fset=lambda self, val: self._flags.__setitem__("RS0", val))
    RS1 = property(fget=lambda self: self._flags.get("RS1"), fset=lambda self, val: self._flags.__setitem__("RS1", val))
    F0 = property(fget=lambda self: self._flags.get("F0"), fset=lambda self, val: self._flags.__setitem__("F0", val))
    AC = property(fget=lambda self: self._flags.get("AC"), fset=lambda self, val: self._flags.__setitem__("AC", val))
    CY = property(fget=lambda self: self._flags.get("CY"), fset=lambda self, val: self._flags.__setitem__("CY", val))

    pass


# flags = Flags()
