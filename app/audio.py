import subprocess
from pathlib import Path


class AudioConversionError(Exception):
    pass


def to_wav(src: Path, dst: Path) -> None:
    """Convertit un audio (ogg/opus WhatsApp, mp3, m4a...) en WAV 16 kHz mono."""
    try:
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(src), "-ar", "16000", "-ac", "1", str(dst)],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        raise AudioConversionError(f"Erreur de conversion audio avec FFmpeg : {e}") from e
