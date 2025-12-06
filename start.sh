#!/bin/bash
# Start script for Render deployment

# Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# Start Gunicorn
exec gunicorn --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120 app:app

