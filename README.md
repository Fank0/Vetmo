# Dota 2 Drafter — статистический MVP + план на 6 агентов

Рекомендует героя для следующего пика по статистике OpenDota: контрпики, роли, мета, размер выборки.
**Статистика решает, LLM объясняет. Qdrant опционален.**

## Быстрый старт (для защиты — P0)

```bash
cp .env.example .env
docker compose up --build
# UI:       http://localhost:8080
# API docs: http://localhost:8000/docs
# n8n:      http://localhost:5678  (admin / из .env)
```

Без Docker (fallback, если Docker нет на машине):
```bash
py -3.12 -m pip install -r backend/requirements.txt
py -3.12 -m uvicorn app.main:app --app-dir backend --port 8000
# открыть frontend/index.html (?backend=http://localhost:8000)
py -3.12 -m pytest backend/tests -v
```

С Qdrant (только если векторный поиск реально нужен):
```bash
docker compose --profile rag up --build
```

## Что где (6 ролей)

| № | Роль | Папка | Вход |
|---|------|-------|------|
| 1 | Architect | `docs/`, `docker-compose.yml`, `infra/` | `docs/architecture.md` |
| 2 | Data Engineer | `backend/app/opendota_client.py`, `loader.py` | `docs/data-sources.md` |
| 3 | Draft Algorithm | `backend/app/scoring.py`, `main.py` | `docs/api-contracts.md` |
| 4 | n8n | `n8n/workflows/` | `n8n/README.md` |
| 5 | RAG (optional) | `backend/app/rag.py`, `infra/qdrant/` | `infra/qdrant/README.md` |
| 6 | Frontend | `frontend/` | `frontend/README.md` |

Контракты заморожены: `docs/api-contracts.md`. Правила: `AGENTS.md`. План: `docs/development-plan.md`. Чеклист защиты: `docs/defense-checklist.md`.

## API (пример)

```bash
curl -X POST http://localhost:8000/recommendations -H "Content-Type: application/json" -d "{\"radiant_picks\":[1],\"dire_picks\":[8,6],\"team_to_pick\":\"radiant\",\"limit\":5}"
```

Ответ: `recommendations[{hero_id, score, confidence, reasons[{type, against_hero_id, summary, games_played}], caveats}]` + `data_updated_at` + `rag_context`.

## Формула

`Score = 0.55*Counter + 0.15*Synergy + 0.15*RoleFit + 0.15*Meta`, сглаживание `K=50`, confidence по сумме игр (≥400 high / ≥100 medium / иначе low). Подробнее: `docs/architecture.md`, код: `backend/app/scoring.py`.

## Definition of Done (MVP)

1. `docker compose up` поднимает postgres+backend+frontend+n8n. 2. Загрузка OpenDota в Postgres (n8n или `loader --once`). 3. `POST /recommendations` воспроизводим, picked/banned исключены. 4. Score считает код, LLM не меняет цифр. 5. Тесты зелёные. 6. Без Qdrant всё работает.
