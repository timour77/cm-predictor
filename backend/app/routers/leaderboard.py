from fastapi import APIRouter, Query, Depends
from typing import List, Optional

from app.models import LeaderboardEntry
from app.database import fetchall, fetchone
from app.routers.auth import get_current_user, get_optional_user

router = APIRouter()


def _build_leaderboard(competition_id: Optional[int]) -> List[LeaderboardEntry]:
    if competition_id:
        rows = fetchall(
            """
            SELECT u.id as user_id, u.username,
                   COALESCE(SUM(p.points), 0) as total_points,
                   COALESCE(SUM(CASE WHEN p.points > 0 THEN 1 ELSE 0 END), 0) as correct_outcomes,
                   COALESCE(SUM(CASE WHEN p.points >= 4 THEN 1 ELSE 0 END), 0) as correct_scores
            FROM users u
            LEFT JOIN predictions p ON p.user_id = u.id AND p.competition_id = %s
            GROUP BY u.id, u.username
            HAVING COALESCE(SUM(p.points), 0) > 0
            ORDER BY total_points DESC
            LIMIT 100
            """,
            (competition_id,),
        )
    else:
        rows = fetchall(
            """
            SELECT u.id as user_id, u.username,
                   COALESCE(SUM(p.points), 0) as total_points,
                   COALESCE(SUM(CASE WHEN p.points > 0 THEN 1 ELSE 0 END), 0) as correct_outcomes,
                   COALESCE(SUM(CASE WHEN p.points >= 4 THEN 1 ELSE 0 END), 0) as correct_scores
            FROM users u
            LEFT JOIN predictions p ON p.user_id = u.id
            GROUP BY u.id, u.username
            HAVING COALESCE(SUM(p.points), 0) > 0
            ORDER BY total_points DESC
            LIMIT 100
            """,
        )
    return [
        LeaderboardEntry(
            rank=i + 1,
            user_id=r["user_id"],
            username=r["username"],
            total_points=r["total_points"],
            correct_outcomes=r["correct_outcomes"],
            correct_scores=r["correct_scores"],
        )
        for i, r in enumerate(rows)
    ]


@router.get("", response_model=List[LeaderboardEntry])
def get_leaderboard(competition_id: Optional[int] = Query(None)):
    return _build_leaderboard(competition_id)


@router.get("/me", response_model=Optional[LeaderboardEntry])
def get_my_position(
    competition_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    board = _build_leaderboard(competition_id)
    for entry in board:
        if entry.user_id == current_user["user_id"]:
            return entry
    return None
