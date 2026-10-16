# Data sources — OpenDota (Agent 2)

Доки: https://docs.opendota.com/ · Base: `https://api.opendota.com/api`

## Эндпоинты MVP

| Endpoint | Использование | Поля |
|----------|---------------|------|
| `GET /heroes` | id, name, localized_name, roles | `id, name, localized_name, roles[], primary_attr, attack_type` |
| `GET /heroStats` | winrate/pickrate общий | `id, win/total? pro_win/pro_pick, ...` — схему проверить кодом, хранить как есть + нормализовать |
| `GET /heroes/{id}/matchups` | матчапы | `hero_id, wins, games_played` (win_rate считаем сами) |

Опционально (после MVP): `/heroes/{id}/durations`, `/proMatches`, `/publicMatches`.

## Лимиты и надёжность

- Бесплатный API **не безлимитный**. Клиент (`opendota_client.py`):
  - `MAX_RPS=1.0` (token bucket), `TIMEOUT=15s`;
  - retry с экспоненциальной задержкой на 429/5xx (до 4 попыток);
  - `User-Agent: dota2-drafter/1.0`, опциональный `api_key`;
  - логирование ошибок без секретов; ошибка одного hero не валит весь ETL.
- Кэширование: n8n хранит `last_successful_sync`, повторный запуск — upsert (идемпотентно).
- Пустые/битые ответы: пропускать с логом, не выдумывать. `patch='unknown'`, пока API не даёт патч-разбивку.

## Нормализация (loader.py)

- `heroes`: upsert по `id`.
- `hero_stats`: `win_rate = wins/games` если games>0 иначе NULL; upsert `(hero_id, patch)`.
- `matchups`: `win_rate = wins/games`; upsert `(hero_id, opponent, patch)`; `CHECK(hero_id <> opponent)`.
- `sync_meta.last_successful_sync` — только после полного успеха; ошибки — в `sync_errors` (лог + таблица/ключ).

## Проверка схемы перед кодом

```bash
curl 'https://api.opendota.com/api/heroes' | head -c 500
curl 'https://api.opendota.com/api/heroes/1/matchups' | head -c 500
```
