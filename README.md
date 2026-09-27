# WhatsApp Transcriber

Petit outil web local pour transcrire des notes vocales WhatsApp (`.ogg`, `.opus`, `.mp3`, `.m4a`, `.wav`) en texte, avec [faster-whisper](https://github.com/SYSTRAN/faster-whisper).

Tout tourne sur ta machine : aucun audio ni texte n'est envoyé à un service externe. Pas besoin de GPU, le modèle tourne en int8 sur le processeur.

## Fonctionnalités

- glisser-déposer d'un ou plusieurs audios, avec l'avancement fichier par fichier ;
- choix du modèle (`tiny`, `base`, `small`, `medium`) et de la langue (fr, en, auto) ;
- lecteur audio, copie du texte en un clic, export `.txt`, `.md` ou `.json` ;
- historique consultable avec recherche, et horodatage par segment.

## Prérequis

- Python 3.10 ou plus récent
- [FFmpeg](https://ffmpeg.org/) (`sudo apt install ffmpeg`, `brew install ffmpeg`…)

## Lancer

```bash
git clone https://github.com/misterkante/whatsapp-transcriber.git
cd whatsapp-transcriber
./start.sh
```

Au premier lancement, `start.sh` crée le venv et installe les dépendances. Ouvre ensuite <http://127.0.0.1:8765>.

Chaque modèle est téléchargé depuis Hugging Face la première fois qu'il est utilisé (environ 75 Mo pour `tiny`, 480 Mo pour `small`, 1,5 Go pour `medium`).

## Configuration

Variables d'environnement, toutes optionnelles :

| Variable      | Défaut        | Rôle                                                      |
|---------------|---------------|-----------------------------------------------------------|
| `WT_HOST`     | `127.0.0.1`   | Adresse d'écoute. `0.0.0.0` pour l'ouvrir au réseau local |
| `WT_PORT`     | `8765`        | Port                                                      |
| `WT_MODEL`    | `small`       | Modèle par défaut côté API                                |
| `WT_THREADS`  | nb de cœurs   | Threads CPU utilisés par Whisper                          |
| `WT_DATA_DIR` | `./data`      | Dossier des audios et de l'historique                     |

L'outil n'a pas d'authentification : n'utilise `WT_HOST=0.0.0.0` que sur un réseau de confiance.

## Structure

```
app/
├── main.py         routes FastAPI
├── transcriber.py  faster-whisper (CPU, int8, un modèle en mémoire à la fois)
├── audio.py        conversion FFmpeg en WAV 16 kHz mono
├── history.py      historique JSON (écritures atomiques)
└── config.py       chemins et variables d'environnement
static/             interface (HTML, CSS et JS, sans dépendance externe)
data/               audios et historique, créé au lancement, ignoré par git
```

## API

| Méthode  | Route                               | Rôle                                           |
|----------|-------------------------------------|------------------------------------------------|
| `POST`   | `/api/transcribe`                   | `files`, `model_name`, `language` (multipart)  |
| `GET`    | `/api/history`                      | historique complet                             |
| `DELETE` | `/api/history/{id}`                 | supprime une transcription et ses fichiers     |
| `GET`    | `/api/audio/{id}`                   | audio converti (WAV)                           |
| `GET`    | `/api/export/{id}?format=txt\|md\|json` | export                                     |

## Licence

MIT
