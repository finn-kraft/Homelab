#!/bin/bash

cd /home/finn/Homelab || exit 1

git add .

git commit -m "Nightly backup $(date '+%Y-%m-%d')" || true

git push

