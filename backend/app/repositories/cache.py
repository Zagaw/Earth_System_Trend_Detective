import hashlib
import json
from pathlib import Path
from time import time

from app.core.config import Settings


def raw_cache_file(settings: Settings, identity: dict[str, object]) -> Path:
    digest = hashlib.sha256(
        json.dumps(identity, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()[:20]
    parameter = str(identity.get("parameter", "unknown"))
    return settings.raw_dir / f"{parameter.lower()}-{digest}.json"


def read_fresh_cache(path: Path, ttl_seconds: int) -> dict | None:
    if not path.exists():
        return None
    age = time() - path.stat().st_mtime
    if age > ttl_seconds:
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_cache(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")
