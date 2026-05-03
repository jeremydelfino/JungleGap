-- ═══════════════════════════════════════════════════════════
-- COACHDIFF + AMÉLIORATIONS STATS — MIGRATION
-- ═══════════════════════════════════════════════════════════

-- ─── 1. CHAMPION_MATCHUPS (nouvelle table) ───
CREATE TABLE IF NOT EXISTS champion_matchups (
    id              SERIAL PRIMARY KEY,
    champion_a      VARCHAR(50)  NOT NULL,
    champion_b      VARCHAR(50)  NOT NULL,
    lane            VARCHAR(20)  NOT NULL,
    tier            VARCHAR(20)  NOT NULL DEFAULT 'MASTER',
    region          VARCHAR(10)  NOT NULL DEFAULT 'EUW',
    n_games         INTEGER      NOT NULL DEFAULT 0,
    a_wins          INTEGER      NOT NULL DEFAULT 0,
    winrate_a       FLOAT        NOT NULL DEFAULT 0.50,
    updated_at      TIMESTAMP    NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_champ_matchup UNIQUE (champion_a, champion_b, lane, tier, region),
    CONSTRAINT ck_champ_order   CHECK (champion_a < champion_b)
);

CREATE INDEX IF NOT EXISTS idx_matchup_lookup_a ON champion_matchups (champion_a, lane, tier);
CREATE INDEX IF NOT EXISTS idx_matchup_lookup_b ON champion_matchups (champion_b, lane, tier);


-- ─── 2. CHAMPION_SYNERGIES (ajout colonnes lanes) ───
ALTER TABLE champion_synergies ADD COLUMN IF NOT EXISTS lane_a VARCHAR(20);
ALTER TABLE champion_synergies ADD COLUMN IF NOT EXISTS lane_b VARCHAR(20);

-- L'ancienne UNIQUE constraint ne tient plus compte des lanes : on la drop et on la recrée
ALTER TABLE champion_synergies DROP CONSTRAINT IF EXISTS uq_champ_synergy;
ALTER TABLE champion_synergies
    ADD CONSTRAINT uq_champ_synergy_lanes
    UNIQUE (champion_a, champion_b, lane_a, lane_b, tier, region);

CREATE INDEX IF NOT EXISTS idx_synergy_lookup ON champion_synergies (champion_a, champion_b, lane_a, lane_b);


-- ─── 3. CHAMPION_PRO_STATS (nouvelle table, agrégat global) ───
CREATE TABLE IF NOT EXISTS champion_pro_stats (
    id              SERIAL PRIMARY KEY,
    champion        VARCHAR(50) NOT NULL,
    lane            VARCHAR(20) NOT NULL,
    n_picks         INTEGER     NOT NULL DEFAULT 0,
    n_bans          INTEGER     NOT NULL DEFAULT 0,
    n_games_total   INTEGER     NOT NULL DEFAULT 0,
    pickrate        FLOAT       NOT NULL DEFAULT 0.0,
    banrate         FLOAT       NOT NULL DEFAULT 0.0,
    presence        FLOAT       NOT NULL DEFAULT 0.0,
    winrate         FLOAT       NOT NULL DEFAULT 0.50,
    last_synced_at  TIMESTAMP   NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_pro_stats UNIQUE (champion, lane)
);

CREATE INDEX IF NOT EXISTS idx_pro_stats_lookup ON champion_pro_stats (champion, lane);


-- ─── 4. COACHDIFF_GAMES (nouvelle table, état des parties) ───
CREATE TABLE IF NOT EXISTS coachdiff_games (
    id              SERIAL PRIMARY KEY,
    user_id         INTEGER     NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status          VARCHAR(20) NOT NULL DEFAULT 'in_progress',
    user_side       VARCHAR(10) NOT NULL,
    bot_side        VARCHAR(10) NOT NULL,
    user_score      FLOAT,
    bot_score       FLOAT,
    user_breakdown  JSONB,
    bot_breakdown   JSONB,
    winner          VARCHAR(10),
    coins_delta     INTEGER     NOT NULL DEFAULT 0,
    draft_state     JSONB       NOT NULL,
    created_at      TIMESTAMP   NOT NULL DEFAULT NOW(),
    finished_at     TIMESTAMP,
    CONSTRAINT ck_status      CHECK (status IN ('in_progress','finished','cancelled')),
    CONSTRAINT ck_user_side   CHECK (user_side IN ('BLUE','RED')),
    CONSTRAINT ck_bot_side    CHECK (bot_side IN ('BLUE','RED')),
    CONSTRAINT ck_winner      CHECK (winner IS NULL OR winner IN ('USER','BOT','DRAW'))
);

CREATE INDEX IF NOT EXISTS idx_coachdiff_user        ON coachdiff_games (user_id);
CREATE INDEX IF NOT EXISTS idx_coachdiff_status      ON coachdiff_games (status);
CREATE INDEX IF NOT EXISTS idx_coachdiff_user_active ON coachdiff_games (user_id, status) WHERE status = 'in_progress';

-- ─── Étendre les types de transactions pour CoachDiff ─────────
ALTER TABLE transactions DROP CONSTRAINT IF EXISTS transactions_type_check;
ALTER TABLE transactions ADD CONSTRAINT transactions_type_check
  CHECK (type IN (
    'signup_bonus', 'daily_reward',
    'bet_placed', 'bet_won', 'bet_lost', 'bet_refunded', 'bet_cancelled',
    'crate_purchase',
    'coachdiff_entry', 'coachdiff_win', 'coachdiff_draw'
  ));