from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from app.models import UserListEntry, UserPredictionHistory, UserStats
from app.database import fetchone, fetchall
from app.routers.auth import get_current_user

router = APIRouter()


@router.get("", response_model=List[UserListEntry])
def list_users(current_user: dict = Depends(get_current_user)):
    rows = fetchall(
        """
        SELECT u.id, u.username,
               COUNT(p.id) as total_predictions,
               COALESCE(SUM(p.points), 0) as total_points,
               COALESCE(SUM(CASE WHEN p.points > 0 THEN 1 ELSE 0 END), 0) as correct_predictions
        FROM users u
        LEFT JOIN predictions p ON p.user_id = u.id
        GROUP BY u.id, u.username
        ORDER BY total_points DESC, u.username
        """,
    )
    return [
        UserListEntry(
            id=r["id"],
            username=r["username"],
            total_predictions=r["total_predictions"],
            total_points=r["total_points"],
            correct_predictions=r["correct_predictions"],
        )
        for r in rows
    ]


@router.get("/{user_id}/stats", response_model=UserStats)
def get_user_stats(user_id: int, current_user: dict = Depends(get_current_user)):
    user = fetchone("SELECT id FROM users WHERE id = %s", (user_id,))
    if not user:
        raise HTTPException(404, "User not found")

    row = fetchone(
        """
        SELECT u.created_at::text as created_at,
               COUNT(p.id) as total_predictions,
               COALESCE(SUM(p.points), 0) as total_points,
               COALESCE(SUM(CASE WHEN p.points > 0 THEN 1 ELSE 0 END), 0) as correct_predictions
        FROM users u
        LEFT JOIN predictions p ON p.user_id = u.id
        WHERE u.id = %s
        GROUP BY u.id, u.created_at
        """,
        (user_id,),
    )

    rank_row = fetchone(
        """
        WITH ranked AS (
            SELECT user_id, RANK() OVER (ORDER BY SUM(points) DESC) as rnk
            FROM predictions
            GROUP BY user_id
            HAVING SUM(points) > 0
        )
        SELECT rnk FROM ranked WHERE user_id = %s
        """,
        (user_id,),
    )

    return UserStats(
        created_at=row["created_at"] if row else None,
        total_predictions=row["total_predictions"] if row else 0,
        total_points=row["total_points"] if row else 0,
        correct_predictions=row["correct_predictions"] if row else 0,
        rank=rank_row["rnk"] if rank_row else None,
    )


@router.get("/{user_id}/predictions", response_model=List[UserPredictionHistory])
def get_user_predictions(user_id: int, current_user: dict = Depends(get_current_user)):
    user = fetchone("SELECT id FROM users WHERE id = %s", (user_id,))
    if not user:
        raise HTTPException(404, "User not found")

    rows = fetchall(
        """
        SELECT p.id, p.match_id, p.competition_id, p.outcome, p.predicted_score, p.points,
               mr.home_team, mr.away_team, mr.home_goals, mr.away_goals,
               mr.match_date, mr.status as match_status,
               c.name as competition_name
        FROM predictions p
        LEFT JOIN match_results mr ON mr.external_match_id = p.match_id
        LEFT JOIN competitions c ON c.id = p.competition_id
        WHERE p.user_id = %s
        ORDER BY mr.match_date DESC NULLS LAST, p.created_at DESC
        """,
        (user_id,),
    )
    return [
        UserPredictionHistory(
            id=r["id"],
            match_id=r["match_id"],
            competition_id=r["competition_id"],
            competition_name=r.get("competition_name"),
            home_team=r.get("home_team"),
            away_team=r.get("away_team"),
            home_goals=r.get("home_goals"),
            away_goals=r.get("away_goals"),
            match_date=r.get("match_date"),
            match_status=r.get("match_status"),
            outcome=r.get("outcome"),
            predicted_score=r.get("predicted_score"),
            points=r.get("points") or 0,
        )
        for r in rows
    ]
