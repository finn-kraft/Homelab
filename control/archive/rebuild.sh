#!/bin/bash

set -e

LAB_DIR="$HOME/lab"
SYSTEMD_DIR="$HOME/.config/systemd/user"
NOIP_CONFIG_DIR="$HOME/.config/noip2"
LOG_DIR="$LAB_DIR/logs"

echo "====================================="
echo " Chromebook Infrastructure Rebuild"
echo "====================================="

echo ""
echo "[1/10] Updating packages..."
sudo apt update

echo ""
echo "[2/10] Installing dependencies..."
sudo apt install -y \
    python3 \
    python3-flask \
    tailscale \
    wakeonlan \
    openssh-server \
    rsync \
    git \
    netcat-openbsd \
    nano

echo ""
echo "[3/10] Creating directory structure..."

mkdir -p "$LAB_DIR"
mkdir -p "$LAB_DIR/services"
mkdir -p "$LAB_DIR/configs"
mkdir -p "$LAB_DIR/logs"
mkdir -p "$SYSTEMD_DIR"
mkdir -p "$NOIP_CONFIG_DIR"

echo ""
echo "[4/10] Configuring SSH..."

sudo ssh-keygen -A || true
sudo rm -f /etc/ssh/sshd_not_to_be_run
sudo service ssh start

echo ""
echo "[5/10] Restoring No-IP config..."

if [ -f "$LAB_DIR/configs/no-ip2.conf" ]; then

    cp "$LAB_DIR/configs/no-ip2.conf" \
       "$NOIP_CONFIG_DIR/no-ip2.conf"

    chmod 600 "$NOIP_CONFIG_DIR/no-ip2.conf"

    echo "No-IP config restored."

else

    echo "WARNING: no-ip2.conf missing."
    echo "Run: noip2 -C manually later."

fi

echo ""
echo "[6/10] Restoring systemd services..."

cp "$LAB_DIR/services/"*.service "$SYSTEMD_DIR/" || true

systemctl --user daemon-reload

echo ""
echo "[7/10] Enabling services..."

systemctl --user enable wake || true
systemctl --user enable noip2 || true
systemctl --user enable startup-check || true

echo ""
echo "[8/10] Starting services..."

systemctl --user restart wake || true
systemctl --user restart noip2 || true
systemctl --user restart startup-check || true

echo ""
echo "[9/10] Restoring cron jobs..."

if [ -f "$LAB_DIR/cron.txt" ]; then

    crontab "$LAB_DIR/cron.txt"

    echo "Cron restored."

else

    echo "WARNING: cron.txt missing."

fi

echo ""
echo "[10/10] Running infrastructure verification..."

sleep 5

systemctl --user start startup-check || true

echo ""
echo "====================================="
echo " Startup Verification"
echo "====================================="

cat "$LAB_DIR/startup.log" || true

echo ""
echo "====================================="
echo " Rebuild Complete"
echo "====================================="

echo ""
echo "IMPORTANT REMAINING MANUAL TASKS:"
echo ""
echo "1. Authenticate Tailscale if needed:"
echo "   sudo tailscale up"
echo ""
echo "2. Verify No-IP:"
echo "   noip2 -S -c ~/.config/noip2/no-ip2.conf"
echo ""
echo "3. Verify dashboard:"
echo "   http://penguin:5000"
echo ""
echo "4. Verify SSH:"
echo "   ssh localhost"
echo ""
echo "5. Verify backups:"
echo "   crontab -l"
echo ""
