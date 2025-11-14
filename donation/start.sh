#!/bin/bash

echo "🚀 Starting Django Donation App..."

# Wait a moment for any dependencies
sleep 2

echo "📁 Current directory contents:"
ls -la

echo "🗄️ Running database migrations..."
python manage.py migrate --noinput

echo "📦 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🌐 Starting Django development server..."
python manage.py runserver 0.0.0.0:${PORT:-8000}
