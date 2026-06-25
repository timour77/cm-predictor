from fastapi import APIRouter, HTTPException
from typing import List
from app.models import CompetitionResponse, GroupStanding
from app.database import fetchall

router = APIRouter()


@router.get("", response_model=List[CompetitionResponse])
def get_competitions():
    rows = fetchall(
        "SELECT id, name, code, type, emblem, area, is_active FROM competitions ORDER BY name"
    )
    return [
        CompetitionResponse(
            id=r["id"],
            name=r["name"],
            code=r["code"] or "",
            type=r["type"] or "",
            emblem=r["emblem"],
            area=r["area"] or "",
            is_active=bool(r["is_active"]),
        )
        for r in rows
    ]


@router.get("/{competition_id}/standings", response_model=List[GroupStanding])
def get_competition_standings(competition_id: int):
    from app.services.football_api import get_standings
    try:
        return get_standings(competition_id)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
