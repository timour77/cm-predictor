from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, matches, predictions, leaderboard, competitions, users

app = FastAPI(title="CM Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(competitions.router, prefix="/api/competitions", tags=["competitions"])
app.include_router(users.router, prefix="/api/users", tags=["users"])


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.get("/api/admin/stuck-matches")
def admin_stuck_matches():
    """Return matches in DB that are not FINISHED/AWARDED — useful to find 'stuck' live matches."""
    from app.database import fetchall
    rows = fetchall(
        """SELECT external_match_id, home_team, away_team, home_goals, away_goals,
                  status, match_date, updated_at
           FROM match_results
           WHERE status NOT IN ('FINISHED', 'AWARDED', 'SCHEDULED', 'TIMED', 'POSTPONED', 'CANCELLED')
           ORDER BY match_date DESC"""
    )
    return rows


@app.post("/api/admin/fix-match")
def admin_fix_match(external_match_id: int, home_goals: int, away_goals: int, status: str = "FINISHED"):
    """Manually set match result and recalculate points for all predictions on this match."""
    import traceback
    from app.database import get_conn, fetchall
    from app.services.scoring import calculate_points
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE match_results
                   SET status=%s, home_goals=%s, away_goals=%s, updated_at=CURRENT_TIMESTAMP
                   WHERE external_match_id=%s""",
                (status, home_goals, away_goals, external_match_id),
            )
            updated_rows = cur.rowcount

        preds = fetchall(
            "SELECT id, outcome, predicted_score FROM predictions WHERE match_id=%s",
            (external_match_id,),
        )
        pts_updated = 0
        with get_conn() as conn:
            cur = conn.cursor()
            for pred in preds:
                pts = calculate_points(
                    pred["outcome"], pred["predicted_score"], home_goals, away_goals
                )
                cur.execute("UPDATE predictions SET points=%s WHERE id=%s", (pts, pred["id"]))
                pts_updated += 1

        return {
            "status": "ok",
            "match_rows_updated": updated_rows,
            "predictions_updated": pts_updated,
        }
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.post("/api/admin/recalculate-scores")
def admin_recalculate_scores():
    import traceback
    from app.database import get_conn
    from app.services.scoring import calculate_points
    updated = 0
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """SELECT p.id, p.outcome, p.predicted_score,
                          mr.home_goals, mr.away_goals
                   FROM predictions p
                   JOIN match_results mr ON mr.external_match_id = p.match_id
                   WHERE mr.status IN ('FINISHED', 'AWARDED')
                     AND mr.home_goals IS NOT NULL
                     AND mr.away_goals IS NOT NULL"""
            )
            cols = [d[0] for d in cur.description]
            rows = [dict(zip(cols, r)) for r in cur.fetchall()]
            for row in rows:
                pts = calculate_points(
                    row["outcome"],
                    row["predicted_score"],
                    row["home_goals"],
                    row["away_goals"],
                )
                cur.execute("UPDATE predictions SET points=%s WHERE id=%s", (pts, row["id"]))
                updated += 1
        return {"status": "ok", "updated": updated}
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.get("/api/admin/bot-prediction-logs")
def admin_bot_prediction_logs(competition_id: int = None, limit: int = 50):
    from app.database import fetchall
    if competition_id:
        rows = fetchall(
            """SELECT * FROM bot_prediction_logs WHERE competition_id=%s
               ORDER BY created_at DESC LIMIT %s""",
            (competition_id, limit),
        )
    else:
        rows = fetchall(
            "SELECT * FROM bot_prediction_logs ORDER BY created_at DESC LIMIT %s",
            (limit,),
        )
    return rows


@app.post("/api/admin/generate-bot-predictions")
def admin_generate_bot_predictions(competition_id: int):
    import traceback
    from app.database import fetchone as db_fetchone
    from app.services.football_api import get_matches
    from app.services.bot_predictor import run_bot_predictions
    try:
        comp = db_fetchone("SELECT name FROM competitions WHERE id=%s", (competition_id,))
        competition_name = comp["name"] if comp else f"Competition {competition_id}"
        matches = get_matches(competition_id)
        result = run_bot_predictions(competition_id, competition_name, matches)
        return {"status": "ok", "competition": competition_name, **result}
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.post("/api/admin/init-db")
def admin_init_db():
    import traceback
    from app.database import get_conn
    results = []
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            results.append("connected")
            cur.execute("SELECT 1")
            results.append("ping ok")
            cur.execute("ALTER TABLE users ALTER COLUMN password DROP NOT NULL")
            cur.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id) WHERE telegram_id IS NOT NULL")
            cur.execute("ALTER TABLE predictions ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP")
            cur.execute("ALTER TABLE predictions ADD COLUMN IF NOT EXISTS edit_count INTEGER DEFAULT 0")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS photo_url TEXT")
            cur.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_bot BOOLEAN DEFAULT FALSE")
            cur.execute("""CREATE TABLE IF NOT EXISTS bot_prediction_logs (
                id SERIAL PRIMARY KEY,
                match_id INTEGER NOT NULL,
                competition_id INTEGER NOT NULL,
                home_team TEXT NOT NULL,
                away_team TEXT NOT NULL,
                match_date TEXT,
                standings TEXT,
                odds TEXT,
                home_form TEXT,
                away_form TEXT,
                outcome TEXT,
                predicted_score TEXT,
                reasoning TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )""")
            results.append("migrations ok")
            cur.execute("""CREATE TABLE IF NOT EXISTS competitions (
                id INTEGER PRIMARY KEY, name TEXT NOT NULL, code TEXT,
                type TEXT, emblem TEXT, area TEXT, is_active INTEGER DEFAULT 1)""")
            results.append("table ok")
            cur.execute("SELECT count(*) FROM competitions")
            row = cur.fetchone()
            count_before = row[0] if row else 0
            results.append(f"count before: {count_before}")
            comps_data = [
                (2001, "UEFA Champions League", "CL", "CUP", "Europe"),
                (2014, "Primera Division", "PD", "LEAGUE", "Spain"),
                (2021, "Premier League", "PL", "LEAGUE", "England"),
                (2019, "Serie A", "SA", "LEAGUE", "Italy"),
                (2002, "Bundesliga", "BL1", "LEAGUE", "Germany"),
                (2015, "Ligue 1", "FL1", "LEAGUE", "France"),
            ]
            for c in comps_data:
                cur.execute(
                    "INSERT INTO competitions (id, name, code, type, area) VALUES (%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING",
                    c,
                )
            results.append("insert ok")
            cur.execute("SELECT id, name FROM competitions ORDER BY name")
            rows = cur.fetchall()
            cols = [d[0] for d in cur.description]
            comps = [dict(zip(cols, r)) for r in rows]
            results.append(f"found {len(comps)} competitions")
        return {"status": "ok", "steps": results, "competitions": comps}
    except Exception as e:
        return {"status": "error", "steps": results, "detail": str(e), "traceback": traceback.format_exc()}
