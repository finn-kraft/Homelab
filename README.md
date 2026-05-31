# Chromebook Infrastructure Node SOP

## Overview

This Chromebook functions as the always-on infrastructure control plane for the homelab. Its purpose is to provide lightweight services that remain available even when the main Proxmox gaming server is powered off. The Chromebook handles remote access, Wake-on-LAN orchestration, infrastructure monitoring, backups, dynamic DNS, and service recovery while consuming very little power.

Core design philosophy:

```text
Chromebook = always-on control plane
Proxmox server = on-demand compute plane
```

Primary responsibilities:
- Tailscale remote access
- SSH/SFTP gateway
- No-IP dynamic DNS updates
- Flask-based Wake-on-LAN dashboard
- Infrastructure health monitoring
- Backup orchestration
- Startup verification and recovery

---

# Architecture

```text
Remote Devices
    ↓
Tailscale
    ↓
Chromebook (penguin)
    ↓
Flask Dashboard
    ↓
SSH → OpenWrt
    ↓
etherwake
    ↓
Proxmox Host
    ↓
Minecraft VM
```

The Chromebook itself never sends raw Wake-on-LAN packets directly. Instead, it securely SSHes into OpenWrt, which then transmits the WoL broadcast packet on the LAN. This avoids Crostini networking limitations and keeps the architecture reliable.

---

# Important Paths

Main working directory:

```text
~/lab
```

Important files:

```text
~/lab/wake.py
~/lab/rebuild.sh
~/lab/backup.sh
~/lab/start-services.sh
~/lab/startup-check.sh
~/lab/cron.txt
~/.config/noip2/no-ip2.conf
~/.config/systemd/user/wake.service
```

Dashboard URL:

```text
http://penguin:5000
```

---

# Services

## Tailscale

Tailscale provides all secure remote connectivity into the homelab. Devices connect using the MagicDNS hostname:

```text
penguin
```

Examples:

```bash
ssh skiing4life12@penguin
sftp skiing4life12@penguin
```

Verification:

```bash
tailscale status
```

If authentication ever breaks:

```bash
sudo tailscale up
```

---

## Flask Wake Dashboard

The Flask dashboard provides:
- one-click Proxmox startup
- remote poweroff control
- live infrastructure monitoring
- Minecraft availability checks
- progressive startup animation/status display
- automatic status refreshes

Infrastructure checks include:
- Router ICMP reachability
- Proxmox ICMP reachability
- Minecraft VM reachability
- Minecraft TCP port 25565 availability

The dashboard now uses real infrastructure state to drive the startup animation. Instead of a fake timer, the UI progressively updates as:

```text
Router online
↓
Proxmox online
↓
Minecraft VM reachable
↓
Minecraft port opens
```

The dashboard also exposes a remote poweroff button that safely shuts down the Proxmox host over SSH.

The wake button is automatically disabled whenever the Proxmox host is already online.

Restart manually if needed:

```bash
systemctl --user restart wake
```

Verify:

```bash
systemctl --user status wake
```

---

## No-IP Dynamic DNS

No-IP maintains the public DNS record:

```text
russellwrt.ddns.net
```

The daemon uses:

```text
~/.config/noip2/no-ip2.conf
```

Verification:

```bash
noip2 -S -c ~/.config/noip2/no-ip2.conf
```

Expected:

```text
1 noip2 process active.
```

Because `noip2` behaves poorly with systemd under Crostini, it is automatically launched from `.bashrc` through:

```text
~/lab/start-services.sh
```

rather than relying entirely on systemd.

---

## SSH / SFTP

The Chromebook acts as a lightweight remote administration and file-transfer node.

Verify locally:

```bash
ssh localhost
```

Remote access:

```bash
ssh skiing4life12@penguin
sftp skiing4life12@penguin
```

Useful SFTP commands:

```bash
put wake.py
get README.md
ls
cd lab
exit
```

---

# Startup Flow

ChromeOS does not automatically launch the Linux VM after reboot. The current workflow is:

```text
Chromebook boots
    ↓
User logs into ChromeOS
    ↓
Linux VM dormant
    ↓
Open Linux Terminal once
    ↓
.bashrc executes
    ↓
start-services.sh runs
    ↓
noip2 starts if needed
    ↓
startup-check.sh validates infrastructure
```

Current `.bashrc` entry:

```bash
# start infrastructure services
~/lab/start-services.sh
```

The startup check verifies:
- wake dashboard
- noip2
- tailscale
- sshd

Example output:

```text
=====================================
 Chromebook Infrastructure Check
=====================================

[OK] wake running
[OK] noip2 running
[OK] tailscale connected
[OK] sshd running
```

---

# Backup System

Backups are performed using:

```text
rsync over SSH
```

Daily backup schedule:

```text
12:00 PM daily
```

Cron entry:

```cron
0 12 * * * /home/skiing4life12/lab/backup.sh
```

Verify:

```bash
crontab -l
```

The Chromebook currently backs up lightweight infrastructure/configuration data rather than full VM images.

---

# Rebuild and Recovery

The rebuild system exists to rapidly recreate the infrastructure environment after:
- Chromebook replacement
- Linux VM corruption
- migration to another machine
- accidental configuration loss

Primary rebuild script:

```bash
bash ~/lab/rebuild.sh
```

The rebuild process:
- installs required packages
- recreates directory structure
- restores SSH functionality
- restores cron jobs
- restores services
- enables infrastructure services
- verifies operational health

Remaining manual tasks after rebuild:
- Tailscale authentication
- possible No-IP credential recreation

This infrastructure is now mostly reproducible from backups plus the rebuild script.

---

# Proxmox / Minecraft Integration

Proxmox host:

```text
192.168.10.200
```

OpenWrt router:

```text
192.168.10.1
```

Minecraft access uses Tailscale instead of public internet exposure. Players connect using:

```text
mcserver
```

or:

```text
100.x.x.x:25565
```

Advantages:
- no port forwarding
- no CGNAT issues
- encrypted traffic
- private access only
- greatly reduced attack surface

Planned Proxmox power schedule:

```text
10:00 AM → automatic startup
10:00 PM → automatic shutdown
2:00 AM → overnight backup startup
3:00 AM → overnight shutdown
```

Recommended mechanism:

```text
BIOS RTC wake + cron shutdowns
```

---

# Troubleshooting

Dashboard issues:

```bash
systemctl --user status wake
python3 ~/lab/wake.py
```

No-IP issues:

```bash
noip2 -S -c ~/.config/noip2/no-ip2.conf
```

SSH issues:

```bash
sudo service ssh start
ssh localhost
```

Tailscale issues:

```bash
tailscale status
sudo tailscale up
```

Infrastructure verification:

```bash
~/lab/startup-check.sh
```

---

# Long-Term Direction

The Chromebook has effectively evolved into a lightweight infrastructure appliance. Future improvements may include:

- replacing ChromeOS with native Linux
- dedicated backup hardware
- HTTPS reverse proxy
- Proxmox API integration
- UPS integration
- Discord notifications
- Minecraft player metrics
- automatic power orchestration
- Dockerization
- full infrastructure-as-code workflows

At its current stage, the Chromebook already functions as:
- management plane
- WoL bridge
- Tailscale gateway
- DDNS client
- SSH/SFTP appliance
- backup orchestrator
- monitoring dashboard
- remote Minecraft startup portal

