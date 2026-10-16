"""RAG / Qdrant retrieval — строго опционален. Владелец: Agent 5.
MVP работает с ENABLE_RAG=false и без Qdrant (DoD №10).
Когда Qdrant доступен: ищет похожие сценарии драфта, возвращает ids+payload.
Никогда не подменяет SQL-scoring.
"""
from __future__ import annotations
import hashlib
import httpx


def _embed(text: str, dim: int = 384) -> list[float]:
    """Детерминированный hash-embedding (fallback, пока нет embedding-модели).
    Прод-замена (5.3): задокументировать модель и dim в infra/qdrant/README.md."""
    vec = []
    for i in range(dim):
        h = hashlib.sha256(f"{text}:{i}".encode()).hexdigest()
        vec.append((int(h[:8], 16) % 2000 - 1000) / 1000.0)
    norm = sum(x * x for x in vec) ** 0.5 or 1.0
    return [x / norm for x in vec]


def draft_text(radiant: list[int], dire: list[int], team: str) -> str:
    return f"radiant {' '.join(map(str, radiant))} vs dire {' '.join(map(str, dire))} to pick {team}"


def search_similar(qdrant_url: str, collection: str, radiant: list[int], dire: list[int],
                   team: str, limit: int = 3, timeout: float = 3.0) -> list[dict]:
    if not qdrant_url:
        return []
    try:
        vec = _embed(draft_text(radiant, dire, team))
        r = httpx.post(f"{qdrant_url.rstrip('/')}/collections/{collection}/points/search",
                       json={"vector": vec, "limit": limit, "with_payload": True}, timeout=timeout)
        if r.status_code == 404:
            return []  # коллекция не создана — честно пусто
        r.raise_for_status()
        out = []
        for p in r.json().get("result", []):
            out.append({"id": p.get("id"), "score": round(float(p.get("score", 0)), 4),
                        "payload": p.get("payload", {})})
        return out
    except Exception:
        return []  # Qdrant недоступен — MVP продолжает работать
