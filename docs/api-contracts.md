# API Contracts (v1.0 — frozen by Agent 1)

Контракты обязательны для всех агентов. Изменение — только через Agent 1.
Примеры значений иллюстративны; реальные ответы строятся из БД.

## 1. Hero

```json
{
  "id": 1,
  "name": "npc_dota_hero_antimage",
  "localized_name": "Anti-Mage",
  "roles": ["Carry", "Escape", "Nuker"],
  "updated_at": "2026-01-01T00:00:00Z"
}
```

- `id`: OpenDota hero id (int, >0).
- `roles`: только из источника (`/heroes`). Не выдумывать.
- `updated_at`: ISO-8601 UTC.

## 2. Matchup

```json
{
  "hero_id": 1,
  "opponent_hero_id": 2,
  "patch": "unknown",
  "games_played": 100,
  "wins": 53,
  "win_rate": 0.53,
  "source": "opendota",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

Правила:
- `patch="unknown"`, если источник не даёт патч. Не выдумывать.
- `win_rate = wins / games_played` (null при games_played=0).
- PK: `(hero_id, opponent_hero_id, patch)`.
- Матчап = ассоциация, не причинность. Всегда отдавать `games_played`.

## 3. Draft Request — POST /recommendations

```json
{
  "radiant_picks": [1, 2],
  "dire_picks": [3, 4],
  "radiant_bans": [5],
  "dire_bans": [6],
  "team_to_pick": "radiant",
  "requested_roles": ["Support"],
  "limit": 10
}
```

Валидация (422 при нарушении):
- все ID — int >0, должны существовать в `heroes` (иначе 422 unknown_hero_id);
- дубли внутри picks/bans запрещены; пересечения picks↔bans запрещены;
- `team_to_pick`: `radiant` | `dire`;
- `requested_roles`: [] = без фильтра;
- `limit`: 1..25, default 10.

## 4. Draft Response

```json
{
  "recommendations": [
    {
      "hero_id": 7,
      "score": 0.72,
      "confidence": "medium",
      "reasons": [
        {
          "type": "matchup",
          "against_hero_id": 3,
          "summary": "Положительная статистика матчапа",
          "games_played": 250
        }
      ],
      "caveats": ["Размер выборки и патч влияют на надёжность"]
    }
  ],
  "data_updated_at": "2026-01-01T00:00:00Z",
  "rag_context": [],
  "meta": {"total_candidates": 118, "excluded": 6, "engine": "statistical-mvp-v1"}
}
```

- `score`: 0..1, считает только `scoring.py`. LLM не меняет.
- `confidence`: `high` (≥400 игр суммарно) / `medium` (≥100) / `low` (иначе).
- `reasons[].type`: `matchup` | `role` | `meta` | `synergy`.
- `caveats`: обязательно при low confidence / unknown patch.
- `rag_context`: [] когда `ENABLE_RAG=false` или Qdrant недоступен.
- `data_updated_at`: из `sync_meta.last_successful_sync` или max(updated_at).

## 5. Explain — POST /explain

Вход: тот же Draft Request + `hero_id`.
Выход: `{ "hero_id": 7, "explanation": "...", "facts_used": {...}, "llm_generated": false }`.
- `explanation` строится из фактов ответа /recommendations.
- Если задан LLM-провайдер — модель лишь перефразирует, цифры не меняет.
- `llm_generated=false` при template-fallback.

## 6. Ошибки

```json
{ "detail": [{"loc": ["body","radiant_picks"], "msg": "duplicate hero id 1", "type": "value_error"}] }
```

- 422 — ошибка валидации; 404 — неизвестный роут; 503 — БД недоступна (с fallback на seed в MVP).

## 7. Дополнительные endpoints меню (v1.1)

- `GET /heroes` → теперь включает `name` (`npc_dota_hero_*`) для портретов Steam CDN в UI.
- `GET /meta/top?limit=10` → `{ top: [{hero_id, localized_name, roles, win_rate}], data_updated_at, db_mode }`, сортировка по `win_rate` desc. Цифры из `hero_stats`/seed, не хардкод.
- `GET /news?limit=10` → `{ news: [{id, title, summary, url, published_at, source}] }`. Пока fallback-лента, прод — RSS dota2.com.
