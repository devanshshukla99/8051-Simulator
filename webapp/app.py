import json

from flask import Flask, make_response, render_template, request

from core.controller import Controller
from core.flags import flags

CLEAR_TOKEN = "batman"
app = Flask(__name__, static_folder="static")
controller = Controller()


@app.route("/reset", methods=["POST"])
def reset():
    global controller
    controller.reset()
    return {
        "registers_flags": render_template(
            "render_registers_flags.html", registers=controller.op.super_memory._registers_todict(), flags=flags
        ),
        "memory": render_template("render_memory.html", memory=controller.op.memory),
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
                return render_template("render_memory.html", memory=controller.op.memory)
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
            return {
                "registers_flags": render_template(
                    "render_registers_flags.html", registers=controller.op.super_memory._registers_todict(), flags=flags
                ),
                "memory": render_template("render_memory.html", memory=controller.op.memory),
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
            return {
                "index": controller._run_idx,
                "registers_flags": render_template(
                    "render_registers_flags.html", registers=controller.op.super_memory._registers_todict(), flags=flags
                ),
                "memory": render_template("render_memory.html", memory=controller.op.memory),
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
                controller.op.memory_write(memloc, memdata)

            return {
                "index": controller._run_idx,
                "registers_flags": render_template(
                    "render_registers_flags.html", registers=controller.op.super_memory._registers_todict(), flags=flags
                ),
                "memory": render_template("render_memory.html", memory=controller.op.memory),
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
    return render_template(
        "index.html",
        memory=controller.op.memory,
        registers=controller.op.super_memory._registers_todict(),
        flags=flags,
    )
