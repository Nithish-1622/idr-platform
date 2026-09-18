#!/bin/bash
set -e

echo "Waiting for PostgreSQL database to start..."
python -c "
import socket, time, os
host = os.environ.get('POSTGRES_HOST', 'db')
port = int(os.environ.get('POSTGRES_PORT', 5432))
for i in range(30):
    try:
        with socket.create_connection((host, port), timeout=2):
            print('PostgreSQL is up and accepting connections.')
            break
    except Exception as e:
        print(f'Waiting for DB connection ({host}:{port})...')
        time.sleep(2)
"

echo "Applying Django Database Migrations..."
python manage.py makemigrations --noinput || true
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput || true

exec "$@"
