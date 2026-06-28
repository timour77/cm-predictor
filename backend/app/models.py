from pydantic import BaseModel
from typing import Optional, List


class RegisterRequest(BaseModel):
    username: str
    password: str


class TelegramAuthRequest(BaseModel):
    initData: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    user_id: int
    token: str
    username: str
    photo_url: Optional[str] = None


class PredictionRequest(BaseModel):
    match_id: int
    competition_id: int
    outcome: Optional[str] = None   # "1", "X", "2"
    predicted_score: Optional[str] = None  # "2-1"


class PredictionResponse(BaseModel):
    id: int
    match_id: int
    competition_id: int
    outcome: Optional[str]
    predicted_score: Optional[str]
    points: int


class MatchResponse(BaseModel):
    external_id: int
    competition_id: int
    competition_name: Optional[str] = None
    home_team: str
    away_team: str
    home_team_id: Optional[int] = None
    away_team_id: Optional[int] = None
    home_team_crest: Optional[str]
    away_team_crest: Optional[str]
    match_date: str
    venue: Optional[str]
    status: str
    home_goals: Optional[int]
    away_goals: Optional[int]
    matchday: Optional[int]
    stage: Optional[str] = None
    user_prediction: Optional[PredictionResponse] = None


class LeaderboardEntry(BaseModel):
    rank: int
    user_id: int
    username: str
    photo_url: Optional[str] = None
    total_points: int
    correct_outcomes: int
    correct_scores: int
    is_bot: bool = False


class UserStats(BaseModel):
    created_at: Optional[str]
    total_predictions: int
    total_points: int
    correct_predictions: int
    rank: Optional[int]


class CompetitionResponse(BaseModel):
    id: int
    name: str
    code: str
    type: str
    emblem: Optional[str]
    area: str
    is_active: bool


class UserListEntry(BaseModel):
    id: int
    username: str
    photo_url: Optional[str] = None
    total_predictions: int
    total_points: int
    correct_predictions: int


class UserPredictionHistory(BaseModel):
    id: int
    match_id: int
    competition_id: int
    competition_name: Optional[str]
    home_team: Optional[str]
    away_team: Optional[str]
    home_goals: Optional[int]
    away_goals: Optional[int]
    match_date: Optional[str]
    match_status: Optional[str]
    outcome: Optional[str]
    predicted_score: Optional[str]
    points: int


class StandingEntry(BaseModel):
    position: int
    team_id: int
    team_name: str
    team_crest: Optional[str]
    played: int
    won: int
    draw: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class GroupStanding(BaseModel):
    group: str
    table: List[StandingEntry]
