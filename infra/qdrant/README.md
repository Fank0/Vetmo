# Qdrant (Agent 5) — OPTIONAL, только после MVP

## Статус
MVP работает **без Qdrant** (`ENABLE_RAG=false`, `rag_context: []`). Не делать обязательным (§5.8 ТЗ).

## Включение
```bash
docker compose --profile rag up qdrant
# .env: ENABLE_RAG=true, QDRANT_URL=http://localhost:6333
```

## Коллекция `draft_scenarios`
- vectors: dim 384 (hash-embedding fallback в `backend/app/rag.py`; прод: зафиксировать embedding-модель и dim здесь).
- payload: `{ hero_ids: int[], patch: str, roles: str[], source: str, updated_at: str, text: str }`.
- создать:
```bash
curl -X PUT http://localhost:6333/collections/draft_scenarios -H "Content-Type: application/json" -d "{\"vectors\":{\"size\":384,\"distance\":\"Cosine\"}}"
```

## Индексация / поиск
- Индексация: будущий n8n Workflow C или `loader --index-rag` (не перезаписывать неизменённые документы).
- Поиск: `GET /similar-scenarios?radiant=1,2&dire=3&team=radiant` → `[{id, score, payload}]`, подмешивается в `DraftResponse.rag_context`.
- Тесты (§5.7): пустая коллекция → `[]`; Qdrant down → `[]` без падения API; устаревший patch виден в payload.

## Сравнение пользы (§5.8)
Замерить: топ-k совпадение рекомендаций с/без RAG на исторических драфтах. Если пользы нет — оставить опциональным.
