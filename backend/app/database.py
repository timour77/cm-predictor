import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from typing import Optional
from app.utils.config import DATABASE_URL

SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        telegram_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS predictions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id),
        match_id INTEGER NOT NULL,
        competition_id INTEGER NOT NULL,
        outcome TEXT,
        predicted_score TEXT,
        points INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(user_id, match_id)
    )""",
    """CREATE TABLE IF NOT EXISTS match_results (
        id SERIAL PRIMARY KEY,
        external_match_id INTEGER NOT NULL UNIQUE,
        competition_id INTEGER NOT NULL,
        home_team TEXT NOT NULL,
        away_team TEXT NOT NULL,
        home_goals INTEGER,
        away_goals INTEGER,
        match_date TEXT,
        status TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    """CREATE TABLE IF NOT EXISTS competitions (
        id INTEGER PRIMARY KEY,
        name TEXT NOT NULL,
        code TEXT,
        type TEXT,
        emblem TEXT,
        area TEXT,
        is_active INTEGER DEFAULT 1
    )""",
    "CREATE INDEX IF NOT EXISTS idx_predictions_user ON predictions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_predictions_match ON predictions(match_id)",
    "CREATE INDEX IF NOT EXISTS idx_predictions_competition ON predictions(competition_id)",
    "CREATE INDEX IF NOT EXISTS idx_match_results_competition ON match_results(competition_id)",
]

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


@contextmanager
def get_conn():
    url = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    conn = psycopg2.connect(url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        with conn.cursor() as cur:
            for stmt in SCHEMA_STATEMENTS:
                cur.execute(stmt)
            for comp in DEFAULT_COMPETITIONS:
                cur.execute(
                    """INSERT INTO competitions (id, name, code, type, emblem, area, is_active)
                       VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                    comp,
                )


def fetchone(query: str, params: tuple = ()):
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchone()


def fetchall(query: str, params: tuple = ()) -> list:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            return cur.fetchall()


def execute(query: str, params: tuple = ()) -> Optional[int]:
    with get_conn() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if cur.description:
                row = cur.fetchone()
                return row["id"] if row else None
            return None
