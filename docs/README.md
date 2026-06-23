# Homelab

Homelab is a centralized infrastructure management platform built around a dedicated control node, a Proxmox compute platform, PBS backup storage, and OpenWrt networking. The project provides monitoring, automation, orchestration, backup management, and future AI-agent integration through a single operational interface.

## Current Capabilities

* Homelab dashboard
* Infrastructure monitoring
* Dynamic VM discovery
* VM power controls
* Proxmox host management
* OpenWrt configuration backups
* GitHub-based configuration management
* PBS-based backup infrastructure

## Repository Structure

```text
control/
├── api/
├── dashboard/
├── docs/
└── scripts/
```

## Running the Dashboard

Create a Python virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the dashboard:

```bash
cd control/api

python3 homelab_api.py
```

The dashboard listens on port:

```text
5001
```

## Recovery

### Control Node Recovery

Install Ubuntu Server.

Clone the repository:

```bash
git clone git@github.com:finn-kraft/Homelab.git

cd Homelab
```

Create and activate a Python environment:

```bash
python3 -m venv .venv

source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Restore PBS backup if available.

Enable services:

```bash
systemctl --user daemon-reload

systemctl --user enable homelab-dashboard.service

systemctl --user start homelab-dashboard.service
```

Verify:

```bash
curl http://localhost:5001/api/status
```

### OpenWrt Recovery

Install OpenWrt firmware.

Copy the desired backup from PBS:

```bash
scp root@<PBS-IP>:/backup/openwrt/<backup>.tar.gz .
```

Restore configuration:

```bash
sysupgrade -r <backup>.tar.gz
```

Reboot:

```bash
reboot
```

## Documentation

Additional design and implementation details are maintained in:

```text
docs/Architecture.md
docs/TODO.md
```

