#!/bin/sh
set -e

until pg_isready -h $POSTGRES_HOST -p $POSTGRES_PORT -U $POSTGRES_USERNAME
do
  sleep 2
done

echo "Running migrations..."
uv run alembic upgrade head

echo "Starting app..."
exec python -m app.bin.main