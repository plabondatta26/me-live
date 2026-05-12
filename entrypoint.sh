#!/bin/bash
set -e

# Wait for Postgres to be ready
#if [ "$DATABASE_HOST" ]; then
#  echo "Waiting for Postgres at $DATABASE_HOST..."
#  until pg_isready -h "$DATABASE_HOST" -p "$DATABASE_PORT" -U "$DATABASE_USER"; do
#    sleep 2
#    echo "Waiting..."
#  done
#fi

# Run migrations and collect static only for web container (assuming the command starts with 'gunicorn')
if [[ "$*" == *"gunicorn"* ]]; then
  echo "Running migrations..."
  python manage.py migrate --noinput

  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

echo "Executing command: $@"
exec "$@"
