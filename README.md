# ⚡ EduComp — Educational Competition Platform

A Django-based competitive learning platform with Duels and Arena modes.

## Features

- **⚔️ Duel**: 1v1 battles — find a real opponent or play against a bot instantly
- **🏟️ Arena**: Live 1-hour events — battle multiple opponents, win points, dominate the leaderboard
- **🤖 Bot System**: Easy / Medium / Hard bots, so you never wait for an opponent
- **❓ Questions**: Single-choice and multiple-choice questions, shown one at a time
- **👤 Accounts**: Full student profiles with rating system
- **🎭 Guest Mode**: Join arenas with just a name — no account needed
- **🏆 Leaderboards**: Live-updating arena leaderboards

## Tech Stack

- Python + Django (SQLite, Django Templates, Django Admin)
- Vanilla CSS (custom minimalist design)
- Vanilla JavaScript (no frameworks)

## Quick Start

```bash
# 1. Clone / unzip the project
cd educomp

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install django

# 4. Run migrations
python manage.py migrate

# 5. Create demo data (admin + questions + bots + arena)
python manage.py setup_demo

# 6. Start the server
python manage.py runserver

# 7. Open http://localhost:8000/
```

## Admin Panel

Go to `http://localhost:8000/admin/`

Login: `admin` / `admin123`

### Create Questions

1. Admin → Questions → Add Question
2. Choose category, write question body, select type (single/multiple choice)
3. Add options with the inline form (check "is correct" for correct answers)
4. Set status to **Published**

### Create Arenas

1. Admin → Arenas → Add Arena
2. Set title, category, start time, end time
3. Check **bot_enabled** so players always find an opponent
4. Save — players can now join at the start time

## Scoring

| Event | Points |
|-------|--------|
| Arena Win | +2 arena points |
| Arena Draw | +1 arena point |
| Arena Loss | 0 arena points |
| Duel Win | +10 rating |
| Duel Draw | +2 rating |
| Duel Loss | -5 rating |

## Project Structure

```
educomp/
├── config/          # Django settings, URLs
├── apps/
│   ├── accounts/    # User model, guest participants, auth views
│   ├── questions/   # Category, Question, QuestionOption
│   ├── duels/       # DuelQueue, duel lobby
│   ├── arenas/      # Arena, ArenaParticipant, ArenaScore
│   └── matches/     # Match, MatchQuestion, Submission, BotProfile
├── templates/       # All HTML templates
├── static/
│   ├── css/style.css
│   └── js/main.js
└── db.sqlite3
```

## Bot Difficulty

| Bot | Accuracy |
|-----|----------|
| Easy | 50-60% |
| Medium | 65-75% |
| Hard | 80-90% |

## Demo Accounts

After running `python manage.py setup_demo`:

| Username | Password | Role |
|----------|----------|------|
| admin | admin123 | Superuser |
| alice | demo123 | Student |
| bob | demo123 | Student |
| carol | demo123 | Student |
