#!/bin/sh

while ! pg_isready -h db -U geouser -d geopoints; do
  echo "Waiting for PostgreSQL..."
  sleep 1
done

python manage.py migrate

python create_superuser.py

python manage.py runserver 0.0.0.0:8000