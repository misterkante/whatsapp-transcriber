import whisper

_models = {}


def _get_model(name: str):
    if name not in _models:
        print(f"Loading Whisper model '{name}'...")
        _models[name] = whisper.load_model(name)
    return _models[name]


def transcribe(wav_path: str, model_name: str, language: str | None) -> dict:
    """Renvoie {text, language, segments} pour un fichier WAV 16 kHz."""
    kwargs = {"language": language} if language and language != "auto" else {}
    res = _get_model(model_name).transcribe(wav_path, **kwargs)
    return {
        "text": res.get("text", "").strip(),
        "language": res.get("language", language),
        "segments": [
            {"start": round(s["start"], 2), "end": round(s["end"], 2), "text": s["text"].strip()}
            for s in res.get("segments", [])
        ],
    }
