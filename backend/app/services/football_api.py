import requests
import time
from typing import List, Dict, Optional
from app.utils.config import FOOTBALL_DATA_API_KEY

BASE_URL = "https://api.football-data.org/v4"
HEADERS = {"X-Auth-Token": FOOTBALL_DATA_API_KEY}

# Simple in-memory cache: {cache_key: (timestamp, data)}
_cache: Dict[str, tuple] = {}
CACHE_TTL = 300  # 5 minutes


def _cached_get(url: str, params: dict = None) -> dict:
    cache_key = url + str(sorted((params or {}).items()))
    now = time.time()
    if cache_key in _cache:
        ts, data = _cache[cache_key]
        if now - ts < CACHE_TTL:
            return data
    try:
        resp = requests.get(url, headers=HEADERS, params=params, timeout=30)
        resp.raise_for_status()
    except requests.exceptions.Timeout:
        raise RuntimeError("football-data.org timeout — try again")
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"football-data.org error: {e}")
    data = resp.json()
    _cache[cache_key] = (now, data)
    return data


def get_matches(
    competition_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None,
) -> List[Dict]:
    # Use /competitions/{id}/matches — the generic /matches endpoint ignores
    # dateFrom/dateTo when competitions filter is also set (API limitation)
    params: Dict = {}
    if date_from:
        params["dateFrom"] = date_from
    if date_to:
        params["dateTo"] = date_to
    if status:
        params["status"] = status

    data = _cached_get(f"{BASE_URL}/competitions/{competition_id}/matches", params)

    result = []
    for m in data.get("matches", []):
        score = m.get("score", {})
        full_time = score.get("fullTime", {})
        venue_data = m.get("venue") or {}
        venue_name = venue_data if isinstance(venue_data, str) else venue_data.get("name")
        result.append({
            "external_id": m["id"],
            "competition_id": competition_id,
            "home_team": m["homeTeam"]["name"],
            "away_team": m["awayTeam"]["name"],
            "home_team_crest": m["homeTeam"].get("crest"),
            "away_team_crest": m["awayTeam"].get("crest"),
            "match_date": m["utcDate"],
            "venue": venue_name,
            "status": m["status"],
            "home_goals": full_time.get("home"),
            "away_goals": full_time.get("away"),
            "matchday": m.get("matchday"),
        })
    return result


def get_competitions() -> List[Dict]:
    data = _cached_get(f"{BASE_URL}/competitions")
    return [
        {
            "id": c["id"],
            "name": c["name"],
            "code": c.get("code", ""),
            "type": c.get("type", ""),
            "emblem": c.get("emblem"),
            "area": c.get("area", {}).get("name", ""),
        }
        for c in data.get("competitions", [])
    ]


def invalidate_cache():
    _cache.clear()
