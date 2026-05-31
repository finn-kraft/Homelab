#!/bin/bash

echo ""
echo "====================================="
echo " Chromebook Infrastructure Check"
echo "====================================="

echo ""
echo "Waiting for services to settle..."
sleep 15

echo ""

check_service() {

    if systemctl --user is-active --quiet "$1"; then
        echo "[OK] $1 running"
    else
        echo "[FAIL] $1 NOT running"
    fi
}

check_service wake

if pgrep noip2 >/dev/null; then
    echo "[OK] noip2 running"
else
    echo "[FAIL] noip2 NOT running"
fi

if tailscale status >/dev/null 2>&1; then
    echo "[OK] tailscale connected"
else
    echo "[FAIL] tailscale NOT connected"
fi

if pgrep sshd >/dev/null; then
    echo "[OK] sshd running"
else
    echo "[FAIL] sshd NOT running"
fi

echo ""
echo "====================================="
echo " Infrastructure Check Complete"
echo "====================================="
echo ""
