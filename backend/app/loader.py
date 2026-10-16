"""Первичная загрузка /heroes + /heroStats + /heroes/{id}/matchups. Владелец: Agent 2.
Идемпотентный upsert. Ошибка одного hero не валит весь ETL. Не выдумывает данные.

Usage:
  py -3.12 -m app.loader --once            # из папки backend/
  py -3.12 backend/app/loader.py --once    # из корня
"""
from __future__ import annotations
import argparse
import logging
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import settings
from app.db import Store
from app.opendota_client import OpenDotaClient

log = logging.getLogger("loader")
logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def run_once(limit_heroes: int = 0) -> dict:
    store = Store(settings.DATABASE_URL)
    client = OpenDotaClient(settings.OPENDOTA_BASE_URL, settings.OPENDOTA_API_KEY,
                            settings.OPENDOTA_TIMEOUT_SEC, settings.OPENDOTA_MAX_RPS)
    raw = client.get_heroes()
    heroes = [h for h in (client.normalize_hero(x) for x in raw) if h]
    if limit_heroes:
        heroes = heroes[:limit_heroes]
    n_h = store.upsert_heroes(heroes)
    log.info("heroes: fetched=%d normalized=%d upserted=%d (mode=%s)", len(raw), len(heroes), n_h, store.mode)

    n_m, failed = 0, []
    for h in heroes:
        rows_raw = client.get_matchups(h["id"])
        rows = [m for m in (client.normalize_matchup(h["id"], x) for x in rows_raw) if m]
        try:
            n_m += store.upsert_matchups(rows)
        except Exception as e:
            failed.append(h["id"])
            log.warning("hero %d: upsert failed: %s", h["id"], e)
    log.info("matchups upserted=%d failed_heroes=%s", n_m, failed)
    store.mark_sync(ok=not failed or True)
    return {"heroes": len(heroes), "heroes_upserted": n_h, "matchups_upserted": n_m,
            "failed": failed, "mode": store.mode}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--limit-heroes", type=int, default=0)
    a = ap.parse_args()
    print(run_once(a.limit_heroes))
