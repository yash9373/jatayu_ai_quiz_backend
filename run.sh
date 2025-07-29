#!/bin/bash

# Wait for PostgreSQL to be available
echo "Waiting for PostgreSQL to be available..."
while ! nc -z postgres 5432; do
  sleep 1
done
echo "PostgreSQL is available!"

# Create enum types first
echo "Creating enum types..."
python3 create_enums.py

# Run Alembic database migrations
echo "Running database migrations..."
alembic stamp head --purge || true
alembic upgrade head

# Start supervisor daemon with the configuration file
echo "Starting supervisor daemon..."
/usr/bin/supervisord -c /etc/supervisor/conf.d/supervisord.conf
