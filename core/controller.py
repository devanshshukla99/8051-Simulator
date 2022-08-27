import re
import inspect

from rich.console import Console

from core.exceptions import OPCODENotFound
from core.flags import JumpFlag
from core.instruction_set import Instructions
from core.operations import Operations
from core.util import decompose_byte, ishex, tohex


class Controller:
    def __init__(self, console=None) -> None:
        self.console = console
        if not console:
            self.console = Console()
        # operations
        self.op = Operations()
        # instruction set
        self._jump_flag = False
        self._address_jump_flag = None
        self.instruct_set = Instructions(self.op)
        self.lookup = {
            name.upper(): call
            for name, call in inspect.getmembers(self.instruct_set, inspect.ismethod)
            if "_" not in name
        }
        # callstack
        self._callstack = []
        self.ready = False
        self._jump_methods = ["JNC", "JNZ", "JC"]
        self._wrap_bounceable_methods()
        self._run_idx = 0
        return

    def __repr__(self):
        return f"{self.op.inspect()}\n{self.__callstackrepr__()}"

    def __callstackrepr__(self) -> str:
        return f"<CallStack calls={len(self._callstack)}>"

    def _wrap_bounceable_methods(self):
        """
        Wrap the jump-ing methods with `Controller._skipper`
        """
        for key in self._jump_methods:
            self.lookup[key] = self._skipper(self.lookup.get(key))
        return True

    def _skipper(self, func):
        """
        Wrapper for jump-ing methods
        """

        def _func(*args, **kwargs):
            kwargs["bounce_to_label"] = self._bounce_to_label
            return func(*args, **kwargs)

        return _func

    def _bounce_to_label(self, label):
        idx, _ = self._locate_jump_label(label)
        print(f"JUMPING to {idx}")
        self._run_idx = idx
        return True

    def _call(self, func, *args, **kwargs) -> bool:
        return func(*args)

    def _get_jump_flags(self) -> list:
        return [x[2] for x in self._callstack if x[2]]

    def _locate_jump_label(self, label, key="label") -> tuple:
        label = label.upper()
        for idx, x in enumerate(self._callstack):
            key_label = x[3].get(key, None)
            if key_label:
                if key_label == label:
                    return idx, x
        return None, None

    def _target_label(self, label) -> bool:
        print(f"======={label}========")
        idx_t, x_t = self._locate_jump_label(label, key="target-label")
        idx_l, x_l = self._locate_jump_label(label)
        if x_t:
            if x_l:
                _target_label = x_t[3].get("target-label")
                _jump_label = x_l[3].get("label")
                print(f"!YES! PC: {_jump_label._counter + 2}")
                print(f"{_target_label._counter} {_target_label._counter}")
                _data_to_write = decompose_byte(str(_jump_label._counter))
                self.op.memory_write(str(_target_label._counter + 1), _data_to_write[1])
                self.op.memory_write(str(_target_label._counter + 2), _data_to_write[0])
                _assembler = self.op._assembler[_target_label._command].replace("0xff", "").strip()
                self.op._assembler[_target_label._command] = " ".join(
                    [_assembler, _data_to_write[1], _data_to_write[0]]
                )
        return

    def inspect(self):
        return self.console.print(self.__repr__())

    def _lookup_opcode_func(self, opcode):
        func = self.lookup.get(opcode)
        if func:
            return func
        raise OPCODENotFound

    @property
    def callstack(self) -> list:
        return self._callstack

    def _addjob(self, opcode: str, func, args: tuple = (), kwargs: dict = {}) -> bool:
        for idx, val in enumerate(args):
            if ishex(val):
                args[idx] = tohex(val)
        self._callstack.append((opcode, func, args, kwargs))
        return True

    def _parser(self, command, *args, **kwargs) -> tuple:
        command = command.strip()
        if not command:
            return None, None
        if command[0] == "#":  # Directive
            command = command[1:]

        match = re.match("^[a-zA-Z]+:", command)
        if match:
            label = match.group()[:-1]
            kwargs["label"] = JumpFlag(label, self.op.super_memory.PC, command)
            return self._parser(command.replace(f"{label}:", ""), *args, **kwargs)

        _proc_command = re.split(r",| ", command)
        for _ in range(_proc_command.count("")):
            _proc_command.remove("")
        opcode = _proc_command[0]
        args = _proc_command[1:]
        return opcode.upper(), args, kwargs

    def parse(self, command):
        self.console.log(command)
        opcode, args, kwargs = self._parser(command)
        if self.instruct_set._is_jump_opcode(opcode):
            # if JNZ | JC | etc ** kwargs the target-label **
            kwargs["target-label"] = JumpFlag(args[0], self.op.super_memory.PC, command)
            args.extend(["0xff", "0xff"])  # placeholder
        opcode_func = self._lookup_opcode_func(opcode)
        self._addjob(opcode, opcode_func, args, kwargs)
        self.op.prepare_operation(command, opcode, *args)
        """
        JNC ZO      ----   Target label
        ...
        ZO: ...     ----    Label


        The function should execute at both commands; if `target-label` or `label` then look for
        `target-label` and `label`;
        if `target-lable` is found then replace the placeholder obtained using the `PC` in `label`
        """
        _label = kwargs.get("target-label", kwargs.get("label", None))
        if _label:
            self._target_label(_label)

        self.ready = True
        return True

    def parse_all(self, commands):
        for command in commands.split("\n"):
            if command:
                self.parse(command)
        return True

    def run_once(self):
        if self._run_idx >= len(self._callstack):
            return False
        try:
            self.console.log(self._callstack[self._run_idx])
            opcode, func, args, kwargs = self._callstack[self._run_idx]
            self._run_idx += 1
            print(self._run_idx)
            self._call(func, *args, **kwargs)
        except StopIteration:
            pass
        return True

    def run(self):
        while self._run_idx < len(self._callstack):
            val = self._callstack[self._run_idx]
            self._run_idx += 1
            # try:
            # print(f"{self._run_idx} -- {val} ", end="")
            opcode, func, args, kwargs = val
            self._call(func, *args, **kwargs)
            # except StopIteration:
            #     pass
        return True

    def set_flag(self, key, val):
        self.op.flags[key] = val
        return True

    def set_flags(self, *args, **kwargs):
        return self.op.flags.set_flags(*args, **kwargs)

    def reset(self) -> bool:
        self.__init__(console=self.console)
        return True

    def reset_callstack(self) -> None:
        self._callstack = []
        self._run_idx = 0
        self.op._assembler = {}
        return True

    pass
