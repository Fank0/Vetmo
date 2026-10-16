# n8n (Agent 4) — ETL и обновление статистики

## Импорт (чистый n8n)
1. `http://localhost:5678` → login из `.env` (`N8N_BASIC_AUTH_*`).
2. Workflows → Import from File → `n8n/workflows/initial_load.json`, `periodic_update.json`.
3. Credentials → создать **Postgres** (host=postgres, db/user/pass из `.env`) и привязать к узлам `Postgres *`.
4. Переменные окружения уже проброшены compose: `OPENDOTA_BASE_URL`, `BACKEND_URL`.
5. Запустить вручную: Execute Workflow → проверить Executions + `SELECT * FROM sync_meta` в postgres.

## Расписания
- `initial_load`: раз в 24ч (heroes + matchups loop). Повторный запуск безопасен (upsert).
- `periodic_update`: раз в 6ч (heroStats + mark sync + backend health).

## Ошибки и лимиты
- HTTP-узлы: retry 4, backoff; 429 не валит workflow — видно в Executions log.
- **Секреты:** API-ключи только в n8n Credentials / ENV. В JSON их нет (проверка перед коммитом).
- RAG-индексация (`Workflow C` из плана) — после MVP, отдельным workflow, включается флагом `ENABLE_RAG`.

## Альтернатива без n8n (fallback для защиты)
```bash
py -3.12 -m app.loader --once   # из папки backend/
```
