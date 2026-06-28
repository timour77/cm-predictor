from typing import Optional


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
    away_goals: int,
    penalty_winner: Optional[str] = None,
) -> int:
    # In knockout matches that go to penalties, add 1 to the winner's goals so
    # a predicted score of 2-1 (or outcome "1") matches a 1-1 → pens home win.
    if penalty_winner == "home":
        home_goals = home_goals + 1
    elif penalty_winner == "away":
        away_goals = away_goals + 1

    actual_result = get_result(home_goals, away_goals)
    actual_score = f"{home_goals}-{away_goals}"

    if predicted_score and predicted_score == actual_score:
        return 3
    if outcome and outcome == actual_result:
        return 1
    return 0
