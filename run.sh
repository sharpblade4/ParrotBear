#!/bin/bash
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found!"
    echo "Please run './install.sh' first to set up the environment."
    exit 1
fi

source venv/bin/activate
python gui.py

deactivate