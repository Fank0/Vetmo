# Architecture (Agent 1, v1.0)

## Диаграмма

```text
OpenDota API
    |
    v
n8n workflows -----> PostgreSQL (source of truth)
                          |
                          v
                  Draft Scoring API (FastAPI, детерминированный)
                    |           |
                    v           v
              Qdrant (opt)   LLM (только объяснения)
                    \           /
                     v         v
                    Web UI (static + nginx)
```

## Принципы (для защиты)

1. **Статистика решает, LLM объясняет.** `score` считает `backend/app/scoring.py`. LLM получает готовые цифры и не может их менять.
2. **PostgreSQL — источник истины.** Герои, матчапы, патчи, sync_meta. Всё ранжирование — SQL + код, не векторный поиск.
3. **Qdrant опционален.** `ENABLE_RAG=false` → всё работает. Включается профилем `rag`: `docker compose --profile rag up`. Retrieval — только контекст для объяснений.
4. **n8n — весь ETL.** Первичная загрузка + периодическое обновление + запись `sync_meta`. Credentials только в n8n, в JSON их нет.
5. **Защита-first:** `docker compose up` поднимает postgres+backend+frontend+n8n за одну команду. Без Docker — локальный запуск backend (seed-fallback) + открытие `frontend/index.html`.

## Сервисы и порты (по .env.example)

| Сервис | Порт | Healthcheck |
|--------|------|-------------|
| postgres | 5432 | `pg_isready` |
| backend | 8000 | `GET /health` |
| frontend | 8080 | nginx 200 |
| n8n | 5678 | UI login |
| qdrant (profile rag) | 6333 | `GET /` |

## Формула scoring (MVP v1, задокументирована)

```text
Score(hero) = w_c*Counter + w_s*Synergy + w_r*RoleFit + w_m*Meta
defaults: w_c=0.55, w_s=0.15, w_r=0.15, w_m=0.15
```

- `Counter` — средний сглаженный винрейт против пиков врага:
  `smoothed = (wins + K*0.5)/(games + K)`, `K=50`.
  Взвешивание по `games`. Нет данных → 0.5 (нейтрально) + `low` confidence.
- `Synergy` (MVP): 0.5 заглушка (интерфейс расширяем, фиктивных оценок нет). Реализуется после сбора ally-статистики.
- `RoleFit`: 1.0 если `requested_roles` пусто или пересекается; 0.3 иначе. Роли только из OpenDota.
- `Meta`: сглаженный винрейт из `hero_stats` (patch='unknown' в MVP), иначе 0.5.
- `confidence`: сумма games по матчапам против врагов: ≥400 high, ≥100 medium, иначе low + caveat.

Ограничения: игнорирует порядок пиков, ранг, патч-детализацию в MVP; матчап ≠ причинность.

## Потоки данных

- **Initial load:** n8n `initial_load.json` или `python -m app.loader --once` → upsert heroes/hero_stats/matchups → `sync_meta.last_successful_sync=now()`.
- **Recommend:** UI → `POST /recommendations` → исключение picked/banned → SQL matchups → `scoring.py` → JSON → UI + `POST /explain` (template или LLM paraphrase).
- **RAG (после MVP):** `loader --index-rag` строит документы (драфт→текст) → embeddings → Qdrant `draft_scenarios` → `GET /similar-scenarios` возвращает ids+payload, подмешивается в `rag_context`.

## Что НЕ делать (границы MVP)

- Не управлять клиентом Dota, не обещать победу, не выдумывать патч/роли/цифры, не требовать всю историю матчей.
