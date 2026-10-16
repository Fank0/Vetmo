"""Новости игры для вкладки меню. Пока — курируемый fallback (источник: официальный блог Dota 2).
Прод-вариант: RSS/парсинг https://www.dota2.com/news + кэш; контракт не меняется.
"""
from __future__ import annotations

FALLBACK_NEWS: list[dict] = [
    {"id": "dota2-blog", "title": "Официальный блог Dota 2 — патчи и события",
     "summary": "Первоисточник новостей игры: обновления, патчи, ивенты.",
     "url": "https://www.dota2.com/news", "published_at": "2026-01-01T00:00:00Z", "source": "dota2.com"},
    {"id": "opendota", "title": "OpenDota — актуальная статистика героев",
     "summary": "Источник цифр для наших рекомендаций: винрейты и матчапы.",
     "url": "https://www.opendota.com/heroes", "published_at": "2026-01-01T00:00:00Z", "source": "opendota"},
    {"id": "liquipedia", "title": "Liquipedia — турниры и мета про-сцены",
     "summary": "Расписание турниров и пики про-команд для понимания меты.",
     "url": "https://liquipedia.net/dota2/Main_Page", "published_at": "2026-01-01T00:00:00Z", "source": "liquipedia"},
]


def get_news(limit: int = 10) -> list[dict]:
    return FALLBACK_NEWS[:max(1, min(limit, len(FALLBACK_NEWS)))]
