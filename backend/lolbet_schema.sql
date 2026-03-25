-- ============================================================
--  LolBet — Schéma PostgreSQL complet
--  Ordre de création respectant les dépendances FK
-- ============================================================


-- ------------------------------------------------------------
-- 1. CARTES (aucune dépendance)
-- ------------------------------------------------------------
CREATE TABLE cards (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    type            VARCHAR(50)     NOT NULL,       -- "champion", "pro_player", "meme", "cosmetic"
    rarity          VARCHAR(20)     NOT NULL        -- "common", "rare", "epic", "legendary"
                    CHECK (rarity IN ('common', 'rare', 'epic', 'legendary')),
    image_url       TEXT            NOT NULL,       -- URL Cloudinary
    -- Boost
    boost_type      VARCHAR(50),                    -- "percent_gain", "flat_gain", NULL si cosmétique
    boost_value     FLOAT           DEFAULT 0,      -- ex: 0.15 = +15%
    trigger_type    VARCHAR(20)                     -- "champion", "player", "mechanic", "any"
                    CHECK (trigger_type IN ('champion', 'player', 'mechanic', 'any', NULL)),
    trigger_value   VARCHAR(100),                   -- "Yasuo", "Faker", "first_blood", etc.
    -- Cosmétiques
    is_banner       BOOLEAN         DEFAULT FALSE,
    is_title        BOOLEAN         DEFAULT FALSE,
    title_text      VARCHAR(100),                   -- ex: "Le Parieur Légendaire"
    created_at      TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 2. CAISSES (aucune dépendance)
-- ------------------------------------------------------------
CREATE TABLE crates (
    id              SERIAL PRIMARY KEY,
    name            VARCHAR(100)    NOT NULL,
    rarity_tier     VARCHAR(20)     NOT NULL
                    CHECK (rarity_tier IN ('common', 'rare', 'epic', 'legendary')),
    price_coins     INT             NOT NULL CHECK (price_coins > 0),
    image_url       TEXT            NOT NULL,
    created_at      TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 3. CONTENU DES CAISSES (dépend de crates + cards)
-- ------------------------------------------------------------
CREATE TABLE crate_contents (
    id              SERIAL PRIMARY KEY,
    crate_id        INT             NOT NULL REFERENCES crates(id) ON DELETE CASCADE,
    card_id         INT             NOT NULL REFERENCES cards(id)  ON DELETE CASCADE,
    weight          INT             NOT NULL CHECK (weight > 0),   -- plus c'est élevé, plus c'est probable
    UNIQUE (crate_id, card_id)
);


-- ------------------------------------------------------------
-- 4. TYPES DE PARIS (aucune dépendance)
-- ------------------------------------------------------------
CREATE TABLE bet_types (
    id              SERIAL PRIMARY KEY,
    slug            VARCHAR(50)     NOT NULL UNIQUE, -- "who_wins", "first_blood", etc.
    label           VARCHAR(100)    NOT NULL,         -- "Qui va gagner ?"
    description     TEXT,                             -- affiché dans le popup
    category        VARCHAR(20)     NOT NULL
                    CHECK (category IN ('classic', 'player', 'wtf')),
    is_active       BOOLEAN         DEFAULT TRUE,     -- désactiver sans supprimer
    created_at      TIMESTAMP       DEFAULT NOW()
);

-- Données initiales — paris classiques au lancement
INSERT INTO bet_types (slug, label, description, category) VALUES
    ('who_wins',          'Qui va gagner ?',             'Parie sur l''équipe bleue ou rouge.',                         'classic'),
    ('first_blood',       'Premier sang',                'Quelle équipe obtient le premier kill ?',                     'classic'),
    ('first_tower',       'Première tour détruite',      'Quelle équipe détruit la première tour ?',                    'classic'),
    ('over_under_kills',  'Total kills (plus/moins)',    'Le total de kills sera-t-il au dessus ou en dessous du seuil ?', 'classic'),
    ('player_kills',      'Kills du joueur recherché',   'Le joueur finira-t-il avec X kills ou plus ?',                'player');


-- ------------------------------------------------------------
-- 5. UTILISATEURS (dépend de cards pour les FK cosmétiques)
-- ------------------------------------------------------------
CREATE TABLE users (
    id                  SERIAL PRIMARY KEY,
    username            VARCHAR(50)     NOT NULL UNIQUE,
    email               VARCHAR(255)    NOT NULL UNIQUE,
    password_hash       TEXT            NOT NULL,
    coins               INT             NOT NULL DEFAULT 500 CHECK (coins >= 0),
    avatar_url          TEXT,                           -- URL Cloudinary uploadée par l'user
    equipped_banner_id  INT             REFERENCES cards(id) ON DELETE SET NULL,
    equipped_title_id   INT             REFERENCES cards(id) ON DELETE SET NULL,
    last_daily          TIMESTAMP,                      -- dernière réclamation du daily reward
    created_at          TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 6. CARTES POSSÉDÉES PAR LES USERS (dépend de users + cards)
-- ------------------------------------------------------------
CREATE TABLE user_cards (
    id              SERIAL PRIMARY KEY,
    user_id         INT             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    card_id         INT             NOT NULL REFERENCES cards(id) ON DELETE CASCADE,
    equipped        BOOLEAN         DEFAULT FALSE,
    obtained_at     TIMESTAMP       DEFAULT NOW(),
    UNIQUE (user_id, card_id)                           -- pas de doublons
);


-- ------------------------------------------------------------
-- 7. JOUEURS RECHERCHÉS — cache local op.gg-like
-- ------------------------------------------------------------
CREATE TABLE searched_players (
    id                  SERIAL PRIMARY KEY,
    riot_puuid          VARCHAR(100)    NOT NULL UNIQUE, -- identifiant universel Riot
    summoner_name       VARCHAR(50)     NOT NULL,
    tag_line            VARCHAR(10)     NOT NULL,        -- ex: "EUW", "KR1"
    region              VARCHAR(10)     NOT NULL,        -- "EUW", "NA", "KR", etc.
    tier                VARCHAR(20),                     -- "DIAMOND", "MASTER", etc.
    rank                VARCHAR(5),                      -- "I", "II", "III", "IV"
    lp                  INT             DEFAULT 0,
    profile_icon_url    TEXT,
    last_updated        TIMESTAMP       DEFAULT NOW(),   -- pour savoir si le cache est frais
    created_at          TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 8. PARTIES EN COURS (dépend de searched_players)
-- ------------------------------------------------------------
CREATE TABLE live_games (
    id                      SERIAL PRIMARY KEY,
    searched_player_id      INT             NOT NULL REFERENCES searched_players(id) ON DELETE CASCADE,
    riot_game_id            VARCHAR(100)    NOT NULL UNIQUE,
    queue_type              VARCHAR(50),                -- "RANKED_SOLO_5x5", "NORMAL", etc.
    blue_team               JSONB           NOT NULL,   -- [{puuid, summonerName, champion, ...}]
    red_team                JSONB           NOT NULL,
    duration_seconds        INT             DEFAULT 0,
    status                  VARCHAR(20)     NOT NULL DEFAULT 'live'
                            CHECK (status IN ('live', 'ended')),
    fetched_at              TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 9. HISTORIQUE DES PARTIES (dépend de searched_players)
-- ------------------------------------------------------------
CREATE TABLE match_history (
    id                      SERIAL PRIMARY KEY,
    searched_player_id      INT             NOT NULL REFERENCES searched_players(id) ON DELETE CASCADE,
    riot_match_id           VARCHAR(100)    NOT NULL,
    champion_played         VARCHAR(50)     NOT NULL,
    role                    VARCHAR(20),                -- "TOP", "JUNGLE", "MID", "ADC", "SUPPORT"
    win                     BOOLEAN         NOT NULL,
    kills                   INT             DEFAULT 0,
    deaths                  INT             DEFAULT 0,
    assists                 INT             DEFAULT 0,
    cs                      INT             DEFAULT 0,
    duration_seconds        INT             NOT NULL,
    played_at               TIMESTAMP       NOT NULL,
    UNIQUE (searched_player_id, riot_match_id)
);


-- ------------------------------------------------------------
-- 10. PARIS (dépend de users + live_games + cards + bet_types)
-- ------------------------------------------------------------
CREATE TABLE bets (
    id              SERIAL PRIMARY KEY,
    user_id         INT             NOT NULL REFERENCES users(id)       ON DELETE CASCADE,
    live_game_id    INT             NOT NULL REFERENCES live_games(id)  ON DELETE CASCADE,
    card_used_id    INT             REFERENCES cards(id)                ON DELETE SET NULL,
    bet_type_slug   VARCHAR(50)     NOT NULL REFERENCES bet_types(slug) ON DELETE RESTRICT,
    bet_value       VARCHAR(100)    NOT NULL,   -- "blue", "red", "over", "under", "5", etc.
    amount          INT             NOT NULL CHECK (amount > 0),
    boost_applied   FLOAT           DEFAULT 0,  -- % de boost réel appliqué au moment du pari
    status          VARCHAR(20)     NOT NULL DEFAULT 'pending'
                    CHECK (status IN ('pending', 'won', 'lost', 'cancelled')),
    payout          INT             DEFAULT 0,  -- gains reçus si gagné
    created_at      TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 11. TRANSACTIONS (dépend de users)
-- ------------------------------------------------------------
CREATE TABLE transactions (
    id              SERIAL PRIMARY KEY,
    user_id         INT             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(30)     NOT NULL
                    CHECK (type IN ('signup_bonus', 'daily_reward', 'bet_placed', 'bet_won', 'bet_lost', 'crate_purchase')),
    amount          INT             NOT NULL,   -- positif = gain, négatif = dépense
    description     TEXT,
    created_at      TIMESTAMP       DEFAULT NOW()
);


-- ------------------------------------------------------------
-- 12. NOTIFICATIONS (dépend de users + bets)
-- ------------------------------------------------------------
CREATE TABLE notifications (
    id              SERIAL PRIMARY KEY,
    user_id         INT             NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    bet_id          INT             REFERENCES bets(id)           ON DELETE SET NULL,
    type            VARCHAR(30)     NOT NULL
                    CHECK (type IN ('bet_won', 'bet_lost', 'daily_available', 'new_card')),
    message         TEXT            NOT NULL,
    is_read         BOOLEAN         DEFAULT FALSE,
    created_at      TIMESTAMP       DEFAULT NOW()
);


-- ============================================================
--  INDEX — pour les requêtes fréquentes
-- ============================================================
CREATE INDEX idx_users_email             ON users(email);
CREATE INDEX idx_searched_players_puuid  ON searched_players(riot_puuid);
CREATE INDEX idx_searched_players_region ON searched_players(region);
CREATE INDEX idx_live_games_status       ON live_games(status);
CREATE INDEX idx_live_games_riot_id      ON live_games(riot_game_id);
CREATE INDEX idx_bets_user_id            ON bets(user_id);
CREATE INDEX idx_bets_live_game_id       ON bets(live_game_id);
CREATE INDEX idx_bets_status             ON bets(status);
CREATE INDEX idx_notifications_user_id   ON notifications(user_id, is_read);
CREATE INDEX idx_match_history_player    ON match_history(searched_player_id);
CREATE INDEX idx_transactions_user_id    ON transactions(user_id);

