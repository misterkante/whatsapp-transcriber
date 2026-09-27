#!/usr/bin/env bash
# Lance WhatsApp Transcriber sur http://$WT_HOST:$WT_PORT
set -euo pipefail

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

HOST="${WT_HOST:-127.0.0.1}"
PORT="${WT_PORT:-8765}"

if ! command -v ffmpeg >/dev/null; then
    echo "ffmpeg est introuvable. Installe-le (ex. : sudo apt install ffmpeg)." >&2
    exit 1
fi

if [ ! -x venv/bin/python ]; then
    echo "Création de l'environnement virtuel..."
    python3 -m venv venv
    venv/bin/pip install --upgrade pip
    venv/bin/pip install -r requirements.txt
fi

echo "WhatsApp Transcriber : http://$HOST:$PORT (CTRL+C pour arrêter)"
exec venv/bin/python -m uvicorn app.main:app --host "$HOST" --port "$PORT"
