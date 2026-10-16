# Defense checklist — что показать (5–7 минут)

1. **Архитектура (30 сек):** открыть `docs/architecture.md` схему. Проговорить: «Статистика решает, LLM объясняет; Postgres — истина; Qdrant опционален».
2. **Docker Compose (60 сек):** `docker compose ps` — 4 сервиса. Если Docker нет на машине защиты — показать `docker-compose.yml` + скриншот запущенных сервисов + fallback (backend локально + UI).
3. **UI (2 мин — главное):** `http://localhost:8080`:
   - выбрать Radiant 2 пика, Dire 2 пика, 2 бана, team_to_pick=radiant;
   - нажать «Рекомендовать» → топ-10 со score, confidence-бейджем, games_played, reasons;
   - показать: выбранные/забаненные исключены; поиск + фильтр ролей; warning при low confidence; loading/error states.
4. **API (60 сек):** Swagger `http://localhost:8000/docs` → `POST /recommendations` с тем же JSON → одинаковый результат (воспроизводимость). `GET /heroes` — роли только из OpenDota.
5. **n8n (60 сек):** `http://localhost:5678` → импортированные `initial_load`, `periodic_update` → executions log → `SELECT * FROM sync_meta` в postgres.
6. **OpenCode (30 сек):** `opencode.json` + `AGENTS.md` + `git log --stat` по папкам (6 ролей). Сказать: «OpenCode — инструмент разработки, не runtime».
7. **Qdrant (только если работает):** `docker compose --profile rag up` → `GET /similar-scenarios` возвращает ids. Подчеркнуть: «Без него MVP работает — `rag_context: []`». Если не поднят — честно сказать «отложен до RAG-этапа по плану §5.8».

## Вопросы комиссии (заготовки)

- «Почему не сырой winrate?» → сглаживание `K=50` + штраф confidence при games<100, формула в `scoring.py`.
- «Матчап = контрит?» → нет, ассоциация; показываем games_played + caveats + patch.
- «LLM выдумывает?» → нет: score считает код, LLM только перефразирует факты (`llm_generated` флаг).
- «Где патч?» → `patch='unknown'`, пока OpenDota не даёт разбивку; не выдумываем.
