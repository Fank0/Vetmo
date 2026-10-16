-- Dota 2 Drafter — init schema (idempotent)
-- Источник истины: PostgreSQL. Qdrant — только опциональный RAG.
-- Совместимо с контрактами docs/api-contracts.md

CREATE TABLE IF NOT EXISTS heroes (
  id            INTEGER PRIMARY KEY,
  name          TEXT NOT NULL,              -- npc_dota_hero_*
  localized_name TEXT NOT NULL,
  roles         TEXT[] NOT NULL DEFAULT '{}',
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS hero_stats (
  hero_id      INTEGER NOT NULL REFERENCES heroes(id) ON DELETE CASCADE,
  patch        TEXT NOT NULL DEFAULT 'unknown',
  games_played INTEGER NOT NULL DEFAULT 0,
  wins         INTEGER NOT NULL DEFAULT 0,
  win_rate     DOUBLE PRECISION,             -- wins/games_played, NULL если games=0
  pick_rate    DOUBLE PRECISION,
  source       TEXT NOT NULL DEFAULT 'opendota',
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (hero_id, patch)
);

CREATE TABLE IF NOT EXISTS matchups (
  hero_id          INTEGER NOT NULL REFERENCES heroes(id) ON DELETE CASCADE,
  opponent_hero_id INTEGER NOT NULL REFERENCES heroes(id) ON DELETE CASCADE,
  patch            TEXT NOT NULL DEFAULT 'unknown',
  games_played     INTEGER NOT NULL DEFAULT 0,
  wins             INTEGER NOT NULL DEFAULT 0,
  win_rate         DOUBLE PRECISION,          -- wins/games_played
  source           TEXT NOT NULL DEFAULT 'opendota',
  updated_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (hero_id, opponent_hero_id, patch),
  CHECK (hero_id <> opponent_hero_id),
  CHECK (games_played >= 0),
  CHECK (wins >= 0)
);

CREATE TABLE IF NOT EXISTS sync_meta (
  key        TEXT PRIMARY KEY,
  value      TEXT NOT NULL,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS draft_sessions (
  id           SERIAL PRIMARY KEY,
  radiant_picks INTEGER[] NOT NULL DEFAULT '{}',
  dire_picks    INTEGER[] NOT NULL DEFAULT '{}',
  radiant_bans  INTEGER[] NOT NULL DEFAULT '{}',
  dire_bans     INTEGER[] NOT NULL DEFAULT '{}',
  team_to_pick  TEXT NOT NULL DEFAULT 'radiant',
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS draft_recommendations (
  id          SERIAL PRIMARY KEY,
  session_id  INTEGER REFERENCES draft_sessions(id) ON DELETE SET NULL,
  request     JSONB NOT NULL,
  response    JSONB NOT NULL,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Индексы для scoring-запросов
CREATE INDEX IF NOT EXISTS idx_matchups_hero ON matchups(hero_id);
CREATE INDEX IF NOT EXISTS idx_matchups_opponent ON matchups(opponent_hero_id);
CREATE INDEX IF NOT EXISTS idx_hero_stats_patch ON hero_stats(patch);

-- Начальное состояние sync
INSERT INTO sync_meta(key, value) VALUES ('last_successful_sync', 'never')
ON CONFLICT (key) DO NOTHING;
INSERT INTO sync_meta(key, value) VALUES ('schema_version', '1.0')
ON CONFLICT (key) DO NOTHING;
