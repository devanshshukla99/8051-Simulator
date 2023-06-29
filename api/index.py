import json

from flask import Flask, make_response, render_template, request

from core.controller import Controller
from core.util import fill_memory

# from core.flags import flags

CLEAR_TOKEN = "batman"
app = Flask(__name__, static_folder="static")
controller = Controller()

app.jinja_env.globals.update(zip=zip)


def _get_ram_and_rom():
    _memory_ram, _memory_rom = None, None
    _ram = fill_memory(controller.op.memory_ram, 256).sort()
    if _ram:
        _ram = list(_ram.items())
        _memory_ram = [_ram[x : x + 16] for x in range(0, len(_ram), 16)]

    _rom = fill_memory(controller.op.memory_rom, 256).sort()
    if _rom:
        _rom = list(_rom.items())
        _memory_rom = [_rom[x : x + 16] for x in range(0, len(_rom), 16)]

    # print(f"RAM:{_memory_ram}; ROM:{_memory_rom}")
    return _memory_ram, _memory_rom


@app.route("/reset", methods=["POST"])
def reset():
    global controller
    controller.reset()
    ram, rom = _get_ram_and_rom()
    return {
        "registers_flags": render_template(
            "render_registers_flags.html",
            registers=controller.op.super_memory._registers_todict(),
            flags=controller.op.super_memory.PSW.flags(),
            general_purpose_registers=controller.op.super_memory._general_purpose_registers,
        ),
        "memory": render_template("render_memory.html", ram=ram, rom=rom),
        "assembler": render_template("render_assembler.html", assembler=controller.op._assembler),
    }


@app.route("/assemble", methods=["POST"])
def assemble():
    global controller
    commands_json = request.data
    if commands_json:
        commands_dict = json.loads(commands_json)
        _commands = commands_dict.get("code", None)
        _flags = commands_dict.get("flags", None)
        if _commands and _flags:
            try:
                controller.set_flags(_flags)
                controller.parse_all(_commands)
                ram, rom = _get_ram_and_rom()
                print("PASSED")
                return render_template("render_memory.html", ram=ram, rom=rom)
            except Exception as e:
                print(e)
                return make_response(f"Exception raised {e}", 400)
    return make_response("Record not found", 400)


@app.route("/run", methods=["POST"])
def run():
    global controller
    print(controller.ready)
    if controller.ready:
        try:
            controller.run()
            ram, rom = _get_ram_and_rom()
            controller.inspect()
            return {
                "registers_flags": render_template(
                    "render_registers_flags.html",
                    registers=controller.op.super_memory._registers_todict(),
                    flags=controller.op.super_memory.PSW.flags(),
                    general_purpose_registers=controller.op.super_memory._general_purpose_registers,
                ),
                "memory": render_template("render_memory.html", ram=ram, rom=rom),
                "assembler": render_template("render_assembler.html", assembler=controller.op._assembler),
            }

        except Exception as e:
            print(e)
            return make_response(f"Exception raised {e}", 400)
    return make_response("Controller not ready", 400)


@app.route("/run-once", methods=["POST"])
def step():
    global controller
    print(controller.ready)
    if controller.ready:
        try:
            controller.run_once()
            ram, rom = _get_ram_and_rom()
            return {
                "index": controller._run_idx,
                "registers_flags": render_template(
                    "render_registers_flags.html",
                    registers=controller.op.super_memory._registers_todict(),
                    flags=controller.op.super_memory.PSW.flags(),
                    general_purpose_registers=controller.op.super_memory._general_purpose_registers,
                ),
                "memory": render_template("render_memory.html", ram=ram, rom=rom),
                "assembler": render_template("render_assembler.html", assembler=controller.op._assembler),
            }
        except Exception as e:
            print(e)
            return make_response(f"Exception raised {e}", 400)
    return make_response("Controller not ready", 400)


@app.route("/memory-edit", methods=["POST"])
def update_memory():
    global controller
    mem_data = request.data
    if mem_data:
        mem_data = json.loads(mem_data)
        print(mem_data)
        try:
            for memloc, memdata in mem_data:
                print("=============================")
                print(memloc, memdata)
                controller.op.memory_ram.write(memloc, memdata)
            ram, rom = _get_ram_and_rom()
            return {
                "index": controller._run_idx,
                "registers_flags": render_template(
                    "render_registers_flags.html",
                    registers=controller.op.super_memory._registers_todict(),
                    flags=controller.op.super_memory.PSW.flags(),
                    general_purpose_registers=controller.op.super_memory._general_purpose_registers,
                ),
                "memory": render_template("render_memory.html", ram=ram, rom=rom),
                "assembler": render_template("render_assembler.html", assembler=controller.op._assembler),
            }
        except Exception as e:
            print(e)
            return make_response(f"Exception raised {e}", 400)
    return make_response("Controller not ready", 400)


@app.route("/", methods=["GET"])
def main():
    global controller
    controller = Controller()
    ram, rom = _get_ram_and_rom()
    return render_template(
        "index.html",
        ram=ram,
        rom=rom,
        registers=controller.op.super_memory._registers_todict(),
        general_purpose_registers=controller.op.super_memory._general_purpose_registers,
        flags=controller.op.super_memory.PSW.flags(),
    )
