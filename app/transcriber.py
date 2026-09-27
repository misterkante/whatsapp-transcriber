import threading

from faster_whisper import WhisperModel

from .config import CPU_THREADS

# Un seul modèle en mémoire à la fois : changer de modèle libère le précédent.
_model: WhisperModel | None = None
_model_name: str | None = None
# CTranslate2 utilise déjà tous les cœurs pour un fichier : on sérialise les appels.
_lock = threading.Lock()


def _get_model(name: str) -> WhisperModel:
    global _model, _model_name
    if _model_name != name:
        print(f"Chargement du modèle Whisper '{name}' (CPU, int8)...")
        _model = WhisperModel(name, device="cpu", compute_type="int8", cpu_threads=CPU_THREADS)
        _model_name = name
    return _model


def transcribe(wav_path: str, model_name: str, language: str | None) -> dict:
    """Renvoie {text, language, segments} pour un fichier WAV 16 kHz."""
    lang = language if language and language != "auto" else None
    with _lock:
        segments, info = _get_model(model_name).transcribe(
            wav_path, language=lang, beam_size=5, vad_filter=True
        )
        # `segments` est un générateur : la transcription se fait pendant l'itération.
        segments = [
            {"start": round(s.start, 2), "end": round(s.end, 2), "text": s.text.strip()}
            for s in segments
        ]
    return {
        "text": " ".join(s["text"] for s in segments).strip(),
        "language": info.language,
        "segments": segments,
    }
