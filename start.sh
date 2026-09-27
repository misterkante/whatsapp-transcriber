#!/bin/bash

# WhatsApp Audio Transcriber Pro Launcher Script
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$DIR"

echo "=========================================================="
echo " 🎙️  WhatsApp Audio Transcriber Pro - Whisper AI"
echo "=========================================================="

if [ ! -d "$DIR/venv" ]; then
    echo "⚙️  Création de l'environnement virtuel Python..."
    python3 -m venv "$DIR/venv"
    "$DIR/venv/bin/pip" install fastapi uvicorn python-multipart openai-whisper soundfile pydub
fi

echo "🚀 Démarrage du serveur web sur http://localhost:8765 ..."
echo "💡 Appuyez sur CTRL+C pour arrêter le serveur."
echo ""

"$DIR/venv/bin/python" -m uvicorn app.main:app --host 0.0.0.0 --port 8765 --reload
