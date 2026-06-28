from fastapi import APIRouter, Query, Depends, HTTPException
from fastapi.responses import JSONResponse
from typing import List, Optional
from datetime import date

from app.models import MatchResponse, PredictionResponse
from app.services.football_api import get_matches, get_matches_today, get_cache_fetched_at, BASE_URL
from app.services.scoring import calculate_points
from app.database import fetchone, fetchall, execute, executemany
from app.routers.auth import get_optional_user

router = APIRouter()


def _upsert_and_score(matches: list, current_user: Optional[dict]) -> List[MatchResponse]:
    if not matches:
        return []

    # Single multi-row upsert (one round-trip) instead of one statement per match
    upsert_rows = [
        (m["external_id"], m["competition_id"], m["home_team"], m["away_team"],
         m.get("home_goals"), m.get("away_goals"), m["match_date"], m["status"])
        for m in matches if m.get("competition_id")
    ]
    if upsert_rows:
        values_ph = ",".join(["(%s,%s,%s,%s,%s,%s,%s,%s)"] * len(upsert_rows))
        execute(
            f"""INSERT INTO match_results
                   (external_match_id, competition_id, home_team, away_team,
                    home_goals, away_goals, match_date, status)
               VALUES {values_ph}
               ON CONFLICT (external_match_id) DO UPDATE SET
                   home_goals = EXCLUDED.home_goals,
                   away_goals = EXCLUDED.away_goals,
                   status = EXCLUDED.status,
                   updated_at = CURRENT_TIMESTAMP""",
            tuple(v for row in upsert_rows for v in row),
        )

    # Batch-score finished matches: 1 SELECT + 1 executemany instead of N+N
    finished_ids = [
        m["external_id"] for m in matches
        if m["status"] in ("FINISHED", "AWARDED")
        and m.get("home_goals") is not None
        and m.get("away_goals") is not None
    ]
    if finished_ids:
        score_map = {
            m["external_id"]: (m["home_goals"], m["away_goals"])
            for m in matches if m["external_id"] in set(finished_ids)
        }
        ph = ",".join(["%s"] * len(finished_ids))
        preds_to_score = fetchall(
            f"SELECT id, match_id, outcome, predicted_score FROM predictions WHERE match_id IN ({ph})",
            tuple(finished_ids),
        )
        if preds_to_score:
            executemany(
                "UPDATE predictions SET points=%s WHERE id=%s",
                [
                    (calculate_points(p["outcome"], p["predicted_score"], *score_map[p["match_id"]]), p["id"])
                    for p in preds_to_score
                ],
            )

    # Batch-fetch current user's predictions: 1 SELECT for all matches
    pred_by_match: dict = {}
    if current_user:
        match_ids = [m["external_id"] for m in matches if m.get("competition_id")]
        if match_ids:
            ph = ",".join(["%s"] * len(match_ids))
            rows = fetchall(
                f"SELECT * FROM predictions WHERE user_id=%s AND match_id IN ({ph})",
                (current_user["user_id"], *match_ids),
            )
            pred_by_match = {r["match_id"]: r for r in rows}

    result = []
    for m in matches:
        pred = None
        if current_user and m.get("competition_id"):
            row = pred_by_match.get(m["external_id"])
            if row:
                pred = PredictionResponse(
                    id=row["id"],
                    match_id=row["match_id"],
                    competition_id=row["competition_id"],
                    outcome=row["outcome"],
                    predicted_score=row["predicted_score"],
                    points=row["points"],
                )
        result.append(
            MatchResponse(
                external_id=m["external_id"],
                competition_id=m["competition_id"] or 0,
                competition_name=m.get("competition_name"),
                home_team=m["home_team"],
                away_team=m["away_team"],
                home_team_id=m.get("home_team_id"),
                away_team_id=m.get("away_team_id"),
                home_team_crest=m.get("home_team_crest"),
                away_team_crest=m.get("away_team_crest"),
                match_date=m["match_date"],
                venue=m.get("venue"),
                status=m["status"],
                home_goals=m.get("home_goals"),
                away_goals=m.get("away_goals"),
                matchday=m.get("matchday"),
                stage=m.get("stage"),
                user_prediction=pred,
            )
        )
    return result


@router.get("/today", response_model=List[MatchResponse])
def list_today_matches(
    date: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    from datetime import date as date_class
    d = date or str(date_class.today())
    try:
        matches = get_matches_today(d)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return _upsert_and_score(matches, current_user)


@router.get("")
def list_matches(
    competition_id: int = Query(...),
    date: Optional[str] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: Optional[dict] = Depends(get_optional_user),
):
    d_from = date or date_from
    d_to = date or date_to

    try:
        matches = get_matches(
            competition_id=competition_id,
            date_from=d_from,
            date_to=d_to,
            status=status,
        )
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))

    result = _upsert_and_score(matches, current_user)
    fetched_at = get_cache_fetched_at(f"{BASE_URL}/competitions/{competition_id}/matches")
    headers = {"X-Cache-Fetched-At": str(int(fetched_at))} if fetched_at else {}
    return JSONResponse(content=[r.model_dump() for r in result], headers=headers)
