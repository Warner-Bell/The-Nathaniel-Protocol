#!/bin/bash
cd "$(dirname "$0")"
if [ -f .venv/Scripts/python.exe ]; then
    exec .venv/Scripts/python.exe kb_server.py
else
    exec .venv/bin/python kb_server.py
fi
