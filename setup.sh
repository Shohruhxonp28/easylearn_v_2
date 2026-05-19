#!/bin/bash
# EduComp - One-Time Setup Script
set -e

echo "=== EduComp Setup ==="

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create migrations and apply them
python manage.py makemigrations accounts questions matches competitions
python manage.py migrate

# Seed demo data (superuser + questions)
python manage.py shell << 'PYEOF'
from accounts.models import Student
from questions.models import Category, Question, QuestionOption
from matches.models import BotProfile

# Superuser
if not Student.objects.filter(username='admin').exists():
    Student.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print("Superuser: admin / admin123")

# Bots
for level in ['easy', 'medium', 'hard']:
    BotProfile.objects.get_or_create(level=level, defaults={'name': f'{level.capitalize()} Bot'})

print("Setup complete! Run: python manage.py runserver")
PYEOF

echo ""
echo "=== DONE ==="
echo "Run the server: source venv/bin/activate && python manage.py runserver"
echo "Admin: http://127.0.0.1:8000/admin/  (admin / admin123)"
echo "Site:  http://127.0.0.1:8000/"
