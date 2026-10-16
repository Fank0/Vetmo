"""OpenDota клиент. Владелец: Agent 2 (2.1–2.3).
Rate-limit + retry с экспоненциальной задержкой + обработка 429. Без выдумывания данных.
"""
from __future__ import annotations
import time
import logging
import httpx

log = logging.getLogger("opendota")


class OpenDotaClient:
    def __init__(self, base_url: str = "https://api.opendota.com/api", api_key: str = "",
                 timeout: float = 15.0, max_rps: float = 1.0, max_retries: int = 4):
        self.base = base_url.rstrip("/")
        self.key = api_key
        self.timeout = timeout
        self.min_interval = 1.0 / max_rps if max_rps > 0 else 0
        self.max_retries = max_retries
        self._last = 0.0
        self._client = httpx.Client(timeout=timeout, headers={"User-Agent": "dota2-drafter/1.0"})

    def _throttle(self) -> None:
        dt = time.monotonic() - self._last
        if dt < self.min_interval:
            time.sleep(self.min_interval - dt)

    def _get(self, path: str, params: dict | None = None) -> httpx.Response | None:
        params = dict(params or {})
        if self.key:
            params["api_key"] = self.key
        backoff = 1.0
        for attempt in range(self.max_retries):
            self._throttle()
            try:
                r = self._client.get(self.base + path, params=params)
                self._last = time.monotonic()
                if r.status_code == 429 or 500 <= r.status_code < 600:
                    log.warning("opendota %s -> %s, retry %d", path, r.status_code, attempt + 1)
                    time.sleep(backoff)
                    backoff *= 2
                    continue
                r.raise_for_status()
                return r
            except httpx.HTTPError as e:
                log.warning("opendota %s error: %s (try %d)", path, e, attempt + 1)
                time.sleep(backoff)
                backoff *= 2
        log.error("opendota %s failed after %d tries", path, self.max_retries)
        return None

    def get_heroes(self) -> list[dict]:
        r = self._get("/heroes")
        if r is None:
            return []
        try:
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def get_hero_stats(self) -> list[dict]:
        r = self._get("/heroStats")
        if r is None:
            return []
        try:
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception:
            return []

    def get_matchups(self, hero_id: int) -> list[dict]:
        r = self._get(f"/heroes/{hero_id}/matchups")
        if r is None:
            return []
        try:
            data = r.json()
            return data if isinstance(data, list) else []
        except Exception:
            return []

    @staticmethod
    def normalize_hero(raw: dict) -> dict | None:
        try:
            hid = int(raw.get("id", 0))
            if hid <= 0:
                return None
            roles = raw.get("roles") or []
            return {"id": hid, "name": str(raw.get("name", "")),
                    "localized_name": str(raw.get("localized_name", f"Hero {hid}")),
                    "roles": [str(x) for x in roles if x]}
        except Exception:
            return None

    @staticmethod
    def normalize_matchup(hero_id: int, raw: dict) -> dict | None:
        try:
            opp = int(raw.get("hero_id", raw.get("opponent_hero_id", 0)))
            g = int(raw.get("games_played", 0))
            w = int(raw.get("wins", 0))
            if opp <= 0 or opp == hero_id or g < 0 or w < 0 or w > g:
                return None
            return {"hero_id": hero_id, "opponent_hero_id": opp, "patch": "unknown",
                    "games_played": g, "wins": w, "win_rate": (w / g if g else None), "source": "opendota"}
        except Exception:
            return None
