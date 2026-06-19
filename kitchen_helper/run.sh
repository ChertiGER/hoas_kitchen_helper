#!/bin/sh
set -e

# Ensure DB dir exists
mkdir -p /data

echo "Starting Küchenhelfer FastAPI..."
export PYTHONPATH="/app/kitchen_helper"

exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --loop auto --workers 1
