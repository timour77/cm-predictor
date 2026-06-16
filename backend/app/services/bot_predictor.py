import json
import re
import requests
from typing import Optional

import anthropic

from app.database import fetchone, execute, fetchall
from app.services.football_api import _cached_get, BASE_URL
from app.utils.config import ODDS_API_KEY, ANTHROPIC_API_KEY

BOT_USERNAME = "Claude"

# Map football-data.org competition IDs → The Odds API sport keys
COMPETITION_SPORT_KEYS = {
    2021: "soccer_epl",
    2014: "soccer_spain_la_liga",
    2002: "soccer_germany_bundesliga",
    2019: "soccer_italy_serie_a",
    2015: "soccer_france_ligue_one",
    2001: "soccer_uefa_champs_league",
    2000: "soccer_fifa_world_cup",
    2018: "soccer_uefa_euro",
}


def get_or_create_bot_user() -> int:
    user = fetchone("SELECT id FROM users WHERE username = %s", (BOT_USERNAME,))
    if user:
        return user["id"]
    return execute(
        "INSERT INTO users (username, is_bot) VALUES (%s, TRUE) RETURNING id",
        (BOT_USERNAME,),
    )


def _normalize_team(name: str) -> str:
    name = name.lower()
    for suffix in [" fc", " cf", " afc", " sc", " bsc", " fk", " sk", " ac", " bc", " united", " city"]:
        if name.endswith(suffix):
            name = name[: -len(suffix)]
    return name.strip()


def _teams_match(odds_name: str, fd_name: str) -> bool:
    a = _normalize_team(odds_name)
    b = _normalize_team(fd_name)
    return a == b or a in b or b in a or a[:6] == b[:6]


def fetch_all_odds(competition_id: int) -> list:
    sport_key = COMPETITION_SPORT_KEYS.get(competition_id)
    if not sport_key or not ODDS_API_KEY:
        return []
    try:
        resp = requests.get(
            f"https://api.the-odds-api.com/v4/sports/{sport_key}/odds",
            params={"apiKey": ODDS_API_KEY, "regions": "eu", "markets": "h2h", "oddsFormat": "decimal"},
            timeout=10,
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return []


def find_odds_for_match(events: list, home_team: str, away_team: str) -> Optional[str]:
    for event in events:
        eh = event.get("home_team", "")
        ea = event.get("away_team", "")
        if _teams_match(eh, home_team) and _teams_match(ea, away_team):
            lines = []
            for bm in event.get("bookmakers", [])[:4]:
                for market in bm.get("markets", []):
                    if market["key"] == "h2h":
                        by_name = {o["name"]: o["price"] for o in market["outcomes"]}
                        h = by_name.get(eh, "?")
                        d = by_name.get("Draw", "?")
                        a = by_name.get(ea, "?")
                        lines.append(f"{bm['title']}: {h} / {d} / {a}")
            if lines:
                return "\n".join(lines)
    return None


def fetch_standings(competition_id: int) -> str:
    try:
        data = _cached_get(f"{BASE_URL}/competitions/{competition_id}/standings")
        for table in data.get("standings", []):
            if table.get("type") == "TOTAL":
                rows = table.get("table", [])[:12]
                lines = []
                for r in rows:
                    gd = r.get("goalDifference", 0)
                    lines.append(
                        f"{r['position']}. {r['team']['name']} — {r['points']}pts (GD {gd:+d})"
                    )
                return "\n".join(lines)
    except Exception:
        pass
    return "Standings unavailable"


def fetch_recent_form(competition_id: int) -> dict[str, list[str]]:
    try:
        data = _cached_get(
            f"{BASE_URL}/competitions/{competition_id}/matches",
            {"status": "FINISHED"},
        )
        form: dict[str, list[str]] = {}
        for m in reversed(data.get("matches", [])):
            score = m.get("score", {}).get("fullTime", {})
            hg, ag = score.get("home"), score.get("away")
            if hg is None or ag is None:
                continue
            home, away = m["homeTeam"]["name"], m["awayTeam"]["name"]
            home_r = "W" if hg > ag else ("D" if hg == ag else "L")
            away_r = "W" if ag > hg else ("D" if ag == hg else "L")
            for team, result in [(home, home_r), (away, away_r)]:
                if team not in form:
                    form[team] = []
                if len(form[team]) < 5:
                    form[team].append(result)
        return form
    except Exception:
        return {}


def generate_prediction(
    home_team: str,
    away_team: str,
    competition_name: str,
    match_date: str,
    standings: str,
    form: dict[str, list[str]],
    odds_text: Optional[str],
) -> dict:
    home_form = " ".join(form.get(home_team, [])) or "unknown"
    away_form = " ".join(form.get(away_team, [])) or "unknown"

    prompt = f"""Predict the result of this football match.

Match: {home_team} vs {away_team}
Competition: {competition_name}
Date: {match_date[:10]}

Current standings (top 12):
{standings}

Recent form (last 5 matches, oldest→newest, W/D/L):
{home_team}: {home_form}
{away_team}: {away_form}
"""
    if odds_text:
        prompt += f"""
Bookmaker odds (home / draw / away):
{odds_text}
"""
    prompt += """
Respond with JSON only — no markdown, no explanation outside the JSON:
{"outcome": "1" or "X" or "2", "predicted_score": "N-N", "reasoning": "one sentence"}"""

    client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=256,
        system="You are a football prediction engine. Return JSON only.",
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # Strip markdown code fences if present
    text = re.sub(r"^```[a-z]*\n?", "", text)
    text = re.sub(r"\n?```$", "", text)
    return json.loads(text.strip())


def run_bot_predictions(competition_id: int, competition_name: str, matches: list) -> dict:
    bot_user_id = get_or_create_bot_user()
    standings = fetch_standings(competition_id)
    form = fetch_recent_form(competition_id)
    odds_events = fetch_all_odds(competition_id)  # single API call for all matches

    results = {"generated": 0, "skipped": 0, "errors": [], "predictions": []}

    for match in matches:
        if match.get("status") not in ("SCHEDULED", "TIMED"):
            results["skipped"] += 1
            continue

        match_id = match["external_id"]
        existing = fetchone(
            "SELECT id FROM predictions WHERE user_id=%s AND match_id=%s",
            (bot_user_id, match_id),
        )
        if existing:
            results["skipped"] += 1
            continue

        home_team = match["home_team"]
        away_team = match["away_team"]
        try:
            odds_text = find_odds_for_match(odds_events, home_team, away_team)
            home_form = " ".join(form.get(home_team, [])) or "unknown"
            away_form = " ".join(form.get(away_team, [])) or "unknown"

            pred = generate_prediction(
                home_team=home_team,
                away_team=away_team,
                competition_name=competition_name,
                match_date=match["match_date"],
                standings=standings,
                form=form,
                odds_text=odds_text,
            )
            execute(
                """INSERT INTO predictions
                   (user_id, match_id, competition_id, outcome, predicted_score, updated_at, edit_count)
                   VALUES (%s,%s,%s,%s,%s,NOW(),0)
                   ON CONFLICT (user_id, match_id) DO NOTHING""",
                (bot_user_id, match_id, competition_id, pred["outcome"], pred["predicted_score"]),
            )
            execute(
                """INSERT INTO bot_prediction_logs
                   (match_id, competition_id, home_team, away_team, match_date,
                    standings, odds, home_form, away_form, outcome, predicted_score, reasoning)
                   VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)""",
                (
                    match_id, competition_id, home_team, away_team, match["match_date"],
                    standings, odds_text or "not available",
                    home_form, away_form,
                    pred["outcome"], pred["predicted_score"], pred.get("reasoning", ""),
                ),
            )
            results["generated"] += 1
            results["predictions"].append({
                "match": f"{home_team} vs {away_team}",
                "date": match["match_date"][:10],
                "outcome": pred["outcome"],
                "score": pred["predicted_score"],
                "reasoning": pred.get("reasoning", ""),
                "odds": odds_text or "not available",
            })
        except Exception as e:
            results["errors"].append(f"match {match_id} ({home_team} vs {away_team}): {e}")

    return results
