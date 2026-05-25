from fastapi import APIRouter
from typing import List
from app.models import CompetitionResponse
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
