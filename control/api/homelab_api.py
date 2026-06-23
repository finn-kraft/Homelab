import json
import subprocess

from flask import Flask
from flask import jsonify
from flask import render_template

app = Flask(
    __name__,
    template_folder="../dashboard/templates",
    static_folder="../dashboard/static"
)


#
# Configuration
#

with open("config.json") as f:
    CONFIG = json.load(f)

with open("services.json") as f:
    SERVICES = json.load(f)

ROUTER_IP = CONFIG["router_ip"]
PROXMOX_IP = CONFIG["proxmox_ip"]


#
# Helpers
#

def run_local(command):

    try:

        return subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=20
        )

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


def run_router(command):

    return run_local(
        [
            "ssh",
            f"root@{ROUTER_IP}",
            command
        ]
    )


def run_service(service_name, action):

    service = SERVICES.get(service_name)

    if service is None:

        return None

    return run_local(
        [
            "ssh",
            f"{service['user']}@{service['host']}",
            f"sudo systemctl {action} {service['service']}"
        ]
    )


#
# Dashboard
#

@app.route("/")
def index():

    return render_template("index.html")


#
# Status
#

@app.route("/api/status")
def api_status():

    proxmox = run_local(
        ["ping", "-c", "1", PROXMOX_IP]
    )

    router = run_local(
        ["ping", "-c", "1", ROUTER_IP]
    )

    return jsonify({
        "success": True,
        "router_online": router.returncode == 0,
        "proxmox_online": proxmox.returncode == 0
    })


#
# VMs
#

@app.route("/api/vms")
def api_vms():

    result = run_proxmox("qm list")

    return jsonify({
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    })


@app.route("/api/vm/<int:vmid>/start", methods=["POST"])
def vm_start(vmid):

    result = run_proxmox(
        f"qm start {vmid}"
    )

    return jsonify({
        "success": result.returncode == 0
    })


@app.route("/api/vm/<int:vmid>/stop", methods=["POST"])
def vm_stop(vmid):

    result = run_proxmox(
        f"qm shutdown {vmid}"
    )

    return jsonify({
        "success": result.returncode == 0
    })


@app.route("/api/vm/<int:vmid>/reboot", methods=["POST"])
def vm_reboot(vmid):

    result = run_proxmox(
        f"qm reboot {vmid}"
    )

    return jsonify({
        "success": result.returncode == 0
    })


#
# Services
#

@app.route("/api/services")
def services():

    return jsonify({
        "success": True,
        "services": SERVICES
    })


@app.route("/api/service/<service_name>/restart",
           methods=["POST"])
def restart_service(service_name):

    result = run_service(
        service_name,
        "restart"
    )

    if result is None:

        return jsonify({
            "success": False,
            "error": "Unknown service"
        })

    return jsonify({
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    })


#
# Host
#

@app.route("/api/host/wake", methods=["POST"])
def host_wake():

    run_router(
        f"etherwake -i "
        f"{CONFIG['wol']['interface']} "
        f"{CONFIG['wol']['mac']}"
    )

    return jsonify({
        "success": True
    })


#
# Health
#

@app.route("/api/health")
def health():

    return jsonify({
        "success": True,
        "api": "healthy"
    })


if __name__ == "__main__":

    print(
        "Starting Homelab API..."
    )

    app.run(
        host="0.0.0.0",
        port=5001,
        debug=False
    )
