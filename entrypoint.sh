#!/bin/sh
# Wait for postgres to be ready (optional, but useful)
until pg_isready -h postgres_db -p 5432; do
  echo "Waiting for postgres..."
  sleep 2
done

# Run Alembic migrations

# rm app/migrations/versions/*.py
alembic revision --autogenerate -m "Init"
alembic upgrade head 

# Start FastAPI with uvicorn
uvicorn main:app --host 0.0.0.0 --port 3000