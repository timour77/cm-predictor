# CM Predictor — Telegram Mini App

Telegram Mini App для прогнозов на футбольные матчи.

## Запуск

### Backend

```bash
cd backend
python3.12 -m venv venv          # только первый раз
venv/bin/pip install -r requirements.txt  # только первый раз
venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

API доступен на http://localhost:8000  
Документация: http://localhost:8000/docs

### Frontend

```bash
cd frontend
npm install    # только первый раз
npm run dev
```

Приложение на http://localhost:5173

## API ключ

football-data.org API ключ уже прописан в `backend/.env`.

## Чемпионаты (реальные ID)

| ID   | Название              |
|------|-----------------------|
| 2000 | FIFA World Cup        |
| 2001 | UEFA Champions League |
| 2002 | Bundesliga            |
| 2014 | Primera Division (ES) |
| 2015 | Ligue 1               |
| 2019 | Serie A               |
| 2021 | Premier League        |

## Система очков

- ✅ Правильный исход (1/X/2): **1 очко**
- ✅ Точный счёт: **+3 очка** (дополнительно)
