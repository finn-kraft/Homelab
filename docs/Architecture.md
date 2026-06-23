# Architecture

The homelab is organized around four primary roles: control, compute, storage, and networking. The design prioritizes reliability, automation, low administrative overhead, and rapid recovery after hardware failure.

## Control Node

The system named **control** serves as the central control plane for the homelab. It remains powered on continuously and hosts the dashboard, monitoring tools, automation scripts, backup orchestration, infrastructure management utilities, and operational documentation.

The control node is intentionally lightweight. Its responsibility is to coordinate workloads rather than perform heavy computation. Resource-intensive tasks are delegated to the compute platform.

Recovery time is minimized through a combination of GitHub-based source control and PBS-based system backups. The control node is expected to be recoverable quickly without requiring extensive manual configuration.

## Compute Platform

The Proxmox server serves as the primary compute platform.

Responsibilities include:

* Virtual machines
* Containers
* Kubernetes workloads
* Experimental services
* AI agent execution
* Future application hosting

The control node issues requests and jobs, while execution occurs on infrastructure hosted by Proxmox.

## Kubernetes

Kubernetes operates on the Proxmox platform and provides the foundation for future distributed services and AI workloads.

The long-term goal is for the control node to dispatch work to Kubernetes-hosted services rather than executing those workloads locally.

## AI Agents

AI agents are a major long-term objective of the homelab.

Agents will execute on Proxmox-hosted infrastructure while being managed and accessed through the control node. This separation allows AI capabilities to scale independently from the management platform.

Planned agent categories include:

* Infrastructure monitoring
* Reporting and analytics
* Backup verification
* Automation and orchestration
* Financial analysis
* Personal productivity

## Storage and Backup

Proxmox Backup Server (PBS) provides centralized backup storage.

Current and future backup targets include:

* Proxmox virtual machines
* OpenWrt configuration backups
* Control node backups
* Documentation and configuration archives

A future NAS will provide general-purpose storage, media storage, archives, datasets, and shared files. PBS and the NAS are expected to remain separate systems with different responsibilities.

### Backup Strategy

GitHub serves as the source of truth for:

* Source code
* Scripts
* Documentation
* Configuration files

PBS serves as the source of truth for:

* System state
* Backup archives
* Recovery data
* Configuration snapshots

This approach minimizes recovery time while maintaining version history.

## Networking

OpenWrt currently provides:

* Routing
* Firewall
* DHCP
* DNS
* VPN access
* Wake-on-LAN

The long-term objective is to minimize the amount of infrastructure hosted on the router itself.

Future plans include replacing the current router with an OPNsense-based platform capable of supporting more advanced networking requirements. At that point, the existing OpenWrt hardware may be repurposed as a dedicated wireless access point.

## Recovery Philosophy

Systems should be designed so that hardware failures are inconvenient rather than catastrophic.

### Control Node Recovery

1. Install Ubuntu Server
2. Clone the GitHub repository

```bash
git clone git@github.com:finn-kraft/Homelab.git
```

3. Create and activate Python environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

4. Install dependencies

```bash
pip install -r requirements.txt
```

5. Restore PBS backup if available
6. Enable system services
7. Verify dashboard operation

### OpenWrt Recovery

1. Install OpenWrt firmware
2. Download desired backup from PBS

```bash
scp root@<PBS-IP>:/backup/openwrt/<backup>.tar.gz .
```

3. Restore configuration

```bash
sysupgrade -r <backup>.tar.gz
```

4. Reboot

```bash
reboot
```

The primary design goal is to reduce recovery time through automation, documentation, backups, and centralized management.

