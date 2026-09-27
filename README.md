# 🎙️ WhatsApp Audio Transcriber Pro

Outil web local autonome conçu pour importer, convertir et transcrire automatiquement des notes vocales WhatsApp (`.ogg`, `.opus`, `.wav`, `.mp3`, `.m4a`) en texte avec la technologie **OpenAI Whisper AI**.

---

## ⚡ Fonctionnalités Clés

- **Glisser-Déposer Réactif** : Importez un ou plusieurs fichiers audio WhatsApp simultanément.
- **Conversion FFmpeg Intégrée** : Conversion automatique des formats WhatsApp (`.ogg` Opus) en 16kHz WAV mono.
- **Whisper AI Local** : Choix du modèle (Tiny, Base, Small, Medium) pour ajuster vitesse et précision.
- **Lecteur Audio Intégré** : Écoutez l'audio directement dans le navigateur.
- **Bouton Copier en 1 Clic** : Copiez la transcription instantanément dans le presse-papier.
- **Exports Multi-Formats** : Téléchargez les transcriptions au format `.txt`, `.md` ou `.json`.
- **Historique Persistant** : Conservez l'historique de vos transcriptions et recherchez dans vos anciens audios.

---

## 🚀 Démarrage Rapide

Ouvrez un terminal et lancez le script de démarrage :

```bash
cd /home/misterkante/dev/whatsapp-transcriber
./start.sh
```

L'application s'ouvrira sur **[http://localhost:8765](http://localhost:8765)**.

---

## 📁 Structure du Projet

```
/home/misterkante/dev/whatsapp-transcriber/
├── main.py           # Serveur backend FastAPI (FFmpeg + Whisper)
├── start.sh          # Script de lancement automatique (Executable)
├── README.md         # Documentation
├── static/
│   └── index.html    # Interface Web (Tailwind CSS + Lucide Icons + SPA JS)
├── venv/             # Environnement virtuel Python autonome
└── data/
    ├── uploads/      # Audios bruts importés
    ├── converted/    # Audios convertis en WAV
    └── history.json  # Historique des transcriptions
```
