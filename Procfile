web: python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput && python3 init_admin.py && gunicorn config.wsgi:application --bind 0.0.0.0:$PORT
release: python3 manage.py migrate --noinput && python3 manage.py collectstatic --noinput && python3 init_admin.py
