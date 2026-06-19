#!/bin/sh
set -e

mkdir -p /data

echo "Starting Küchenhelfer Addon..."
export PYTHONPATH="/app"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop auto --workers 1
