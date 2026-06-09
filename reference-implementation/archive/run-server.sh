#!/usr/bin/env bash
# Local: ./run-server.sh        LAN share: ./run-server.sh --share
cd "$(dirname "$0")"
python3 archive-server.py "$@"
