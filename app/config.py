import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
STATIC_DIR = BASE_DIR / "static"

DATA_DIR = Path(os.getenv("WT_DATA_DIR", BASE_DIR / "data"))
UPLOADS_DIR = DATA_DIR / "uploads"
CONVERTED_DIR = DATA_DIR / "converted"
HISTORY_FILE = DATA_DIR / "history.json"

MODELS = ("tiny", "base", "small", "medium")
DEFAULT_MODEL = os.getenv("WT_MODEL", "small")

for d in (UPLOADS_DIR, CONVERTED_DIR):
    d.mkdir(parents=True, exist_ok=True)
