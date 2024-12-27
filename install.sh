#!/bin/bash

python3 -m venv venv
source venv/bin/activate

# if running on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    if ! command -v brew &> /dev/null; then
        echo "Homebrew is not installed. Please install it first."
        exit 1
    fi
    brew install python-tk
    brew install portaudio
fi

pip install -r requirements.txt

deactivate
echo "Installation complete!"
