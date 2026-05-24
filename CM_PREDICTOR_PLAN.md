# 🏆 Telegram Mini App для Прогнозов Матчей - ПЛАН РАЗРАБОТКИ

## 📋 Обзор проекта

**Название:** CM Predictor (Championship Match Predictor)

**Тип:** Telegram Mini App (встроенное веб-приложение в Telegram)

**Стек:**
- Frontend: React + Vite
- Backend: FastAPI (Python)
- БД: SQLite (локальная разработка) / Supabase (production)
- API: football-data.org (v4)

**API ключ:** `07cdd2788af245f39acf16042394eac2`

---

## 🏗️ АРХИТЕКТУРА

```
┌─────────────────────────────────────────────────────────┐
│                    TELEGRAM                             │
│  ┌─────────────────────────────────────────────────┐   │
│  │         Mini App (встроенный браузер)           │   │
│  │                                                 │   │
│  │  ┌──────────────────────────────────────────┐  │   │
│  │  │        React Frontend (Vite)             │  │   │
│  │  │  - Логин                                 │  │   │
│  │  │  - Выбор чемпионата                      │  │   │
│  │  │  - Список матчей на день                 │  │   │
│  │  │  - Форма прогнозов                       │  │   │
│  │  │  - Таблица лидеров                       │  │   │
│  │  └──────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
           ↓ HTTP запросы
┌─────────────────────────────────────────────────────────┐
│               FASTAPI BACKEND                           │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │  /auth - Логин/регистрация                       │  │
│  │  /matches - Получение матчей на день            │  │
│  │  /predictions - Сохранение/получение прогнозов  │  │
│  │  /leaderboard - Таблица лидеров                 │  │
│  │  /competitions - Список чемпионатов             │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
      ↓ API запросы        ↓ SQL запросы
┌──────────────────┐  ┌──────────────────┐
│ football-data.org│  │   SQLite БД      │
│                  │  │  (или Supabase)  │
│ - Матчи          │  │                  │
│ - Результаты     │  │ - users          │
│ - Статистика     │  │ - predictions    │
└──────────────────┘  │ - leaderboard    │
                      └──────────────────┘
```

---

## 📁 СТРУКТУРА ПРОЕКТА

```
cm-predictor/
│
├── backend/
│   ├── main.py                 # FastAPI app
│   ├── requirements.txt
│   ├── .env.example
│   │
│   ├── app/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite / Supabase
│   │   ├── models.py           # Pydantic models
│   │   │
│   │   ├── routers/
│   │   │   ├── auth.py         # Логин/регистрация
│   │   │   ├── matches.py      # Матчи и API
│   │   │   ├── predictions.py  # Прогнозы
│   │   │   ├── leaderboard.py  # Таблица лидеров
│   │   │   └── competitions.py # Выбор чемпионата
│   │   │
│   │   ├── services/
│   │   │   ├── football_api.py # Интеграция с football-data.org
│   │   │   └── scoring.py      # Логика подсчёта очков
│   │   │
│   │   └── utils/
│   │       └── config.py       # Конфигурация
│   │
│   └── tests/
│       └── test_api.py
│
├── frontend/
│   ├── package.json
│   ├── vite.config.js
│   ├── .env.example
│   │
│   ├── src/
│   │   ├── main.jsx            # Entry point
│   │   ├── App.jsx             # Root component
│   │   ├── App.css
│   │   │
│   │   ├── pages/
│   │   │   ├── LoginPage.jsx
│   │   │   ├── HomePage.jsx
│   │   │   ├── MatchesPage.jsx
│   │   │   ├── LeaderboardPage.jsx
│   │   │   └── SettingsPage.jsx
│   │   │
│   │   ├── components/
│   │   │   ├── Header.jsx
│   │   │   ├── MatchCard.jsx
│   │   │   ├── PredictionForm.jsx
│   │   │   ├── LeaderboardTable.jsx
│   │   │   └── CompetitionSelector.jsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useTelegramUser.js
│   │   │   ├── useAuth.js
│   │   │   └── useApi.js
│   │   │
│   │   ├── services/
│   │   │   └── api.js          # API клиент
│   │   │
│   │   ├── utils/
│   │   │   └── constants.js
│   │   │
│   │   └── styles/
│   │       ├── index.css
│   │       └── variables.css
│   │
│   └── public/
│       └── index.html
│
├── telegram_bot/
│   ├── bot.py
│   └── requirements.txt
│
└── README.md
```

---

## 🗄️ СХЕМА БД (SQLite)

```sql
-- Таблица пользователей
CREATE TABLE users (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE NOT NULL,
  password TEXT NOT NULL,  -- хешированный пароль
  telegram_id INTEGER,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица прогнозов
CREATE TABLE predictions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL,
  match_id INTEGER NOT NULL,        -- ID матча из football-data.org
  competition_id INTEGER NOT NULL,  -- ID чемпионата
  outcome TEXT,                     -- "1", "X", "2" (победа 1, ничья, победа 2)
  predicted_score TEXT,             -- Прогноз точного счёта "2-1"
  points INTEGER DEFAULT 0,         -- Полученные очки
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id),
  UNIQUE(user_id, match_id)
);

-- Таблица результатов матчей
CREATE TABLE match_results (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  external_match_id INTEGER NOT NULL,  -- ID матча из football-data.org
  competition_id INTEGER NOT NULL,
  home_team TEXT NOT NULL,
  away_team TEXT NOT NULL,
  home_goals INTEGER,
  away_goals INTEGER,
  match_date TIMESTAMP,
  status TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Таблица лидеров (денормализованная для быстрого доступа)
CREATE TABLE leaderboard (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  user_id INTEGER NOT NULL UNIQUE,
  competition_id INTEGER NOT NULL,
  total_points INTEGER DEFAULT 0,
  correct_outcomes INTEGER DEFAULT 0,
  correct_scores INTEGER DEFAULT 0,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Таблица поддерживаемых чемпионатов
CREATE TABLE competitions (
  id INTEGER PRIMARY KEY,
  external_id INTEGER NOT NULL,  -- ID из football-data.org
  name TEXT NOT NULL,
  code TEXT,
  type TEXT,
  is_active INTEGER DEFAULT 1,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Индексы
CREATE INDEX idx_predictions_user ON predictions(user_id);
CREATE INDEX idx_predictions_competition ON predictions(competition_id);
CREATE INDEX idx_leaderboard_competition ON leaderboard(competition_id, total_points DESC);
CREATE INDEX idx_match_results_competition ON match_results(competition_id);
```

---

## 🔑 API ENDPOINTS

### Authentication
```
POST /api/auth/register
  Body: { username, password }
  Response: { user_id, token }

POST /api/auth/login
  Body: { username, password }
  Response: { user_id, token, username }

POST /api/auth/logout
  Response: { success }
```

### Competitions
```
GET /api/competitions
  Response: [
    { id, name, code, type, is_active },
    ...
  ]

GET /api/competitions/{id}/info
  Response: { id, name, code, type, total_matches, completed_matches }
```

### Matches
```
GET /api/matches?competition_id=3&date=2026-06-11
  Response: [
    {
      id, external_id, competition_id,
      home_team, away_team,
      match_date, venue, status,
      home_goals, away_goals,
      user_prediction: { outcome, predicted_score }
    },
    ...
  ]

GET /api/matches?competition_id=3&status=SCHEDULED
  Response: [...]  # Только предстоящие матчи

GET /api/matches?competition_id=3&status=FINISHED
  Response: [...]  # Только завершённые матчи
```

### Predictions
```
POST /api/predictions
  Body: {
    match_id, competition_id, outcome, predicted_score
  }
  Response: { success, points_earned }

PUT /api/predictions/{prediction_id}
  Body: { outcome, predicted_score }
  Response: { success, points_earned }

GET /api/predictions?competition_id=3
  Response: [
    { id, match_id, outcome, predicted_score, points, created_at },
    ...
  ]

DELETE /api/predictions/{prediction_id}
  Response: { success }
```

### Leaderboard
```
GET /api/leaderboard?competition_id=3
  Response: [
    {
      rank, user_id, username,
      total_points, correct_outcomes, correct_scores
    },
    ...
  ]

GET /api/leaderboard/me?competition_id=3
  Response: { rank, user_id, username, total_points, ... }
```

---

## 🎨 ФРОНТЕНД СТРАНИЦЫ

### 1. **Login Page** (Страница входа)
- Два поля: Username и Password
- Кнопка Login
- Ссылка на регистрацию (или встроенная форма)
- Валидация перед отправкой
- Сохранение токена в localStorage

### 2. **Home Page** (Главная страница)
- Header с именем пользователя и выходом
- **Competition Selector** - выпадающий список чемпионатов
- **Date/Matchday Selector** - выбор даты или номера тура
- Кнопка "Today" для быстрого выбора сегодня
- Кнопка "Next Matchday" для перехода на следующий тур

### 3. **Matches Page** (Список матчей на выбранный день)
- Список матчей в виде карточек
- На каждой карточке:
  - 🏠 Домашняя команда
  - 🏢 Гостевая команда
  - ⏰ Время матча
  - 🏟️ Стадион
  - Статус (SCHEDULED, LIVE, FINISHED)
  
- **Если SCHEDULED (матч ещё не начался):**
  - Кнопки для выбора исхода (1 / X / 2)
  - Поле для ввода точного счёта (2-1)
  - Кнопка "Save Prediction"
  - Отображение сохранённого прогноза (если есть)
  
- **Если FINISHED (матч завершён):**
  - Показать результат (зелёный/красный для угадывания)
  - Показать заработанные очки (если предсказывал)

### 4. **Leaderboard Page** (Таблица лидеров)
- Таблица с колонками:
  - 🥇 Место
  - 👤 Имя пользователя
  - 🔢 Всего очков
  - ✅ Угадано исходов
  - 🎯 Угадано точных счётов
- Выделение текущего пользователя
- Подгрузка предыдущих 100 мест скроллингом
- Переключение между чемпионатами

### 5. **Settings Page** (Настройки)
- Выбор чемпионата по умолчанию
- Выход (logout)
- Информация об аккаунте
- Версия приложения

---

## 🔄 ЛОГИКА ПОДСЧЁТА ОЧКОВ

```python
def calculate_points(prediction, match_result):
    """
    prediction: { outcome, predicted_score }
    match_result: { home_goals, away_goals }
    
    Returns: points (int)
    """
    points = 0
    actual_result = get_result(match_result['home_goals'], match_result['away_goals'])
    
    # 1. Проверка угадывания исхода
    if prediction['outcome'] == actual_result:
        points += 1  # 1 очко за правильный исход
    
    # 2. Проверка угадывания точного счёта
    actual_score = f"{match_result['home_goals']}-{match_result['away_goals']}"
    if prediction['predicted_score'] == actual_score:
        points += 3  # 3 очка за точный счёт (в дополнение к исходу)
    
    return points

def get_result(home_goals, away_goals):
    """Возвращает '1', 'X' или '2'"""
    if home_goals > away_goals:
        return '1'
    elif home_goals < away_goals:
        return '2'
    else:
        return 'X'
```

**Система очков:**
- ✅ Правильный исход (1, X, 2): **1 очко**
- ✅ Точный счёт (2-1): **3 очка** (дополнительно к исходу, если угадан)
- ❌ Неправильный прогноз: **0 очков**

---

## 🔌 ИНТЕГРАЦИЯ С football-data.org API

### Получение матчей
```python
def get_matches_for_date(competition_id: int, date: str) -> List[Dict]:
    """
    competition_id: ID чемпионата (3 для ЧМ, 2014 для Premier League и т.д.)
    date: '2026-06-11'
    
    Returns: список матчей на эту дату
    """
    url = 'https://api.football-data.org/v4/matches'
    params = {
        'competitions': competition_id,
        'dateFrom': date,
        'dateTo': date
    }
    headers = {'X-Auth-Token': API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    return [
        {
            'external_id': match['id'],
            'home_team': match['homeTeam']['name'],
            'away_team': match['awayTeam']['name'],
            'home_goals': match['score']['fullTime']['home'],
            'away_goals': match['score']['fullTime']['away'],
            'match_date': match['utcDate'],
            'venue': match['venue']['name'],
            'status': match['status']
        }
        for match in data['matches']
    ]
```

### Получение чемпионатов
```python
def get_competitions() -> List[Dict]:
    """Получить список всех поддерживаемых чемпионатов"""
    url = 'https://api.football-data.org/v4/competitions'
    headers = {'X-Auth-Token': API_KEY}
    
    response = requests.get(url, headers=headers)
    data = response.json()
    
    return [
        {
            'id': comp['id'],
            'name': comp['name'],
            'code': comp['code'],
            'type': comp['type']
        }
        for comp in data['competitions']
    ]
```

### Обновление результатов
```python
def update_match_results(competition_id: int):
    """
    Получить завершённые матчи и обновить БД
    Запускать каждые 5 минут при помощи APScheduler
    """
    url = 'https://api.football-data.org/v4/matches'
    params = {
        'competitions': competition_id,
        'status': 'FINISHED'
    }
    headers = {'X-Auth-Token': API_KEY}
    
    response = requests.get(url, params=params, headers=headers)
    data = response.json()
    
    for match in data['matches']:
        # Обновляем в БД
        save_to_db({
            'external_id': match['id'],
            'home_goals': match['score']['fullTime']['home'],
            'away_goals': match['score']['fullTime']['away'],
            'status': 'FINISHED'
        })
        
        # Пересчитываем очки для всех прогнозов по этому матчу
        recalculate_points_for_match(match['id'])
```

---

## 🔐 АУТЕНТИФИКАЦИЯ

### Локально (для разработки)
- Простая аутентификация по username/password
- Хеширование пароля (bcrypt)
- JWT токены для сессий
- Сохранение токена в localStorage (frontend)

### Telegram Integration
- При открытии Mini App получать Telegram user ID
- Связывать аккаунт с telegram_id
- Использовать Telegram initData для верификации

---

## 🚀 ЭТАПЫ РАЗРАБОТКИ

### Этап 1: Backend базовая структура
- [x] FastAPI приложение
- [x] SQLite БД с таблицами
- [x] Маршруты аутентификации
- [x] Интеграция с football-data.org API

### Этап 2: Backend логика
- [x] Получение матчей на день
- [x] Сохранение прогнозов
- [x] Подсчёт очков
- [x] Таблица лидеров

### Этап 3: Frontend структура
- [x] React + Vite базовый setup
- [x] Роутинг между страницами
- [x] Компоненты для каждой страницы

### Этап 4: Frontend функциональность
- [x] Страница логина
- [x] Список матчей
- [x] Форма прогнозов
- [x] Таблица лидеров

### Этап 5: Интеграция
- [x] Frontend ↔ Backend API
- [x] Telegram SDK интеграция
- [x] Тестирование в Telegram

### Этап 6: Deploy
- [x] Frontend на Vercel
- [x] Backend на Railway
- [x] БД на Supabase (опционально)
- [x] Telegram бот для запуска Mini App

---

## 🛠️ ТЕХНОЛОГИЧЕСКИЕ РЕШЕНИЯ

### Состояние (State Management)
- React Context API для простоты
- Кэширование данных в localStorage

### Стили
- CSS Modules или Tailwind CSS
- Адаптивный дизайн для мобильных

### Error Handling
- Try-catch блоки в API запросах
- User-friendly ошибки в UI
- Логирование на backend

### Rate Limiting
- Кэширование матчей (обновление каждый час)
- Дебаунсинг при сохранении прогноза

---

## 📱 TELEGRAM MINI APP БОТ

```python
# telegram_bot.py
from telegram import Update, WebAppInfo, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler

async def start(update: Update, context):
    keyboard = [[KeyboardButton(
        text="⚽ Открыть приложение",
        web_app=WebAppInfo(url="https://your-app-url.com")
    )]]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    await update.message.reply_text(
        "Нажмите кнопку для открытия приложения:",
        reply_markup=reply_markup
    )

if __name__ == '__main__':
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.run_polling()
```

---

## 🌐 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ

### Backend (.env)
```
FOOTBALL_DATA_API_KEY=07cdd2788af245f39acf16042394eac2
DATABASE_URL=sqlite:///./predictor.db
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
CORS_ORIGINS=["http://localhost:5173", "https://your-frontend.com"]
```

### Frontend (.env)
```
VITE_API_URL=http://localhost:8000
VITE_APP_NAME=CM Predictor
```

---

## ✨ ОСОБЕННОСТИ И УЛУЧШЕНИЯ

### MVP (Минимально жизнеспособный продукт)
- ✅ Логин (простой)
- ✅ Список матчей
- ✅ Форма прогнозов
- ✅ Таблица лидеров
- ✅ Открывается в Telegram

### Future Features (После MVP)
- 🔜 Уведомления о начале матча
- 🔜 История прогнозов
- 🔜 Статистика пользователя
- 🔜 Чаты между пользователями
- 🔜 Приватные контесты (коды приглашения)
- 🔜 Различные системы подсчёта очков
- 🔜 Темная тема
- 🔜 Мультиязычность (EN, RU, ES и т.д.)
- 🔜 Интеграция с платежами
- 🔜 Рефлинки

---

## 🧪 ТЕСТИРОВАНИЕ

### Backend (pytest)
```python
def test_login():
    response = client.post("/api/auth/login", 
                          json={"username": "tim", "password": "pass"})
    assert response.status_code == 200

def test_save_prediction():
    response = client.post("/api/predictions",
                          json={"match_id": 1, "outcome": "1", "predicted_score": "2-1"},
                          headers={"Authorization": "Bearer token"})
    assert response.status_code == 200

def test_get_leaderboard():
    response = client.get("/api/leaderboard?competition_id=3")
    assert response.status_code == 200
    assert len(response.json()) > 0
```

### Frontend (Vitest + React Testing Library)
- Тесты компонентов
- Тесты API интеграции
- E2E тесты основного flow

---

## 📊 МОНИТОРИНГ И ЛОГИРОВАНИЕ

- Логи backend'a в файл
- Ошибки в Telegram (опционально)
- Метрики в Grafana (production)

---

## 🎯 УСПЕШНОЕ ЗАВЕРШЕНИЕ ПРОЕКТА

Приложение считается завершённым когда:
1. ✅ Можешь залогиниться
2. ✅ Видишь список матчей на день
3. ✅ Можешь добавить прогноз
4. ✅ Видишь таблицу лидеров
5. ✅ Можешь выбрать разный чемпионат
6. ✅ Открывается в Telegram без ошибок
7. ✅ Работает на мобильном (Telegram iOS/Android)

---

## 📝 ГОТОВО К РЕАЛИЗАЦИИ

Этот план содержит:
- ✅ Полную архитектуру
- ✅ Структуру проекта
- ✅ API endpoints
- ✅ Логику подсчёта очков
- ✅ Примеры кода
- ✅ Интеграцию с API
- ✅ Переменные окружения
- ✅ Future features

**Можешь передать этот файл в Claude Code для реализации!**
