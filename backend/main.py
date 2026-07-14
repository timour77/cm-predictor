from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import auth, matches, predictions, leaderboard, competitions, users, teams

app = FastAPI(title="CM Predictor API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Cache-Fetched-At"],
)

app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(competitions.router, prefix="/api/competitions", tags=["competitions"])
app.include_router(users.router, prefix="/api/users", tags=["users"])
app.include_router(teams.router, prefix="/api/teams", tags=["teams"])


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
def admin_fix_match(
    external_match_id: int,
    home_goals: int,
    away_goals: int,
    status: str = "FINISHED",
    penalty_winner: str = None,
):
    """Manually set match result and recalculate points for all predictions on this match."""
    import traceback
    from app.database import get_conn, fetchall
    from app.services.scoring import calculate_points
    try:
        with get_conn() as conn:
            cur = conn.cursor()
            cur.execute(
                """UPDATE match_results
                   SET status=%s, home_goals=%s, away_goals=%s,
                       penalty_winner=%s, updated_at=CURRENT_TIMESTAMP
                   WHERE external_match_id=%s""",
                (status, home_goals, away_goals, penalty_winner, external_match_id),
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
                    pred["outcome"], pred["predicted_score"], home_goals, away_goals, penalty_winner
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


@app.post("/api/admin/generate-prediction-for-match")
def admin_generate_prediction_for_match(match_id: int, competition_id: int = 2000):
    """Generate Claude prediction for a specific match."""
    import traceback
    from app.database import fetchone, execute
    from app.services.football_api import get_matches, BASE_URL, HEADERS
    from app.services.bot_predictor import (
        generate_prediction, get_or_create_bot_user, fetch_standings,
        fetch_recent_form, fetch_all_odds, find_odds_for_match
    )
    import requests

    try:
        # Get competition name
        comp = fetchone("SELECT name FROM competitions WHERE id=%s", (competition_id,))
        competition_name = comp["name"] if comp else f"Competition {competition_id}"

        # Fetch match from API
        resp = requests.get(f"{BASE_URL}/matches/{match_id}", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        match_data = resp.json()
        m = match_data.get("match") or match_data

        # Get bot user
        bot_user_id = get_or_create_bot_user()

        # Fetch context data
        standings = fetch_standings(competition_id)
        form = fetch_recent_form(competition_id)
        odds_events = fetch_all_odds(competition_id)

        home_team = m.get("homeTeam", {}).get("name") or "TBD"
        away_team = m.get("awayTeam", {}).get("name") or "TBD"
        match_date = m.get("utcDate", "")

        # Generate prediction
        odds_text = find_odds_for_match(odds_events, home_team, away_team)
        pred = generate_prediction(
            home_team=home_team,
            away_team=away_team,
            competition_name=competition_name,
            match_date=match_date,
            standings=standings,
            form=form,
            odds_text=odds_text,
        )

        # Insert prediction
        execute(
            """INSERT INTO predictions
               (user_id, match_id, competition_id, outcome, predicted_score, updated_at, edit_count)
               VALUES (%s,%s,%s,%s,%s,NOW(),0)
               ON CONFLICT (user_id, match_id) DO UPDATE SET
               outcome=EXCLUDED.outcome, predicted_score=EXCLUDED.predicted_score, updated_at=NOW()""",
            (bot_user_id, match_id, competition_id, pred["outcome"], pred["predicted_score"]),
        )

        return {
            "status": "ok",
            "match_id": match_id,
            "match": f"{home_team} vs {away_team}",
            "outcome": pred["outcome"],
            "predicted_score": pred["predicted_score"],
            "reasoning": pred.get("reasoning", ""),
        }
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.post("/api/admin/sync-live-match")
def admin_sync_live_match(match_id: int):
    """Fetch latest match data from API and update score if changed."""
    import traceback
    from app.database import fetchone as db_fetchone, fetchall, get_conn
    from app.services.football_api import BASE_URL, HEADERS, _regulation_score
    import requests

    try:
        resp = requests.get(f"{BASE_URL}/matches/{match_id}", headers=HEADERS, timeout=10)
        resp.raise_for_status()
        match_data = resp.json()
        # API returns match data either under "match" key or directly
        m = match_data.get("match") or match_data

        score = m.get("score", {})
        full_time = _regulation_score(score)
        home_goals = full_time.get("home")
        away_goals = full_time.get("away")
        status = m.get("status")

        # Check current state in DB
        current = db_fetchone(
            "SELECT home_goals, away_goals, status FROM match_results WHERE external_match_id=%s",
            (match_id,)
        )

        if not current:
            return {"status": "error", "detail": "Match not found in database"}

        # Update if status or score changed
        updated = False
        if current["status"] != status or current["home_goals"] != home_goals or current["away_goals"] != away_goals:
            with get_conn() as conn:
                cur = conn.cursor()
                cur.execute(
                    """UPDATE match_results
                       SET status=%s, home_goals=%s, away_goals=%s, updated_at=CURRENT_TIMESTAMP
                       WHERE external_match_id=%s""",
                    (status, home_goals, away_goals, match_id),
                )
            updated = True

        # Recalculate points if result was updated and match is finished
        pts_updated = 0
        if updated and status in ('FINISHED', 'AWARDED') and home_goals is not None and away_goals is not None:
            from app.services.scoring import calculate_points
            preds = fetchall(
                "SELECT id, outcome, predicted_score FROM predictions WHERE match_id=%s",
                (match_id,),
            )
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
            "match_id": match_id,
            "current_status": status,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "updated": updated,
            "predictions_recalculated": pts_updated
        }
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.post("/api/admin/recalculate-match-predictions")
def admin_recalculate_match_predictions(match_id: int):
    """Recalculate points for all predictions on a specific match."""
    import traceback
    from app.database import fetchall, get_conn
    from app.services.scoring import calculate_points

    try:
        # Get match result
        match_result = fetchall(
            "SELECT external_match_id, home_goals, away_goals, penalty_winner FROM match_results WHERE external_match_id=%s",
            (match_id,)
        )
        if not match_result:
            return {"status": "error", "detail": "Match not found"}

        mr = match_result[0]
        home_goals = mr["home_goals"]
        away_goals = mr["away_goals"]
        penalty_winner = mr.get("penalty_winner")

        if home_goals is None or away_goals is None:
            return {"status": "error", "detail": "Match has no final score"}

        # Get all predictions for this match
        preds = fetchall(
            "SELECT id, outcome, predicted_score FROM predictions WHERE match_id=%s",
            (match_id,),
        )

        # Recalculate points for each prediction
        updated = 0
        with get_conn() as conn:
            cur = conn.cursor()
            for pred in preds:
                pts = calculate_points(
                    pred["outcome"], pred["predicted_score"], home_goals, away_goals, penalty_winner
                )
                cur.execute("UPDATE predictions SET points=%s WHERE id=%s", (pts, pred["id"]))
                updated += 1

        return {
            "status": "ok",
            "match_id": match_id,
            "home_goals": home_goals,
            "away_goals": away_goals,
            "predictions_updated": updated
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
                          mr.home_goals, mr.away_goals, mr.penalty_winner
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
                    row.get("penalty_winner"),
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


@app.post("/api/admin/reset-tbd-bot-predictions")
def admin_reset_tbd_bot_predictions(competition_id: int):
    """Delete bot predictions made while opponents were still placeholders (TBD),
    so they can be regenerated now that real teams are known."""
    import traceback
    from app.database import fetchall, execute
    try:
        bot = fetchall("SELECT id FROM users WHERE username='Claude' AND is_bot=TRUE")
        if not bot:
            return {"status": "ok", "reset": 0, "match_ids": []}
        bot_user_id = bot[0]["id"]

        logs = fetchall(
            """SELECT DISTINCT match_id FROM bot_prediction_logs
               WHERE competition_id=%s
                 AND (home_team ILIKE %s OR away_team ILIKE %s
                      OR home_team ILIKE %s OR away_team ILIKE %s)""",
            (competition_id, "%TBD%", "%TBD%", "%Winner%", "%Winner%"),
        )
        match_ids = [row["match_id"] for row in logs]
        if not match_ids:
            return {"status": "ok", "reset": 0, "match_ids": []}

        for match_id in match_ids:
            execute(
                "DELETE FROM predictions WHERE user_id=%s AND match_id=%s",
                (bot_user_id, match_id),
            )
            execute(
                "DELETE FROM bot_prediction_logs WHERE competition_id=%s AND match_id=%s",
                (competition_id, match_id),
            )

        return {"status": "ok", "reset": len(match_ids), "match_ids": match_ids}
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.get("/api/admin/today-matches")
def admin_today_matches(competition_id: int = 2000):
    """Show all matches for today with their status and scores."""
    from datetime import datetime, timezone
    from app.services.football_api import get_matches

    matches = get_matches(competition_id)
    today = datetime.now(timezone.utc).date()

    today_matches = []
    for m in matches:
        try:
            match_date = datetime.fromisoformat(m["match_date"].replace("Z", "+00:00")).date()
            if match_date == today:
                today_matches.append({
                    "id": m["external_id"],
                    "home_team": m["home_team"],
                    "away_team": m["away_team"],
                    "status": m["status"],
                    "time": m["match_date"],
                    "score": f"{m['home_goals']}-{m['away_goals']}" if m['home_goals'] is not None else "not started",
                })
        except:
            pass

    return {
        "date": str(today),
        "competition_id": competition_id,
        "matches": today_matches,
        "total": len(today_matches)
    }


@app.get("/api/admin/debug-live-match")
def admin_debug_live_match(match_id: int):
    """Debug: show raw match data from API."""
    import traceback
    from app.services.football_api import BASE_URL, HEADERS
    import requests
    import json

    try:
        resp = requests.get(f"{BASE_URL}/matches/{match_id}", headers=HEADERS, timeout=10)
        data = resp.json()

        if resp.status_code != 200:
            return {"status": "error", "http_status": resp.status_code, "api_response": data}

        # Return full response for debugging
        return {"full_response": data}
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.get("/api/admin/debug-match-statuses")
def admin_debug_match_statuses(competition_id: int):
    from app.services.football_api import get_matches
    matches = get_matches(competition_id)
    statuses = {}
    for m in matches:
        status = m["status"]
        if status not in statuses:
            statuses[status] = []
        statuses[status].append(f"{m['home_team']} vs {m['away_team']} ({m['match_date'][:10]})")
    return {"statuses": statuses, "total": len(matches)}


@app.post("/api/admin/generate-bot-predictions")
def admin_generate_bot_predictions(competition_id: int, force: bool = False):
    import traceback
    from app.database import fetchone as db_fetchone
    from app.services.football_api import get_matches
    from app.services.bot_predictor import run_bot_predictions
    try:
        comp = db_fetchone("SELECT name FROM competitions WHERE id=%s", (competition_id,))
        competition_name = comp["name"] if comp else f"Competition {competition_id}"
        matches = get_matches(competition_id)
        result = run_bot_predictions(competition_id, competition_name, matches, force=force)
        return {"status": "ok", "competition": competition_name, **result}
    except Exception as e:
        return {"status": "error", "detail": str(e), "traceback": traceback.format_exc()}


@app.post("/api/admin/init-db")
def admin_init_db():
    import traceback
    from app.database import get_conn, init_db
    results = []
    try:
        init_db()
        results.append("schema migrations ok (init_db)")
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
            cur.execute("ALTER TABLE match_results ADD COLUMN IF NOT EXISTS penalty_winner TEXT")
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
