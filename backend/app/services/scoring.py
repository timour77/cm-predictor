from typing import Dict, Optional


def get_result(home_goals: int, away_goals: int) -> str:
    if home_goals > away_goals:
        return "1"
    elif home_goals < away_goals:
        return "2"
    return "X"


def calculate_points(
    outcome: Optional[str],
    predicted_score: Optional[str],
    home_goals: int,
    away_goals: int
) -> int:
    points = 0
    actual_result = get_result(home_goals, away_goals)

    if outcome and outcome == actual_result:
        points += 1

    actual_score = f"{home_goals}-{away_goals}"
    if predicted_score and predicted_score == actual_score:
        points += 3

    return points
