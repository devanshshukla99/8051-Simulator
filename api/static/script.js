window.onload = function () {
    console.log("load");
    // reload code contents
    document.getElementById("code").value = localStorage.getItem("code");

    document.getElementById("run").disabled = true;
    document.getElementById("step").disabled = true;

    document.getElementById("assemble").addEventListener("click", function () {
        console.log("assemble")
        const request = new XMLHttpRequest();
        request.open("POST", `/assemble`);
        request.onload = () => {
            const response = request.responseText;
            if (request.status != 200) {
                alert(response)
            }
            else {
                document.getElementById("run").disabled = false
                document.getElementById("step").disabled = false
                document.getElementById("memory-container").innerHTML = response;
                ProgressSideBar(_code, 0)
            }
        };
        var _code = document.getElementById("code").value.trim();
        if (_code) {
            // save code
            localStorage.setItem("code", _code)
            console.log("sent")
            request.send(JSON.stringify(
                {
                    "code": _code,
                    "flags": GetFlags()
                }
            ));
        }
    });

    document.getElementById("run").addEventListener("click", function () {
        console.log("run");
        const request = new XMLHttpRequest();
        request.open("POST", `/run`);
        request.onload = () => {
            const response = request.responseText;
            if (request.status != 200) {
                alert(response);
            }
            else {
                const _resp_dict = JSON.parse(response)
                document.getElementById("registers-flags").innerHTML = _resp_dict["registers_flags"];
                document.getElementById("memory-container").innerHTML = _resp_dict["memory"];
                document.getElementById("assembler-container").innerHTML = _resp_dict["assembler"];
                ProgressSideBar(_code, _code.split("\n").filter(Boolean).length)
            }
        };
        var _code = document.getElementById("code").value.trim();
        request.send(_code);
    });

    document.getElementById("step").addEventListener("click", function () {
        console.log("step");
        const request = new XMLHttpRequest();
        request.open("POST", `/run-once`);
        request.onload = () => {
            const response = request.responseText;
            if (request.status != 200) {
                AlertProgressSideBar()
                alert(response)
            }
            else {
                const _resp_dict = JSON.parse(response)
                index = _resp_dict["index"];
                document.getElementById("registers-flags").innerHTML = _resp_dict["registers_flags"];
                document.getElementById("memory-container").innerHTML = _resp_dict["memory"];
                document.getElementById("assembler-container").innerHTML = _resp_dict["assembler"];
                document.getElementById("code").value = _code;
                ProgressSideBar(_code, index)
            }
        };
        var _code = document.getElementById("code").value.trim();
        request.send(_code);
    });

    document.getElementById("reset").addEventListener("click", function () {
        console.log("reset")
        const request = new XMLHttpRequest();
        request.open("POST", `/reset`);
        request.onload = () => {
            const response = request.responseText;
            if (request.status != 200) {
                alert(response)
            }
            else {
                const _resp_dict = JSON.parse(response)
                document.getElementById("registers-flags").innerHTML = _resp_dict["registers_flags"];
                document.getElementById("memory-container").innerHTML = _resp_dict["memory"];
                document.getElementById("assembler-container").innerHTML = _resp_dict["assembler"];
                document.getElementById("run").disabled = true
                document.getElementById("step").disabled = true
                document.getElementById("track").textContent = ""

            }
        };
        request.send();
    });

    // memory-edit EventListener
    document.getElementById("memory_edit_input").addEventListener("keyup", event => {
        if (event.key === "Enter") {
            event.preventDefault();
            _mem_edit = ProcessMemEdit(event.target.value)
            if (!_mem_edit) {
                alert("invalid")
            }
            const request = new XMLHttpRequest();
            request.open("POST", `/memory-edit`);
            request.onload = () => {
                const response = request.responseText;
                if (request.status != 200) {
                    alert(response)
                }
                else {
                    const _resp_dict = JSON.parse(response)
                    index = _resp_dict["index"];
                    document.getElementById("registers-flags").innerHTML = _resp_dict["registers_flags"];
                    document.getElementById("memory-container").innerHTML = _resp_dict["memory"];
                    document.getElementById("assembler-container").innerHTML = _resp_dict["assembler"];
                }
            }
            request.send(JSON.stringify(_mem_edit));
        }
    });
    var footer = document.querySelector("header");
    if (footer) {
        footer.innerHTML = ``
    }
}

function GetFlags() {
    var flags_dict = {}
    document.querySelectorAll(".flag-input").forEach(element => {
        flags_dict[element.id] = element.checked
    });
    return flags_dict
}
function AlertProgressSideBar() {
    var track = document.getElementById("track");
    _track = track.textContent.trim().split("\n")
    _track[_track.length - 1] = "❌\n"
    track.textContent = _track.join("\n")
}
function ProgressSideBar(code, index) {
    var track = document.getElementById("track");
    code_split = code.split("\n")
    console.log(index, code, code_split.length)
    track.textContent = ""
    for (let i = 0; i < index; i++) {
        if (code_split[i] === "") {
            console.log("skip `" + code_split[i] + "`", i)
            i += 1
            track.textContent += "\n"
        }
        track.textContent += "✔\n"
        console.log(i, code_split[i])
    }
    if (index < code_split.length) {
        track.textContent += "▶"
    }
}
function ParseHex(data) {
    if (data.match("0[x|X][a-fA-F0-9]+")) {
        return data
    }
    else if (data.match("[a-fA-F0-9]+H$")) {
        _match = data.match("[a-fA-F0-9]+")[0]
        return "0x" + _match
    }
    return "0x" + data
}
function ProcessMemEdit(data) {
    // check if range => randomize
    if (data.includes(":")) {
        data = data.split(":")
        _data = []
        for (let i = 0; i < data.length; i++) {
            data[i] = ParseHex(data[i])
        }
        start = parseInt(data[0])
        end = parseInt(data[1])

        idx = 0
        for (let i = start; i <= end; i++) {
            _data[idx++] = ["0x" + i.toString(16), "0x" + parseInt(Math.random() * 255).toString(16)]
        }
        return _data
    }
    else if (!data.includes("=")) {
        return false
    }
    data = data.split("=")
    for (let i = 0; i < data.length; i++) {
        data[i] = ParseHex(data[i])
    }
    return [data]
}