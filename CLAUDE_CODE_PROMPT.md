# 💻 ПРОМПТ ДЛЯ CLAUDE CODE

Скопируй и вставь этот текст в Claude Code (https://claude.ai/code):

---

## ПОЛНЫЙ ПРОМПТ:

Реализуй полный Telegram Mini App для прогнозов на матчи по следующему плану:

### ТРЕБОВАНИЯ:

1. **Backend (FastAPI на Python)**
   - Аутентификация (login/register) с паролем
   - Получение матчей из football-data.org API (ключ: 07cdd2788af245f39acf16042394eac2)
   - Система прогнозов (сохранение исхода и точного счёта)
   - Подсчёт очков: 1 очко за правильный исход + 3 очка за точный счёт
   - Таблица лидеров
   - Выбор чемпионата (не только ЧМ, но и другие лиги)
   - SQLite база данных

2. **Frontend (React + Vite)**
   - Страница логина (username/password)
   - Главная страница с выбором чемпионата и даты
   - Список матчей на день
   - На каждом матче кнопки для выбора исхода (1/X/2) и поле для точного счёта
   - Таблица лидеров с очками
   - Адаптивный дизайн для мобильных (Telegram)
   - Интеграция с Telegram SDK (@telegram-apps/sdk)

3. **API Endpoints:**
   - POST /api/auth/login - логин
   - POST /api/auth/register - регистрация
   - GET /api/matches - матчи на день (с параметрами: competition_id, date)
   - POST /api/predictions - сохранить прогноз
   - GET /api/leaderboard - таблица лидеров
   - GET /api/competitions - список чемпионатов

4. **Интеграция с football-data.org:**
   ```
   API ключ: 07cdd2788af245f39acf16042394eac2
   Endpoint: https://api.football-data.org/v4/matches
   Пример запроса:
   GET https://api.football-data.org/v4/matches?competitions=3&dateFrom=2026-06-11&dateTo=2026-06-11
   Header: X-Auth-Token: 07cdd2788af245f39acf16042394eac2
   ```

5. **Важные требования:**
   - Должна быть возможность добавлять прогнозы только для SCHEDULED матчей (не начавшихся)
   - Результаты должны показываться для FINISHED матчей
   - Выбор чемпионата должен быть легко масштабируемым
   - Приложение должно открываться в Telegram без ошибок
   - Красивый интерфейс с использованием CSS или Tailwind

6. **Структура проекта:**
   ```
   backend/
     - main.py
     - requirements.txt
     - app/database.py
     - app/models.py
     - app/routers/auth.py
     - app/routers/matches.py
     - app/routers/predictions.py
     - app/routers/leaderboard.py
     - app/routers/competitions.py
     - app/services/football_api.py
     - app/services/scoring.py
   
   frontend/
     - src/App.jsx
     - src/pages/LoginPage.jsx
     - src/pages/HomePage.jsx
     - src/pages/LeaderboardPage.jsx
     - src/components/MatchCard.jsx
     - src/components/LeaderboardTable.jsx
     - src/components/CompetitionSelector.jsx
     - src/services/api.js
     - src/hooks/useAuth.js
   ```

7. **Тестовые данные:**
   - Некоторые чемпионаты для тестирования:
     - 3 = FIFA World Cup 2026
     - 2014 = Premier League
     - 2016 = La Liga
     - 2017 = Bundesliga
     - 2018 = Serie A
     - 2019 = Ligue 1

### ПЕРВООЧЕРЕДНО:

Начни с:
1. Backend структура + SQLite
2. Роутеры аутентификации
3. Интеграция с football-data.org
4. Frontend базовая структура
5. Страница логина
6. Список матчей с формой прогноза
7. Таблица лидеров

### ОФОРМЛЕНИЕ:

- Используй профессиональный дизайн
- Адаптивный для мобильных
- Цвета: синий (#3b82f6), зелёный (#10b981), красный (#ef4444)
- Шрифты: система по умолчанию

### ЗАПУСК:

Backend:
```bash
cd backend
pip install -r requirements.txt
python main.py
```

Frontend:
```bash
cd frontend
npm install
npm run dev
```

---

Реализуй этот проект полностью и готовым к использованию.

---

## КАК ИСПОЛЬЗОВАТЬ:

1. Открой https://claude.ai/code в браузере
2. Скопируй весь текст выше (от "Реализуй полный Telegram Mini App..." до конца)
3. Вставь в Claude Code
4. Claude создаст проект
5. Скачай все файлы
6. Запусти по инструкции выше

---

## ДОПОЛНИТЕЛЬНО:

После того как Claude создаст базовый проект, ты можешь просить:

- "Добавь темную тему"
- "Добавь уведомления о начале матча"
- "Добавь истории прогнозов"
- "Добавь statistiky пользователя"
- "Добавь возможность приватных контестов (коды приглашения)"
- "Измени систему подсчёта очков на X"
- "Добавь новый чемпионат для теста"

---

**Готово! Просто скопируй и вставь в Claude Code!** 🚀
