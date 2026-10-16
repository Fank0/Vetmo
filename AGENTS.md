# AGENTS.md — как OpenCode используется в разработке (для защиты)

OpenCode — **инструмент разработки**, а не runtime-компонент драфтера.
На защите показать: историю промптов/сессий, этот файл, `opencode.json`,
и то, что каждая роль работала в своей папке по контрактам из `docs/api-contracts.md`.

## 6 ролей (номера = разделы ТЗ)

| № | Роль | Папка-владелец | Задачи |
|---|------|----------------|--------|
| 1 | Architect / Coordinator | `docs/`, `docker-compose.yml`, `.env.example`, `infra/` | 1.1–1.6 + интеграция 7.1–7.7 |
| 2 | Data Engineer | `backend/app/opendota_client.py`, `loader.py`, `infra/postgres/` | 2.1–2.7 |
| 3 | Draft Algorithm | `backend/app/scoring.py`, `models.py`, `main.py`, `backend/tests/` | 3.1–3.10 |
| 4 | n8n Workflow Engineer | `n8n/` | 4.1–4.7 |
| 5 | RAG / Qdrant Engineer | `backend/app/rag.py`, `infra/qdrant/` | 5.1–5.8, только после MVP |
| 6 | Frontend / UX Engineer | `frontend/` | 6.1–6.9 |

## Правила (обязательны для всех сессий)

1. Не менять общие контракты (`Hero`, `Matchup`, Draft Request/Response) без Агента 1.
2. Одна роль — одна папка. Чужие файлы только на чтение.
3. Реальные ключи только в локальном `.env` / credentials n8n. Коммитить только `.env.example`.
4. Матчап = статистическая ассоциация, не причинность. Не выдумывать патч/роли/цифры.
5. `score` считает только код (`scoring.py`), LLM его не меняет.
6. Qdrant опционален: `ENABLE_RAG=false` → всё работает без него.
7. Каждая сессия в конце: изменения, тесты, ограничения, следующий шаг.

## Пример запуска роли в OpenCode

```
# Агент 3 — Scoring API
opencode run "Роль: Agent 3 Draft Algorithm, задачи 3.1–3.10.
Контракты: docs/api-contracts.md. Владелец: backend/app/scoring.py, models.py, main.py.
Не менять контракты. В конце: отчёт + pytest backend/tests"
```

## Что показать на защите (OpenCode-трек)

- `opencode.json` + этот файл;
- `docs/development-plan.md` с разбивкой по агентам;
- git log по папкам (видно разделение труда);
- живой запуск: `docker compose up` → UI → рекомендации → объяснение без выдуманной статистики.
