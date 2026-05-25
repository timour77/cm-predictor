from fastapi import APIRouter, Query, Depends, HTTPException
from typing import List, Optional
from datetime import date

from app.models import MatchResponse, PredictionResponse
from app.services.football_api import get_matches
from app.database import fetchone
from app.routers.auth import get_optional_user

router = APIRouter()


@router.get("/", response_model=List[MatchResponse])
def list_matches(
    competition_id: int = Query(...),
    date: Optional[str] = Query(None),      # "2026-06-11"
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

    result = []
    for m in matches:
        pred = None
        if current_user:
            row = fetchone(
                "SELECT * FROM predictions WHERE user_id=%s AND match_id=%s",
                (current_user["user_id"], m["external_id"]),
            )
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
                competition_id=m["competition_id"],
                home_team=m["home_team"],
                away_team=m["away_team"],
                home_team_crest=m.get("home_team_crest"),
                away_team_crest=m.get("away_team_crest"),
                match_date=m["match_date"],
                venue=m.get("venue"),
                status=m["status"],
                home_goals=m.get("home_goals"),
                away_goals=m.get("away_goals"),
                matchday=m.get("matchday"),
                user_prediction=pred,
            )
        )

    return result
