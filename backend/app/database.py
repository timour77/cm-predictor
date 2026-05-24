import sqlite3
from contextlib import contextmanager
from app.utils.config import DATABASE_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    telegram_id INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    competition_id INTEGER NOT NULL,
    outcome TEXT,
    predicted_score TEXT,
    points INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id),
    UNIQUE(user_id, match_id)
);

CREATE TABLE IF NOT EXISTS match_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_match_id INTEGER NOT NULL UNIQUE,
    competition_id INTEGER NOT NULL,
    home_team TEXT NOT NULL,
    away_team TEXT NOT NULL,
    home_goals INTEGER,
    away_goals INTEGER,
    match_date TEXT,
    status TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS competitions (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT,
    type TEXT,
    emblem TEXT,
    area TEXT,
    is_active INTEGER DEFAULT 1
);

CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id);
CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id);
CREATE INDEX IF NOT EXISTS idx_predictions_competition ON predictions(competition_id);
CREATE INDEX IF NOT EXISTS idx_match_results_competition ON match_results(competition_id);
"""

DEFAULT_COMPETITIONS = [
    (2000, "FIFA World Cup", "WC", "CUP", None, "World", 1),
    (2001, "UEFA Champions League", "CL", "CUP", None, "Europe", 1),
    (2002, "Bundesliga", "BL1", "LEAGUE", None, "Germany", 1),
    (2013, "Brasileirao Série A", "BSA", "LEAGUE", None, "Brazil", 1),
    (2014, "Primera Division", "PD", "LEAGUE", None, "Spain", 1),
    (2015, "Ligue 1", "FL1", "LEAGUE", None, "France", 1),
    (2016, "Championship", "ELC", "LEAGUE", None, "England", 1),
    (2017, "Primeira Liga", "PPL", "LEAGUE", None, "Portugal", 1),
    (2018, "European Championship", "EC", "CUP", None, "Europe", 1),
    (2019, "Serie A", "SA", "LEAGUE", None, "Italy", 1),
    (2021, "Premier League", "PL", "LEAGUE", None, "England", 1),
    (2152, "Copa Libertadores", "CLI", "CUP", None, "South America", 1),
]


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)
        conn.executemany(
            "INSERT OR IGNORE INTO competitions (id, name, code, type, emblem, area, is_active) VALUES (?,?,?,?,?,?,?)",
            DEFAULT_COMPETITIONS,
        )


@contextmanager
def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetchone(query: str, params: tuple = ()) -> sqlite3.Row:
    with get_conn() as conn:
        return conn.execute(query, params).fetchone()


def fetchall(query: str, params: tuple = ()) -> list:
    with get_conn() as conn:
        return conn.execute(query, params).fetchall()


def execute(query: str, params: tuple = ()) -> int:
    with get_conn() as conn:
        cur = conn.execute(query, params)
        return cur.lastrowid
