-- ============================================================
-- schema.sql — Recipe Explorer Database Schema
-- Engine: SQLite (dev)
-- ============================================================

DROP TABLE IF EXISTS recipes;

CREATE TABLE recipes (
    id               INTEGER      PRIMARY KEY AUTOINCREMENT,

    -- Core identity
    title            VARCHAR(500),
    cuisine          VARCHAR(200),

    -- Numeric fields — NaN from source JSON stored as NULL
    rating           FLOAT,        -- e.g. 4.8    (NULL = not rated)
    prep_time        INTEGER,      -- minutes     (NULL = unavailable)
    cook_time        INTEGER,      -- minutes     (NULL = unavailable)
    total_time       INTEGER,      -- minutes     (NULL = unavailable)

    -- Text
    description      TEXT,
    serves           VARCHAR(100), -- e.g. "8 servings"

    -- Extracted at seed time for efficient SQL-level range filtering.
    -- Parsing "389 kcal" → 389 avoids a Python-side full-table scan.
    calories         INTEGER,      -- kcal (NULL when missing)

    -- Full nutrients object for display (all fields kept)
    nutrients        TEXT          -- stored as JSON string
);

-- ── Indexes ──────────────────────────────────────────────────────────────────
-- Chosen to match the filter patterns used in /api/recipes/search

CREATE INDEX IF NOT EXISTS idx_recipes_title      ON recipes (title);
CREATE INDEX IF NOT EXISTS idx_recipes_cuisine    ON recipes (cuisine);
CREATE INDEX IF NOT EXISTS idx_recipes_rating     ON recipes (rating);
CREATE INDEX IF NOT EXISTS idx_recipes_total_time ON recipes (total_time);
CREATE INDEX IF NOT EXISTS idx_recipes_calories   ON recipes (calories);