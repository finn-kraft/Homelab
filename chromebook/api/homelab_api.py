from flask import Flask, jsonify, render_template
import subprocess

app = Flask(__name__)

ROUTER_IP = "192.168.10.1"
PROXMOX_IP = "192.168.10.9"

def read_remote_json(path):

    result = run_proxmox(
        f"cat {path}"
    )

    if result.returncode != 0:

        return None

    try:

        import json

        return json.loads(
            result.stdout
        )

    except Exception:

        return None

@app.route("/api/proxmox/details")
def proxmox_details():

    data = read_remote_json(
        "/var/lib/homelab/host_status.json"
    )

    if data is None:

        return jsonify({
            "success": False
        })

    data["success"] = True

    return jsonify(data)

@app.route("/api/vm/<int:vmid>/details")
def vm_details(vmid):

    data = read_remote_json(
        "/var/lib/homelab/vm_status.json"
    )

    if data is None:

        return jsonify({
            "success": False
        })

    vm = data.get(str(vmid))

    if vm is None:

        return jsonify({
            "success": False
        })

    vm["success"] = True

    return jsonify(vm)

@app.route("/api/proxmox/metrics")
def proxmox_metrics():

    cpu = run_proxmox(
        "top -bn1 | grep 'Cpu(s)'"
    )

    ram = run_proxmox(
        "free -m"
    )

    uptime = run_proxmox(
        "uptime -p"
    )

    return jsonify({
        "success": True,
        "cpu": cpu.stdout.strip(),
        "ram": ram.stdout.strip(),
        "uptime": uptime.stdout.strip()
        })

@app.route("/")
def index():
    return render_template("index.html")

def run_local(command):

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20
        )

        return result

    except Exception as e:

        class FakeResult:
            returncode = -1
            stdout = ""
            stderr = str(e)

        return FakeResult()


def run_proxmox(command):

    return run_local(
        [
            "ssh",
            f"root@{PROXMOX_IP}",
            command
        ]
    )


def run_openwrt(command):

    return run_local(
        [
            "ssh",
            f"root@{ROUTER_IP}",
            command
        ]
    )


def run_openwrt_to_proxmox(command):

    return run_local(
        [
            "ssh",
            f"root@{ROUTER_IP}",
            (
                "ssh -i /root/.ssh/id_ed25519 "
                f"root@{PROXMOX_IP} "
                f"'{command}'"
            )
        ]
    )


def parse_qm_list(output):

    vms = []

    lines = output.splitlines()

    if len(lines) <= 1:
        return vms

    for line in lines[1:]:

        parts = line.split()

        if len(parts) < 3:
            continue

        try:

            vmid = int(parts[0])

            name = parts[1]

            status = parts[2]

            vms.append({
                "vmid": vmid,
                "name": name,
                "status": status
            })

        except:
            continue

    return vms


@app.route("/api/status")
def api_status():

    proxmox = run_local(
        ["ping", "-c", "1", PROXMOX_IP]
    )

    router = run_local(
        ["ping", "-c", "1", ROUTER_IP]
    )

    return jsonify({
        "router_online": router.returncode == 0,
        "proxmox_online": proxmox.returncode == 0
    })


@app.route("/api/vms")
def api_vms():

    result = run_proxmox(
        "qm list"
    )

    if result.returncode != 0:

        return jsonify({
            "success": False,
            "error": result.stderr
        })

    return jsonify({
        "success": True,
        "vms": parse_qm_list(
            result.stdout
        )
    })


@app.route("/api/host/wake", methods=["POST"])
def host_wake():

    subprocess.Popen(
        [
            "ssh",
            f"root@{ROUTER_IP}",
            "etherwake -i br-lan 00:d8:61:0d:34:30"
        ]
    )

    return jsonify({
        "success": True,
        "message": "Wake command sent"
    })


@app.route("/api/host/suspend", methods=["POST"])
def host_suspend():

    subprocess.Popen(
        [
            "ssh",
            f"root@{ROUTER_IP}",
            (
                "ssh -i /root/.ssh/id_ed25519 "
                f"root@{PROXMOX_IP} "
                "'systemctl suspend'"
            )
        ]
    )

    return jsonify({
        "success": True,
        "message": "Suspend command sent"
    })


@app.route("/api/host/reboot", methods=["POST"])
def host_reboot():

    subprocess.Popen(
        [
            "ssh",
            f"root@{PROXMOX_IP}",
            "systemctl reboot"
        ]
    )

    return jsonify({
        "success": True,
        "message": "Reboot command sent"
    })


@app.route("/api/vm/<int:vmid>/start", methods=["POST"])
def vm_start(vmid):

    result = run_proxmox(
        f"qm start {vmid}"
    )

    return jsonify({
        "success": result.returncode == 0,
        "message": f"VM {vmid} start initiated",
        "stdout": result.stdout,
        "stderr": result.stderr
    })

@app.route("/api/vm/<int:vmid>/stop", methods=["POST"])
def vm_stop(vmid):

    result = run_proxmox(
        f"qm shutdown {vmid}"
    )

    return jsonify({
        "success": result.returncode == 0,
        "message": f"VM {vmid} shutdown initiated",
        "stdout": result.stdout,
        "stderr": result.stderr
    })

@app.route("/api/vm/<int:vmid>/reboot", methods=["POST"])
def vm_reboot(vmid):

    result = run_proxmox(
        f"qm reboot {vmid}"
    )

    return jsonify({
        "success": result.returncode == 0,
        "message": f"VM {vmid} reboot initiated",
        "stdout": result.stdout,
        "stderr": result.stderr
    })


if __name__ == "__main__":

    print("Starting Homelab API on port 5001...")

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )
