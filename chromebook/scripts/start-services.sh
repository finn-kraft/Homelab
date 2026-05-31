#!/bin/bash

echo "Starting infrastructure services..."

if ! pgrep noip2 > /dev/null; then
    noip2 -c ~/.config/noip2/no-ip2.conf
fi

~/lab/startup-check.sh
