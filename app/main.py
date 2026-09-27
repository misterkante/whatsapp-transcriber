import shutil
import time
import json
import uuid
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from fastapi.middleware.cors import CORSMiddleware

from . import history, transcriber
from .audio import AudioConversionError, to_wav
from .config import CONVERTED_DIR, DEFAULT_MODEL, STATIC_DIR, UPLOADS_DIR

app = FastAPI(title="WhatsApp Audio Transcriber", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.post("/api/transcribe")
async def transcribe_audios(
    files: List[UploadFile] = File(...),
    model_name: str = Form(DEFAULT_MODEL),
    language: str = Form("fr"),
):
    items = history.load()
    results = []

    for file in files:
        item_id = str(uuid.uuid4())
        original_name = file.filename or "audio_whatsapp.ogg"
        ext = "." + original_name.rsplit(".", 1)[-1].lower() if "." in original_name else ".ogg"
        raw_path = UPLOADS_DIR / f"{item_id}{ext}"
        wav_path = CONVERTED_DIR / f"{item_id}.wav"

        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            to_wav(raw_path, wav_path)
        except AudioConversionError as e:
            raise HTTPException(status_code=500, detail=str(e))

        try:
            start = time.time()
            res = transcriber.transcribe(str(wav_path), model_name, language)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la transcription: {e}")

        item = {
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
        results.append(item)
        items.insert(0, item)

    history.save(items)
    return {"status": "success", "count": len(results), "data": results}


@app.get("/api/history")
async def get_history():
    return history.load()


@app.delete("/api/history/{item_id}")
async def delete_item(item_id: str):
    history.save([i for i in history.load() if i["id"] != item_id])
    for d in (UPLOADS_DIR, CONVERTED_DIR):
        for f in d.glob(f"{item_id}*"):
            f.unlink(missing_ok=True)
    return {"status": "deleted"}


@app.get("/api/audio/{item_id}")
async def get_audio(item_id: str):
    wav_path = CONVERTED_DIR / f"{item_id}.wav"
    if wav_path.exists():
        return FileResponse(wav_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio file not found")


@app.get("/api/export/{item_id}")
async def export_item(item_id: str, format: str = "txt"):
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
        headers={"Content-Disposition": f"attachment; filename=\"{filename}\""},
    )


app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
