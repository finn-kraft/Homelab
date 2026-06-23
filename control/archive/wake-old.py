from flask import Flask, render_template_string, jsonify
import subprocess
import socket
import os
import time

app = Flask(__name__)

# =========================
# Infrastructure Addresses
# =========================

ROUTER_IP = '192.168.10.1'
PROXMOX_IP = '192.168.10.9'
MC_VM_IP = '192.168.10.200'
MC_PORT = 25565

# =========================
# Backup State
# =========================

LAST_BACKUP_FILE = os.path.expanduser(
    '~/lab/state/last-backup.txt'
)

# =========================
# Session Extension Settings
# =========================

MAX_EXTENDS = 3
EXTEND_MINUTES = 20
EXTEND_COOLDOWN_SECONDS = 600

last_extend_time = 0
extend_count = 0

# =========================
# Utility Functions
# =========================

def ping_host(ip):

    result = subprocess.run(
        ['ping', '-c', '1', ip],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )

    return result.returncode == 0


def check_port(ip, port):

    try:

        sock = socket.create_connection(
            (ip, port),
            timeout=2
        )

        sock.close()

        return True

    except:

        return False


def get_last_backup_age():

    try:

        modified = os.path.getmtime(
            LAST_BACKUP_FILE
        )

        age_seconds = int(
            time.time() - modified
        )

        hours = age_seconds // 3600
        minutes = (age_seconds % 3600) // 60

        return f'{hours}h {minutes}m ago'

    except:

        return 'Unknown'


def get_proxmox_uptime():

    try:

        result = subprocess.check_output(
            [
                'ssh',
                f'root@{PROXMOX_IP}',
                'uptime -p'
            ],
            text=True,
            timeout=5
        )

        return result.strip()

    except:

        return 'Unavailable'


def get_shutdown_status():

    try:

        result = subprocess.check_output(
            [
                'ssh',
                f'root@{PROXMOX_IP}',
                'shutdown --show'
            ],
            text=True,
            stderr=subprocess.DEVNULL,
            timeout=5
        )

        result = result.strip()

        if result:
            return result

        return 'No scheduled shutdown'

    except:

        return 'Unavailable'


def build_status():

    global extend_count

    router_online = ping_host(ROUTER_IP)

    proxmox_online = ping_host(PROXMOX_IP)

    mc_vm_online = ping_host(MC_VM_IP)

    minecraft_ready = check_port(
        MC_VM_IP,
        MC_PORT
    )

    shutdown_status = get_shutdown_status()

    # =========================
    # Infrastructure State Machine
    # =========================

    if not proxmox_online:

        state = 'OFFLINE'

    elif proxmox_online and not minecraft_ready:

        state = 'BOOTING_MINECRAFT'

    else:

        state = 'ONLINE'

    # =========================
    # Extend Button Logic
    # =========================

    show_extend = False
    extend_enabled = False

    if (
        minecraft_ready and
        'shutdown' in shutdown_status.lower()
    ):

        show_extend = True

        if (
            extend_count < MAX_EXTENDS and
            time.time() - last_extend_time >
            EXTEND_COOLDOWN_SECONDS
        ):

            extend_enabled = True

    return {
        'router_online': router_online,
        'proxmox_online': proxmox_online,
        'mc_vm_online': mc_vm_online,
        'minecraft_ready': minecraft_ready,
        'state': state,
        'shutdown_status': shutdown_status,
        'backup_age': get_last_backup_age(),
        'uptime': get_proxmox_uptime(),
        'show_extend': show_extend,
        'extend_enabled': extend_enabled,
        'extend_count': extend_count
    }


# =========================
# HTML Dashboard
# =========================

HTML = """
<!DOCTYPE html>
<html>
<head>

<title>Homelab Control</title>

<style>

body {
    background-color: #0f172a;
    color: white;
    font-family: Arial, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
    padding: 20px;
}

.card {
    background-color: #1e293b;
    padding: 40px;
    border-radius: 20px;
    width: 600px;
    box-shadow: 0 10px 25px rgba(0,0,0,0.4);
}

h1 {
    text-align: center;
}

.status {
    text-align: center;
    font-size: 24px;
    margin-top: 20px;
    font-weight: bold;
}

.online {
    color: #22c55e;
}

.offline {
    color: #ef4444;
}

.warning {
    color: #facc15;
}

.button-row {
    display: flex;
    gap: 15px;
    justify-content: center;
    margin-top: 25px;
    flex-wrap: wrap;
}

button {
    border: none;
    border-radius: 12px;
    padding: 16px 24px;
    font-size: 16px;
    color: white;
    cursor: pointer;
}

button:disabled {
    background-color: #475569 !important;
    cursor: not-allowed;
}

.wake-btn {
    background-color: #16a34a;
}

.shutdown-btn {
    background-color: #dc2626;
}

.extend-btn {
    background-color: #2563eb;
}

.step {
    margin-top: 12px;
    background-color: #0f172a;
    border-radius: 10px;
    padding: 12px;
}

.details {
    margin-top: 25px;
}

.detail-row {
    display: flex;
    justify-content: space-between;
    background-color: #0f172a;
    padding: 10px;
    border-radius: 10px;
    margin-top: 10px;
}

#feedback {
    text-align: center;
    margin-top: 20px;
    color: #facc15;
    font-weight: bold;
}

</style>

</head>
<body>

<div class="card">

<h1>Homelab Control</h1>

<div class="status" id="statusText"></div>

<div class="button-row">

<button
    class="wake-btn"
    id="wakeBtn"
    onclick="wakeServer()">
    ⚡ Start Server
</button>

<button
    class="shutdown-btn"
    id="shutdownBtn"
    onclick="shutdownServer()">
    🛑 Suspend Server
</button>

<button
    class="extend-btn"
    id="extendBtn"
    onclick="extendSession()">
    ⏱ Extend 20m
</button>

</div>

<div id="feedback"></div>

<div class="step" id="router-step"></div>
<div class="step" id="proxmox-step"></div>
<div class="step" id="minecraft-step"></div>
<div class="step" id="ready-step"></div>

<div class="details">

<div class="detail-row">
    <span>🕒 Proxmox Uptime</span>
    <span id="uptime"></span>
</div>

<div class="detail-row">
    <span>💾 Last Backup</span>
    <span id="backup"></span>
</div>

<div class="detail-row">
    <span>⚠ Shutdown Status</span>
    <span id="shutdown-status"></span>
</div>

<div class="detail-row">
    <span>⏱ Session Extensions</span>
    <span id="extend-count"></span>
</div>

</div>

</div>

<script>

let pollDelay = 5000;

async function refreshStatus() {

    const response = await fetch('/status');

    const data = await response.json();

    document.getElementById('uptime').innerText =
        data.uptime;

    document.getElementById('backup').innerText =
        data.backup_age;

    document.getElementById('shutdown-status').innerText =
        data.shutdown_status;

    document.getElementById('extend-count').innerText =
        `${data.extend_count}/3`;

    const statusText =
        document.getElementById('statusText');

    if (data.state === 'OFFLINE') {

        statusText.innerHTML =
            '<span class="offline">🔴 OFFLINE</span>';

        pollDelay = 5000;
    }

    if (data.state === 'BOOTING_MINECRAFT') {

        statusText.innerHTML =
            '<span class="warning">🟡 STARTING...</span>';

        pollDelay = 2000;
    }

    if (data.state === 'ONLINE') {

        statusText.innerHTML =
            '<span class="online">🟢 ONLINE</span>';

        pollDelay = 5000;
    }

    document.getElementById('wakeBtn').disabled =
        data.proxmox_online;

    document.getElementById('shutdownBtn').disabled =
        !data.proxmox_online;

    const extendBtn =
        document.getElementById('extendBtn');

    if (data.show_extend) {

        extendBtn.style.display = 'inline-block';
        extendBtn.disabled = !data.extend_enabled;

    } else {

        extendBtn.style.display = 'none';
    }

    document.getElementById('router-step').innerHTML =
        data.router_online
            ? '✅ Router Online'
            : '❌ Router Offline';

    document.getElementById('proxmox-step').innerHTML =
        data.proxmox_online
            ? '✅ Proxmox Online'
            : '❌ Proxmox Offline';

    document.getElementById('minecraft-step').innerHTML =
        data.mc_vm_online
            ? '✅ Minecraft VM Reachable'
            : '❌ Minecraft VM Offline';

    document.getElementById('ready-step').innerHTML =
        data.minecraft_ready
            ? '✅ Minecraft Ready'
            : '⏳ Waiting for Minecraft';

    setTimeout(refreshStatus, pollDelay);
}

async function wakeServer() {

    const feedback =
        document.getElementById('feedback');

    feedback.innerText =
        '⚡ Sending wake command...';

    try {

        const response = await fetch('/wake', {
            method: 'POST'
        });

        const result = await response.text();

        feedback.innerText = result;

    } catch {

        feedback.innerText =
            '❌ Wake command failed';
    }
}

async function shutdownServer() {

    const confirmed = confirm(
        'Suspend the Proxmox server?'
    );

    if (!confirmed) {
        return;
    }

    const feedback =
        document.getElementById('feedback');

    feedback.innerText =
        '🛑 Sending suspend command...';

    try {

        const response = await fetch('/shutdown', {
            method: 'POST'
        });

        const result = await response.text();

        feedback.innerText = result;

    } catch {

        feedback.innerText =
            '❌ Suspend command failed';
    }
}

async function extendSession() {

    const feedback =
        document.getElementById('feedback');

    feedback.innerText =
        '⏱ Extending session...';

    try {

        const response = await fetch('/extend', {
            method: 'POST'
        });

        const result = await response.text();

        feedback.innerText = result;

    } catch {

        feedback.innerText =
            '❌ Session extension failed';
    }
}

refreshStatus();

</script>

</body>
</html>
"""


# =========================
# Flask Routes
# =========================

@app.route('/')
def index():
    return render_template_string(HTML)


@app.route('/status')
def status():
    return jsonify(build_status())


@app.route('/wake', methods=['POST'])
def wake():

    global extend_count

    extend_count = 0

    subprocess.Popen(
        [
            'ssh',
            f'root@{ROUTER_IP}',
            'etherwake -i br-lan 00:d8:61:0d:34:30'
        ]
    )

    return 'Wake command sent.'


@app.route('/shutdown', methods=['POST'])
def shutdown():

    subprocess.Popen(
        [
            'ssh',
            f'root@{PROXMOX_IP}',
            'systemctl suspend'
        ]
    )

    return 'Suspend command sent.'


@app.route('/extend', methods=['POST'])
def extend():

    global extend_count
    global last_extend_time

    now = time.time()

    if extend_count >= MAX_EXTENDS:
        return 'Maximum extensions reached.'

    if now - last_extend_time < EXTEND_COOLDOWN_SECONDS:
        return 'Extension cooldown active.'

    extend_count += 1
    last_extend_time = now

    subprocess.Popen(
        [
            'ssh',
            f'root@{PROXMOX_IP}',
            f'shutdown -c && shutdown -h +{EXTEND_MINUTES}'
        ]
    )

    return f'Session extended by {EXTEND_MINUTES} minutes.'


app.run(
    host='0.0.0.0',
    port=5000
)


