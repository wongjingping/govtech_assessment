#!/bin/bash
set -e

echo "Starting API server..."
echo "Current directory: $(pwd)"

# Wait for the source code to be mounted
echo "Waiting for source code volumes to be mounted..."
while [ ! -f /app/src/app.py ]; do
    echo "Source code not yet mounted, waiting..."
    sleep 1
done

echo "Contents of /app:"
ls -la /app
echo "Contents of /app/src:"
ls -la /app/src
echo "Python path: $PYTHONPATH"

echo "Starting Uvicorn server..."
exec uvicorn main:app --host 0.0.0.0 --port 8000 --reload 