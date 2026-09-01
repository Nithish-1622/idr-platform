#!/bin/bash
set -e

echo "Waiting for PostgreSQL database to start..."
while ! nc -z ${POSTGRES_HOST:-db} ${POSTGRES_PORT:-5432}; do
  sleep 1
done
echo "PostgreSQL is up and accepting connections."

echo "Applying Django Database Migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

exec "$@"
