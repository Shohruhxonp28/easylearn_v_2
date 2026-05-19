import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.accounts.models import User

def create_admin():
    username = os.environ.get('DJANGO_SUPERUSER_USERNAME', 'admin')
    password = os.environ.get('DJANGO_SUPERUSER_PASSWORD', 'admin123')
    email = os.environ.get('DJANGO_SUPERUSER_EMAIL', 'admin@example.com')

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f"✅ Superuser '{username}' muvaffaqiyatli yaratildi (Parol: {password}).")
    else:
        print(f"ℹ️ Superuser '{username}' allaqachon mavjud.")

if __name__ == '__main__':
    create_admin()
