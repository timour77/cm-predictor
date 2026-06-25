from fastapi import APIRouter, Query, HTTPException
from typing import List
from app.models import MatchResponse
from app.services.football_api import get_team_matches

router = APIRouter()


@router.get("/{team_id}/matches", response_model=List[MatchResponse])
def list_team_matches(
    team_id: int,
    competition_id: int = Query(...),
):
    try:
        matches = get_team_matches(team_id, competition_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    return [
        MatchResponse(
            external_id=m["external_id"],
            competition_id=m["competition_id"],
            home_team=m["home_team"],
            away_team=m["away_team"],
            home_team_crest=m.get("home_team_crest"),
            away_team_crest=m.get("away_team_crest"),
            match_date=m["match_date"],
            venue=None,
            status=m["status"],
            home_goals=m.get("home_goals"),
            away_goals=m.get("away_goals"),
            matchday=m.get("matchday"),
        )
        for m in matches
    ]
