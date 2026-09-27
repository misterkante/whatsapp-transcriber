import shutil
import time
import json
import uuid
from pathlib import Path
from urllib.parse import quote
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from starlette.concurrency import run_in_threadpool

from . import history, transcriber
from .audio import AudioConversionError, to_wav
from .config import CONVERTED_DIR, DEFAULT_MODEL, MODELS, STATIC_DIR, UPLOADS_DIR

app = FastAPI(title="WhatsApp Audio Transcriber", version="1.0.0")



def _check_id(item_id: str) -> str:
    """Les ids servent à construire des chemins de fichiers : on n'accepte que des UUID."""
    try:
        return str(uuid.UUID(item_id))
    except ValueError:
        raise HTTPException(status_code=404, detail="Item not found")


def _process(file: UploadFile, model_name: str, language: str) -> dict:
    """Enregistre, convertit et transcrit un fichier. Nettoie derrière lui en cas d'échec."""
    item_id = str(uuid.uuid4())
    original_name = file.filename or "audio_whatsapp.ogg"
    ext = Path(original_name).suffix.lower()
    if not ext[1:].isalnum():
        ext = ".ogg"
    raw_path = UPLOADS_DIR / f"{item_id}{ext}"
    wav_path = CONVERTED_DIR / f"{item_id}.wav"

    try:
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        to_wav(raw_path, wav_path)
        start = time.time()
        res = transcriber.transcribe(str(wav_path), model_name, language)
    except Exception:
        raw_path.unlink(missing_ok=True)
        wav_path.unlink(missing_ok=True)
        raise

    return {
        "id": item_id,
        "filename": original_name,
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model": model_name,
        "language": res["language"],
        "duration_proc": round(time.time() - start, 2),
        "text": res["text"],
        "segments": res["segments"],
        "audio_url": f"/api/audio/{item_id}",
    }


@app.post("/api/transcribe")
async def transcribe_audios(
    files: List[UploadFile] = File(...),
    model_name: str = Form(DEFAULT_MODEL),
    language: str = Form("fr"),
):
    if model_name not in MODELS:
        raise HTTPException(status_code=400, detail=f"Modèle inconnu : {model_name}")

    results, errors = [], []
    for file in files:
        # FFmpeg et Whisper sont bloquants : on les sort de la boucle d'événements
        # pour que le serveur reste disponible (historique, lecture audio...).
        try:
            item = await run_in_threadpool(_process, file, model_name, language)
        except AudioConversionError as e:
            errors.append({"filename": file.filename, "error": str(e)})
            continue
        except Exception as e:
            errors.append({"filename": file.filename, "error": f"Erreur lors de la transcription: {e}"})
            continue
        # Sauvegarde fichier par fichier : un échec plus loin ne fait rien perdre.
        history.add(item)
        results.append(item)

    if not results:
        raise HTTPException(status_code=500, detail="; ".join(e["error"] for e in errors))
    return {"status": "success", "count": len(results), "data": results, "errors": errors}


@app.get("/api/history")
async def get_history():
    return history.load()


@app.delete("/api/history/{item_id}")
async def delete_item(item_id: str):
    item_id = _check_id(item_id)
    history.remove(item_id)
    for d in (UPLOADS_DIR, CONVERTED_DIR):
        for f in d.glob(f"{item_id}*"):
            f.unlink(missing_ok=True)
    return {"status": "deleted"}


@app.get("/api/audio/{item_id}")
async def get_audio(item_id: str):
    item_id = _check_id(item_id)
    wav_path = CONVERTED_DIR / f"{item_id}.wav"
    if wav_path.exists():
        return FileResponse(wav_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio file not found")


@app.get("/api/export/{item_id}")
async def export_item(item_id: str, format: str = "txt"):
    item_id = _check_id(item_id)
    item = history.get(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if format == "json":
        content = json.dumps(item, ensure_ascii=False, indent=2)
        media_type = "application/json"
    elif format == "md":
        content = "# Transcription Audio WhatsApp\n\n"
        content += f"- **Fichier:** `{item['filename']}`\n"
        content += f"- **Date:** {item['timestamp']}\n"
        content += f"- **Modèle:** Whisper {item['model']}\n\n"
        content += f"## Texte\n\n{item['text']}\n\n"
        content += "## Horodatage\n\n"
        for s in item.get("segments", []):
            content += f"- `[{s['start']}s - {s['end']}s]` {s['text']}\n"
        media_type = "text/markdown"
    else:
        format = "txt"
        content = item["text"]
        media_type = "text/plain"

    filename = f"transcription_{item['filename']}.{format}"
    return Response(
        content=content,
        media_type=media_type,
        # filename* (RFC 5987) : supporte accents et caractères spéciaux sans casser l'en-tête.
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"},
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
