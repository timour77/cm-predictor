import threading
import pg8000.dbapi
import ssl
from urllib.parse import urlparse
from contextlib import contextmanager
from typing import Optional
from app.utils.config import DATABASE_URL

SCHEMA_STATEMENTS = [
    """CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username TEXT UNIQUE NOT NULL,
        password TEXT,
        telegram_id BIGINT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )""",
    "ALTER TABLE users ALTER COLUMN password DROP NOT NULL",
    "CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id) WHERE telegram_id IS NOT NULL",
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
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url TEXT",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT FALSE",
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP",
    "ALTER TABLE predictions ADD COLUMN IF NOT EXISTS edit_count INTEGER DEFAULT 0",
    "ALTER TABLE match_results ADD COLUMN IF NOT EXISTS penalty_winner TEXT",
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


# A fresh SSL handshake to the (remote) Postgres dominates request latency in
# serverless: a single endpoint may run 4-5 queries, each previously opening and
# closing its own connection. We instead cache one connection per worker thread
# and reuse it across queries/requests, reconnecting only when it has gone stale.
_local = threading.local()

# Errors that mean the cached connection is dead and should be dropped + retried.
_CONN_ERRORS = (
    pg8000.dbapi.InterfaceError,
    pg8000.dbapi.OperationalError,
    ConnectionError,
    OSError,
    ssl.SSLError,
)


def _connect():
    url = urlparse(DATABASE_URL.replace("postgres://", "postgresql://", 1))
    ssl_ctx = ssl.create_default_context()
    return pg8000.dbapi.connect(
        host=url.hostname,
        user=url.username,
        password=url.password,
        database=url.path.lstrip("/"),
        port=url.port or 5432,
        ssl_context=ssl_ctx,
    )


def _shared_conn():
    conn = getattr(_local, "conn", None)
    if conn is None:
        conn = _connect()
        _local.conn = conn
    return conn


def _drop_conn():
    conn = getattr(_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
    _local.conn = None


@contextmanager
def get_conn():
    conn = _shared_conn()
    try:
        yield conn
        conn.commit()
    except _CONN_ERRORS:
        _drop_conn()
        raise
    except Exception:
        try:
            conn.rollback()
        except Exception:
            _drop_conn()
        raise


def _run(op):
    """Run a unit of DB work on the shared connection, reconnecting once if the
    cached connection was dropped by the server (idle timeout, frozen instance)."""
    for attempt in range(2):
        conn = _shared_conn()
        try:
            result = op(conn)
            conn.commit()
            return result
        except _CONN_ERRORS:
            _drop_conn()
            if attempt == 1:
                raise
        except Exception:
            try:
                conn.rollback()
            except Exception:
                _drop_conn()
            raise


def _to_dict(cursor, row):
    if row is None or cursor.description is None:
        return None
    cols = [d[0] for d in cursor.description]
    return dict(zip(cols, row))


def init_db():
    with get_conn() as conn:
        cur = conn.cursor()
        for stmt in SCHEMA_STATEMENTS:
            cur.execute(stmt)
        for comp in DEFAULT_COMPETITIONS:
            cur.execute(
                """INSERT INTO competitions (id, name, code, type, emblem, area, is_active)
                   VALUES (%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
                comp,
            )


def fetchone(query: str, params: tuple = ()):
    def op(conn):
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        return _to_dict(cur, cur.fetchone())
    return _run(op)


def fetchall(query: str, params: tuple = ()) -> list:
    def op(conn):
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        if cur.description is None:
            return []
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, row)) for row in cur.fetchall()]
    return _run(op)


def executemany(query: str, params_list: list):
    def op(conn):
        cur = conn.cursor()
        for params in params_list:
            cur.execute(query, params)
    return _run(op)


def execute(query: str, params: tuple = ()) -> Optional[int]:
    def op(conn):
        cur = conn.cursor()
        if params:
            cur.execute(query, params)
        else:
            cur.execute(query)
        if cur.description:
            row = cur.fetchone()
            return row[0] if row else None
        return None
    return _run(op)
