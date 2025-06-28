#!/bin/sh
# Wait for postgres to be ready (optional, but useful)
echo "Waiting for PostgreSQL..."
while ! nc -z postgres_db 5432; do
  sleep 1
done
echo "Postgres is up!"

# Run Alembic migrations

echo "📦 Running Alembic migrations..."
alembic upgrade head 

# Start FastAPI with uvicorn
echo "🚀 Starting FastAPI..."
uvicorn main:app --host 0.0.0.0 --port 3000