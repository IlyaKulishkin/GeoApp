#!/bin/sh

while ! pg_isready -h db -U geouser -d geopoints; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

if [ "$1" = "web" ]; then
    python manage.py migrate --noinput
    python create_superuser.py
    exec python manage.py runserver 0.0.0.0:8000
fi

exec "$@"