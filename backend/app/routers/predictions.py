from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional

from app.models import PredictionRequest, PredictionResponse
from app.database import fetchone, fetchall, execute
from app.routers.auth import get_current_user
from app.services.football_api import get_matches
from app.services.scoring import calculate_points

router = APIRouter()


def _recalculate_and_update(prediction_id: int):
    row = fetchone("SELECT * FROM predictions WHERE id=%s", (prediction_id,))
    if not row:
        return
    match_row = fetchone(
        "SELECT home_goals, away_goals, status FROM match_results WHERE external_match_id=%s",
        (row["match_id"],),
    )
    if match_row and match_row["status"] == "FINISHED":
        pts = calculate_points(
            row["outcome"],
            row["predicted_score"],
            match_row["home_goals"],
            match_row["away_goals"],
        )
        execute("UPDATE predictions SET points=%s WHERE id=%s", (pts, prediction_id))


@router.post("", response_model=PredictionResponse)
def save_prediction(body: PredictionRequest, current_user: dict = Depends(get_current_user)):
    existing = fetchone(
        "SELECT id FROM predictions WHERE user_id=%s AND match_id=%s",
        (current_user["user_id"], body.match_id),
    )
    if existing:
        pred_id = existing["id"]
        execute(
            """UPDATE predictions SET outcome=%s, predicted_score=%s, competition_id=%s,
               updated_at=NOW(), edit_count=COALESCE(edit_count,0)+1 WHERE id=%s""",
            (body.outcome, body.predicted_score, body.competition_id, pred_id),
        )
    else:
        pred_id = execute(
            """INSERT INTO predictions (user_id, match_id, competition_id, outcome, predicted_score, updated_at, edit_count)
               VALUES (%s,%s,%s,%s,%s,NOW(),0) RETURNING id""",
            (current_user["user_id"], body.match_id, body.competition_id, body.outcome, body.predicted_score),
        )

    _recalculate_and_update(pred_id)
    row = fetchone("SELECT * FROM predictions WHERE id=%s", (pred_id,))
    return PredictionResponse(
        id=row["id"],
        match_id=row["match_id"],
        competition_id=row["competition_id"],
        outcome=row["outcome"],
        predicted_score=row["predicted_score"],
        points=row["points"],
    )


@router.get("", response_model=List[PredictionResponse])
def get_my_predictions(
    competition_id: Optional[int] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    if competition_id:
        rows = fetchall(
            "SELECT * FROM predictions WHERE user_id=%s AND competition_id=%s",
            (current_user["user_id"], competition_id),
        )
    else:
        rows = fetchall("SELECT * FROM predictions WHERE user_id=%s", (current_user["user_id"],))
    return [
        PredictionResponse(
            id=r["id"],
            match_id=r["match_id"],
            competition_id=r["competition_id"],
            outcome=r["outcome"],
            predicted_score=r["predicted_score"],
            points=r["points"],
        )
        for r in rows
    ]


@router.put("/{prediction_id}", response_model=PredictionResponse)
def update_prediction(
    prediction_id: int,
    body: PredictionRequest,
    current_user: dict = Depends(get_current_user),
):
    row = fetchone(
        "SELECT * FROM predictions WHERE id=%s AND user_id=%s",
        (prediction_id, current_user["user_id"]),
    )
    if not row:
        raise HTTPException(404, "Prediction not found")
    execute(
        "UPDATE predictions SET outcome=%s, predicted_score=%s WHERE id=%s",
        (body.outcome, body.predicted_score, prediction_id),
    )
    _recalculate_and_update(prediction_id)
    row = fetchone("SELECT * FROM predictions WHERE id=%s", (prediction_id,))
    return PredictionResponse(
        id=row["id"],
        match_id=row["match_id"],
        competition_id=row["competition_id"],
        outcome=row["outcome"],
        predicted_score=row["predicted_score"],
        points=row["points"],
    )


@router.delete("/{prediction_id}")
def delete_prediction(prediction_id: int, current_user: dict = Depends(get_current_user)):
    row = fetchone(
        "SELECT id FROM predictions WHERE id=%s AND user_id=%s",
        (prediction_id, current_user["user_id"]),
    )
    if not row:
        raise HTTPException(404, "Prediction not found")
    execute("DELETE FROM predictions WHERE id=%s", (prediction_id,))
    return {"success": True}


@router.get("/match/{match_id}")
def get_match_predictions(match_id: int, current_user: dict = Depends(get_current_user)):
    rows = fetchall(
        """SELECT p.outcome, p.predicted_score, p.points, u.username, u.id as user_id,
                  p.updated_at::text as updated_at, COALESCE(p.edit_count, 0) as edit_count
           FROM predictions p JOIN users u ON u.id = p.user_id
           WHERE p.match_id = %s
           ORDER BY p.points DESC NULLS LAST, u.username""",
        (match_id,),
    )
    return [
        {
            "username": r["username"],
            "user_id": r["user_id"],
            "outcome": r["outcome"],
            "predicted_score": r["predicted_score"],
            "points": r["points"] or 0,
            "updated_at": r.get("updated_at"),
            "edit_count": r.get("edit_count") or 0,
        }
        for r in rows
    ]
