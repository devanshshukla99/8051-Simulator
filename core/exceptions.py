class SyntaxError(Exception):
    def __init__(self, msg="invalid syntax") -> None:
        super().__init__(msg)


class OPCODENotFound(Exception):
    def __init__(self, opcode, msg="is an invalid opcode") -> None:
        exception_msg = f"`{opcode}` {msg}"
        super().__init__(exception_msg)


class MemoryLimitExceeded(Exception):
    def __init__(self, msg="Memory limit exceeded") -> None:
        super().__init__(msg)


class InvalidMemoryAddress(Exception):
    def __init__(self, msg="Invalid memory address") -> None:
        super().__init__(msg)


class ValueErrorHexRequired(ValueError):
    def __init__(self, value, msg="invalid valid; only hex supported!") -> None:
        super().__init__(f"{msg}({value})")
