# Development plan — 6 агентов + интеграция (Agent 1)

## Порядок (рекомендованный §11 ТЗ)

1. **Agent 1 Architect** — DONE в этом коммите: структура, контракты, compose, docs.
2. **Agent 2 Data Engineer (2.1–2.7)** — `opendota_client.py`, `loader.py`, `infra/postgres/`. Критерий: чистая БД → load → reload без дубликатов + `pytest backend/tests/test_loader.py`.
3. **Agent 3 Draft Algorithm (3.1–3.10)** — `scoring.py`, `models.py`, `main.py`. Критерий: воспроизводимость, исключение picked/banned, confidence при малых данных + `pytest backend/tests/`.
4. **Agent 4 n8n (4.1–4.7)** — импорт `n8n/workflows/*.json` в чистый n8n, ручной запуск, проверка `sync_meta`.
5. **Agent 6 Frontend (6.1–6.9)** — UI на моках → подключение к `POST /recommendations`. Критерий: нельзя выбрать героя дважды, видны score/confidence/games.
6. **Agent 5 RAG (5.1–5.8)** — только после MVP: коллекция `draft_scenarios`, `rag.py`, сравнение с/без RAG. Не делать обязательным.
7. **Agent 1 Integration (7.1–7.7)** — `docker compose up --build`, README на чистом окружении, fix тестов.

## Доска для защиты (P0)

- [ ] `docker compose up --build` → postgres ✅ backend ✅ frontend ✅ n8n ✅
- [ ] UI (8080): пики/баны двух команд → топ-10 → score bar + confidence + games + reasons
- [ ] API (8000): `/health`, `/heroes`, `/recommendations`, `/explain` отвечают
- [ ] n8n (5678): import workflows → manual run → данные в postgres
- [ ] VS Code: F5 (debug backend), tasks (up/test/loader)
- [ ] OpenCode-трек: `opencode.json` + `AGENTS.md` + git log по папкам
- [ ] Qdrant: `docker compose --profile rag up` → `/similar-scenarios` непусто; без профиля — `rag_context: []`, MVP работает

## Команды

```bash
cp .env.example .env
docker compose up --build          # P0 всё
docker compose --profile rag up    # + Qdrant
# Без Docker (fallback):
py -3.12 -m pip install -r backend/requirements.txt
py -3.12 -m uvicorn app.main:app --app-dir backend --port 8000
# открыть frontend/index.html (BACKEND_URL=http://localhost:8000)
py -3.12 -m pytest backend/tests -v
```
