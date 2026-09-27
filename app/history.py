import json
import threading

from .config import HISTORY_FILE

# Plusieurs requêtes peuvent écrire en même temps (threads) : un seul verrou suffit.
_lock = threading.Lock()


def load() -> list[dict]:
    if not HISTORY_FILE.exists():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []


def _save(items: list[dict]) -> None:
    # Écriture atomique : un crash en cours d'écriture ne corrompt pas l'historique.
    tmp = HISTORY_FILE.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(HISTORY_FILE)


def add(item: dict) -> None:
    with _lock:
        _save([item, *load()])


def remove(item_id: str) -> None:
    with _lock:
        _save([i for i in load() if i["id"] != item_id])


def get(item_id: str) -> dict | None:
    return next((i for i in load() if i["id"] == item_id), None)
