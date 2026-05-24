# 🚀 БЫСТРЫЙ СТАРТ РАЗРАБОТКИ

## 📋 Что нужно знать перед тем как передать в Claude Code

### 1. FOOTBALL-DATA.ORG API

**API ключ:** `07cdd2788af245f39acf16042394eac2`

**Основной endpoint:**
```
GET https://api.football-data.org/v4/matches
Headers: { 'X-Auth-Token': '07cdd2788af245f39acf16042394eac2' }
```

**Примеры запросов:**
```python
# Получить все матчи
https://api.football-data.org/v4/matches

# На конкретный день
https://api.football-data.org/v4/matches?dateFrom=2026-06-11&dateTo=2026-06-11

# Конкретного чемпионата
https://api.football-data.org/v4/matches?competitions=3

# Статус (SCHEDULED, LIVE, FINISHED)
https://api.football-data.org/v4/matches?status=SCHEDULED

# Все вместе
https://api.football-data.org/v4/matches?competitions=3&dateFrom=2026-06-11&dateTo=2026-06-11&status=SCHEDULED
```

**Популярные ID чемпионатов:**
- 3 = FIFA World Cup
- 2014 = Premier League
- 2015 = Championship (England)
- 2016 = La Liga (Spain)
- 2017 = Bundesliga (Germany)
- 2018 = Serie A (Italy)
- 2019 = Ligue 1 (France)
- 2001 = Champions League
- 2000 = UEFA Cup

---

## 🏗️ РАЗДЕЛЕНИЕ НА МОДУЛИ

### Backend состоит из:

#### 1. **main.py** (entry point)
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, matches, predictions, leaderboard, competitions

app = FastAPI(title="CM Predictor API")

# CORS для фронтенда
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"])

# Подключение роутеров
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(matches.router, prefix="/api/matches", tags=["matches"])
app.include_router(predictions.router, prefix="/api/predictions", tags=["predictions"])
app.include_router(leaderboard.router, prefix="/api/leaderboard", tags=["leaderboard"])
app.include_router(competitions.router, prefix="/api/competitions", tags=["competitions"])

@app.get("/health")
def health_check():
    return {"status": "ok"}
```

#### 2. **app/database.py** (работа с БД)
```python
import sqlite3
from typing import Optional, List, Dict

class Database:
    def __init__(self, db_path: str = "predictor.db"):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Инициализация базы данных"""
        # Создать все таблицы если их нет
    
    def execute(self, query: str, params: tuple = ()):
        """Выполнить SQL запрос"""
    
    def fetch_one(self, query: str, params: tuple = ()):
        """Получить один результат"""
    
    def fetch_all(self, query: str, params: tuple = ()):
        """Получить все результаты"""

db = Database()
```

#### 3. **app/models.py** (Pydantic модели)
```python
from pydantic import BaseModel
from typing import Optional

class User(BaseModel):
    id: int
    username: str
    created_at: str

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    user_id: int
    token: str
    username: str

class PredictionRequest(BaseModel):
    match_id: int
    competition_id: int
    outcome: str  # "1", "X", "2"
    predicted_score: Optional[str] = None

class PredictionResponse(BaseModel):
    id: int
    match_id: int
    outcome: str
    predicted_score: Optional[str]
    points: int
```

#### 4. **app/routers/auth.py** (аутентификация)
```python
from fastapi import APIRouter, HTTPException
from app.models import LoginRequest, LoginResponse
from app.database import db
import jwt
from datetime import datetime, timedelta

router = APIRouter()

@router.post("/register", response_model=LoginResponse)
def register(user: LoginRequest):
    """Регистрация нового пользователя"""
    # Проверить что пользователь не существует
    # Хешировать пароль
    # Сохранить в БД
    # Вернуть token

@router.post("/login", response_model=LoginResponse)
def login(user: LoginRequest):
    """Логин пользователя"""
    # Найти пользователя в БД
    # Проверить пароль
    # Создать JWT token
    # Вернуть user_id и token

@router.post("/logout")
def logout(token: str):
    """Выход пользователя"""
    # Инвалидировать token
```

#### 5. **app/routers/matches.py** (матчи)
```python
from fastapi import APIRouter, Query
from app.services.football_api import get_matches_for_date
from app.database import db

router = APIRouter()

@router.get("/")
def get_matches(
    competition_id: int = Query(...),
    date: Optional[str] = Query(None),  # "2026-06-11"
    status: Optional[str] = Query(None)  # "SCHEDULED", "FINISHED"
):
    """Получить матчи на день"""
    # Получить от football-data.org
    # Вернуть с пользовательскими прогнозами если авторизован
```

#### 6. **app/routers/predictions.py** (прогнозы)
```python
@router.post("/")
def save_prediction(prediction: PredictionRequest):
    """Сохранить прогноз"""
    # Проверить что матч ещё не начался
    # Сохранить в БД
    # Вернуть успех

@router.get("/")
def get_predictions(competition_id: int = Query(...)):
    """Получить прогнозы пользователя"""

@router.put("/{prediction_id}")
def update_prediction(prediction_id: int, prediction: PredictionRequest):
    """Обновить прогноз"""

@router.delete("/{prediction_id}")
def delete_prediction(prediction_id: int):
    """Удалить прогноз"""
```

#### 7. **app/routers/leaderboard.py** (таблица лидеров)
```python
@router.get("/")
def get_leaderboard(competition_id: int = Query(...)):
    """Получить таблицу лидеров"""
    # Запрос из БД с сортировкой по очкам
    # Лимит 100 записей

@router.get("/me")
def get_my_position(competition_id: int = Query(...)):
    """Мое место в таблице"""
```

#### 8. **app/services/football_api.py** (интеграция API)
```python
import requests
from datetime import datetime

API_KEY = "07cdd2788af245f39acf16042394eac2"
BASE_URL = "https://api.football-data.org/v4"

def get_matches(
    competition_id: int,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    status: Optional[str] = None
) -> List[Dict]:
    """Получить матчи из football-data.org"""
    params = {
        'competitions': competition_id
    }
    if date_from:
        params['dateFrom'] = date_from
    if date_to:
        params['dateTo'] = date_to
    if status:
        params['status'] = status
    
    headers = {'X-Auth-Token': API_KEY}
    
    response = requests.get(f'{BASE_URL}/matches', params=params, headers=headers)
    data = response.json()
    
    return [
        {
            'external_id': m['id'],
            'home_team': m['homeTeam']['name'],
            'away_team': m['awayTeam']['name'],
            'match_date': m['utcDate'],
            'status': m['status'],
            'home_goals': m['score']['fullTime']['home'],
            'away_goals': m['score']['fullTime']['away'],
            'venue': m.get('venue', {}).get('name')
        }
        for m in data.get('matches', [])
    ]

def get_competitions() -> List[Dict]:
    """Получить список чемпионатов"""
    headers = {'X-Auth-Token': API_KEY}
    response = requests.get(f'{BASE_URL}/competitions', headers=headers)
    data = response.json()
    
    return [
        {
            'id': c['id'],
            'name': c['name'],
            'code': c['code'],
            'type': c['type']
        }
        for c in data.get('competitions', [])
    ]
```

#### 9. **app/services/scoring.py** (подсчёт очков)
```python
def get_result(home_goals: int, away_goals: int) -> str:
    """Определить исход"""
    if home_goals > away_goals:
        return "1"
    elif home_goals < away_goals:
        return "2"
    else:
        return "X"

def calculate_points(prediction: Dict, home_goals: int, away_goals: int) -> int:
    """Подсчитать очки за прогноз"""
    points = 0
    actual_result = get_result(home_goals, away_goals)
    
    # 1 очко за правильный исход
    if prediction['outcome'] == actual_result:
        points += 1
    
    # 3 очка за точный счёт
    predicted_score = prediction.get('predicted_score')
    actual_score = f"{home_goals}-{away_goals}"
    if predicted_score == actual_score:
        points += 3
    
    return points
```

### Frontend состоит из:

#### 1. **pages/LoginPage.jsx** (страница входа)
```javascript
export function LoginPage() {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  
  const handleLogin = async () => {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password })
    })
    // Сохранить токен и перейти
  }
  
  return (
    <div className="login">
      <input value={username} onChange={e => setUsername(e.target.value)} placeholder="Username" />
      <input value={password} onChange={e => setPassword(e.target.value)} placeholder="Password" type="password" />
      <button onClick={handleLogin}>Login</button>
    </div>
  )
}
```

#### 2. **components/MatchCard.jsx** (карточка матча)
```javascript
export function MatchCard({ match, onPredictionChange, savedPrediction }) {
  const [outcome, setOutcome] = useState(savedPrediction?.outcome || null)
  const [score, setScore] = useState(savedPrediction?.predicted_score || '')
  
  const handleSave = async () => {
    await fetch('/api/predictions', {
      method: 'POST',
      body: JSON.stringify({
        match_id: match.id,
        competition_id: match.competition_id,
        outcome,
        predicted_score: score
      })
    })
  }
  
  return (
    <div className="match-card">
      <h3>{match.home_team} vs {match.away_team}</h3>
      
      {match.status === 'SCHEDULED' && (
        <>
          <button onClick={() => setOutcome('1')}>Win 1</button>
          <button onClick={() => setOutcome('X')}>Draw</button>
          <button onClick={() => setOutcome('2')}>Win 2</button>
          <input value={score} onChange={e => setScore(e.target.value)} placeholder="2-1" />
          <button onClick={handleSave}>Save</button>
        </>
      )}
      
      {match.status === 'FINISHED' && (
        <p>Result: {match.home_goals}-{match.away_goals}</p>
      )}
    </div>
  )
}
```

#### 3. **components/LeaderboardTable.jsx** (таблица)
```javascript
export function LeaderboardTable({ leaderboard }) {
  return (
    <table>
      <thead>
        <tr>
          <th>Rank</th>
          <th>Username</th>
          <th>Points</th>
          <th>Outcomes</th>
          <th>Scores</th>
        </tr>
      </thead>
      <tbody>
        {leaderboard.map((player, idx) => (
          <tr key={player.user_id}>
            <td>{idx + 1}</td>
            <td>{player.username}</td>
            <td>{player.total_points}</td>
            <td>{player.correct_outcomes}</td>
            <td>{player.correct_scores}</td>
          </tr>
        ))}
      </tbody>
    </table>
  )
}
```

---

## 📦 DEPENDENCIES

### Backend (requirements.txt)
```
fastapi==0.104.1
uvicorn==0.24.0
requests==2.31.0
pydantic==2.5.0
python-dotenv==1.0.0
bcrypt==4.1.1
PyJWT==2.8.1
apscheduler==3.10.4
sqlite3
```

### Frontend (package.json)
```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "@telegram-apps/sdk": "^0.1.0"
  },
  "devDependencies": {
    "vite": "^5.0.0",
    "@vitejs/plugin-react": "^4.2.0"
  }
}
```

---

## 🔑 КРИТИЧЕСКИЕ МОМЕНТЫ

### 1. CORS на frontend
- Должны быть разные URL для фронтенда и бэкенда
- Бэкенд должен разрешать CORS с URL фронтенда

### 2. Telegram Mini App
- При открытии нужно получить Telegram user ID
- Использовать `@telegram-apps/sdk` для инициализации
- Передавать initData на backend для верификации (optional)

### 3. Безопасность
- Никогда не отправлять API ключ на frontend!
- Все запросы к football-data.org только с backend
- Хешировать пароли перед сохранением

### 4. Производительность
- Кэшировать матчи локально
- Обновлять результаты в фоне (APScheduler)
- Пагинация для лидеров (100 за раз)

### 5. Error Handling
- Проверить статус ответов от API
- Graceful degradation если API недоступен
- Логировать ошибки на backend

---

## 🎯 ПОРЯДОК РАЗРАБОТКИ

1. ✅ Backend базовая структура
2. ✅ Аутентификация
3. ✅ Интеграция с football-data.org
4. ✅ Матчи и прогнозы (CRUD)
5. ✅ Подсчёт очков
6. ✅ Таблица лидеров
7. ✅ Frontend базовая структура
8. ✅ Pages и Components
9. ✅ API интеграция
10. ✅ Telegram SDK интеграция
11. ✅ Тестирование локально
12. ✅ Deploy

---

## ⚠️ ВАЖНЫЕ ПРИМЕЧАНИЯ

- API ключ: `07cdd2788af245f39acf16042394eac2` (защищай это!)
- Для быстрого старта используй SQLite (не требует отдельного сервера)
- Frontend можно разрабатывать параллельно с backend
- Протестируй в Telegram Mini App очень рано (может быть много surprises)

---

## 📞 ГОТОВО!

Передай **CM_PREDICTOR_PLAN.md** + этот файл в Claude Code и скажи:

> "Реализуй Telegram Mini App для прогнозов матчей по плану. Начни с backend (FastAPI), потом frontend (React). Используй football-data.org API для получения матчей."

Good luck! 🚀
