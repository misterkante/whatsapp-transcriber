import os
import shutil
import subprocess
import time
import json
import uuid
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import whisper

app = FastAPI(title="WhatsApp Audio Transcriber Pro", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
UPLOADS_DIR = os.path.join(BASE_DIR, "data", "uploads")
CONVERTED_DIR = os.path.join(BASE_DIR, "data", "converted")
DB_FILE = os.path.join(BASE_DIR, "data", "history.json")
STATIC_DIR = os.path.join(BASE_DIR, "static")

os.makedirs(UPLOADS_DIR, exist_ok=True)
os.makedirs(CONVERTED_DIR, exist_ok=True)
os.makedirs(STATIC_DIR, exist_ok=True)

# Loaded whisper models cache
MODELS = {}

def get_model(model_name: str = "small"):
    if model_name not in MODELS:
        print(f"Loading Whisper model '{model_name}'...")
        MODELS[model_name] = whisper.load_model(model_name)
    return MODELS[model_name]

def load_history():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []

def save_history(history):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=2)

@app.post("/api/transcribe")
async def transcribe_audios(
    files: List[UploadFile] = File(...),
    model_name: str = Form("small"),
    language: str = Form("fr")
):
    history = load_history()
    results = []
    
    model = get_model(model_name)

    for file in files:
        item_id = str(uuid.uuid4())
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        original_name = file.filename or "audio_whatsapp.ogg"
        ext = os.path.splitext(original_name)[1].lower() or ".ogg"
        
        raw_path = os.path.join(UPLOADS_DIR, f"{item_id}{ext}")
        wav_path = os.path.join(CONVERTED_DIR, f"{item_id}.wav")

        # Save uploaded raw file
        with open(raw_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Convert to 16kHz mono WAV via ffmpeg
        try:
            subprocess.run([
                "ffmpeg", "-y", "-i", raw_path,
                "-ar", "16000", "-ac", "1", wav_path
            ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur de conversion audio avec FFmpeg: {str(e)}")

        # Transcribe with Whisper
        try:
            start_time = time.time()
            transcribe_kwargs = {}
            if language and language != "auto":
                transcribe_kwargs["language"] = language

            res = model.transcribe(wav_path, **transcribe_kwargs)
            duration_proc = round(time.time() - start_time, 2)
            
            transcript_text = res.get("text", "").strip()
            detected_lang = res.get("language", language)

            # Get segments with timestamps
            segments = []
            for seg in res.get("segments", []):
                segments.append({
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": seg["text"].strip()
                })

            item_data = {
                "id": item_id,
                "filename": original_name,
                "timestamp": timestamp,
                "model": model_name,
                "language": detected_lang,
                "duration_proc": duration_proc,
                "text": transcript_text,
                "segments": segments,
                "audio_url": f"/api/audio/{item_id}"
            }

            results.append(item_data)
            history.insert(0, item_data)

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Erreur lors de la transcription: {str(e)}")

    save_history(history)
    return {"status": "success", "count": len(results), "data": results}

@app.get("/api/history")
async def get_history():
    return load_history()

@app.delete("/api/history/{item_id}")
async def delete_item(item_id: str):
    history = load_history()
    new_history = [item for item in history if item["id"] != item_id]
    save_history(new_history)
    
    # Cleanup files
    for d in [UPLOADS_DIR, CONVERTED_DIR]:
        for f in os.listdir(d):
            if f.startswith(item_id):
                try:
                    os.remove(os.path.join(d, f))
                except Exception:
                    pass
    return {"status": "deleted"}

@app.get("/api/audio/{item_id}")
async def get_audio(item_id: str):
    wav_path = os.path.join(CONVERTED_DIR, f"{item_id}.wav")
    if os.path.exists(wav_path):
        return FileResponse(wav_path, media_type="audio/wav")
    raise HTTPException(status_code=404, detail="Audio file not found")

@app.get("/api/export/{item_id}")
async def export_item(item_id: str, format: str = "txt"):
    history = load_history()
    item = next((i for i in history if i["id"] == item_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    filename = f"transcription_{item['filename']}.{format}"
    
    if format == "json":
        content = json.dumps(item, ensure_ascii=False, indent=2)
        media_type = "application/json"
    elif format == "md":
        content = f"# Transcription Audio WhatsApp\n\n"
        content += f"- **Fichier:** `{item['filename']}`\n"
        content += f"- **Date:** {item['timestamp']}\n"
        content += f"- **Modèle:** Whisper {item['model']}\n\n"
        content += f"## Texte\n\n{item['text']}\n\n"
        content += f"## Horodatage\n\n"
        for s in item.get("segments", []):
            content += f"- `[{s['start']}s - {s['end']}s]` {s['text']}\n"
        media_type = "text/markdown"
    else:
        content = item['text']
        media_type = "text/plain"

    return HTMLResponse(content=content, headers={"Content-Disposition": f"attachment; filename=\"{filename}\""})

# Serve static frontend
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
