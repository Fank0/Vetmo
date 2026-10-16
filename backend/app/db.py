"""Доступ к PostgreSQL с graceful fallback на seed (для демо без Docker).
Агент 2: ETL пишет сюда через upsert; Агент 3: scoring читает отсюда.
"""
from __future__ import annotations
from datetime import datetime, timezone

from . import seed
from .scoring import HeroRow, MatchupRow

try:
    import psycopg
    _HAS_PG = True
except Exception:
    _HAS_PG = False


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class Store:
    def __init__(self, dsn: str = ""):
        self.dsn = dsn
        self.mode = "seed"
        self.conn = None
        if dsn and _HAS_PG:
            try:
                self.conn = psycopg.connect(dsn, connect_timeout=3)
                self.conn.execute("SELECT 1")
                self.mode = "postgres"
            except Exception:
                self.conn = None
                self.mode = "seed"

    # --- reads (Agent 3) ---
    def heroes(self) -> list[HeroRow]:
        if self.mode == "postgres" and self.conn is not None:
            try:
                rows = self.conn.execute("SELECT id, name, localized_name, roles FROM heroes").fetchall()
                return [HeroRow(id=r[0], localized_name=r[2], roles=list(r[3] or []), name=r[1] or "") for r in rows]
            except Exception:
                pass
        return [HeroRow(id=h["id"], localized_name=h["localized_name"], roles=h["roles"], name=h.get("name", "")) for h in seed.SEED_HEROES]

    def hero_map(self) -> dict[int, HeroRow]:
        return {h.id: h for h in self.heroes()}

    def matchup(self, hero_id: int, opp_id: int) -> MatchupRow | None:
        if self.mode == "postgres" and self.conn is not None:
            try:
                r = self.conn.execute(
                    "SELECT hero_id, opponent_hero_id, games_played, wins FROM matchups "
                    "WHERE hero_id=%s AND opponent_hero_id=%s ORDER BY games_played DESC LIMIT 1",
                    (hero_id, opp_id)).fetchone()
                if r and r[2]:
                    return MatchupRow(hero_id=r[0], opponent_hero_id=r[1], games_played=r[2], wins=r[3])
            except Exception:
                pass
        key = (hero_id, opp_id)
        if key in seed.SEED_MATCHUPS:
            w, g = seed.SEED_MATCHUPS[key]
            return MatchupRow(hero_id=hero_id, opponent_hero_id=opp_id, games_played=g, wins=w)
        return None

    def meta_wr(self, hero_id: int) -> float | None:
        if self.mode == "postgres" and self.conn is not None:
            try:
                r = self.conn.execute(
                    "SELECT win_rate FROM hero_stats WHERE hero_id=%s ORDER BY games_played DESC LIMIT 1",
                    (hero_id,)).fetchone()
                if r and r[0] is not None:
                    return float(r[0])
            except Exception:
                pass
        return seed.SEED_META.get(hero_id)

    def data_updated_at(self) -> str:
        if self.mode == "postgres" and self.conn is not None:
            try:
                r = self.conn.execute("SELECT value FROM sync_meta WHERE key='last_successful_sync'").fetchone()
                if r and r[0] not in (None, "never", ""):
                    return str(r[0])
                r2 = self.conn.execute("SELECT max(updated_at) FROM heroes").fetchone()
                if r2 and r2[0]:
                    return str(r2[0])
            except Exception:
                pass
        return seed.NOW

    # --- writes (Agent 2) ---
    def upsert_heroes(self, heroes: list[dict]) -> int:
        if self.mode != "postgres" or self.conn is None:
            return 0
        n = 0
        with self.conn.cursor() as cur:
            for h in heroes:
                cur.execute(
                    "INSERT INTO heroes(id, name, localized_name, roles, updated_at) VALUES (%s,%s,%s,%s,now()) "
                    "ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, localized_name=EXCLUDED.localized_name, "
                    "roles=EXCLUDED.roles, updated_at=now()", 
                    (h["id"], h.get("name", ""), h.get("localized_name", ""), h.get("roles", [])))
                n += 1
        self.conn.commit()
        return n

    def upsert_matchups(self, rows: list[dict]) -> int:
        if self.mode != "postgres" or self.conn is None:
            return 0
        n = 0
        with self.conn.cursor() as cur:
            for m in rows:
                g, w = int(m.get("games_played", 0)), int(m.get("wins", 0))
                wr = (w / g) if g else None
                cur.execute(
                    "INSERT INTO matchups(hero_id, opponent_hero_id, patch, games_played, wins, win_rate, source, updated_at) "
                    "VALUES (%s,%s,%s,%s,%s,%s,%s,now()) ON CONFLICT (hero_id, opponent_hero_id, patch) DO UPDATE SET "
                    "games_played=EXCLUDED.games_played, wins=EXCLUDED.wins, win_rate=EXCLUDED.win_rate, updated_at=now()",
                    (m["hero_id"], m["opponent_hero_id"], m.get("patch", "unknown"), g, w, wr, m.get("source", "opendota")))
                n += 1
        self.conn.commit()
        return n

    def mark_sync(self, ok: bool = True) -> None:
        if self.mode != "postgres" or self.conn is None:
            return
        try:
            self.conn.execute(
                "INSERT INTO sync_meta(key,value,updated_at) VALUES ('last_successful_sync',%s,now()) "
                "ON CONFLICT (key) DO UPDATE SET value=EXCLUDED.value, updated_at=now()",
                (_now() if ok else "error",))
            self.conn.commit()
        except Exception:
            pass
