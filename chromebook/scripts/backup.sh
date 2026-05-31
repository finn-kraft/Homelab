#!/bin/bash

rsync -av ~/lab ~/.ssh ~/.config/systemd/user root@192.168.10.9:/backup/chromebook
