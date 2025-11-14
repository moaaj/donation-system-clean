#!/usr/bin/env bash
# exit on error
set -o errexit

echo "🔄 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "🔄 Setting up Django..."
export DJANGO_SETTINGS_MODULE=donation.settings_production

echo "🔄 Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "🔄 Running database migrations..."
python manage.py migrate --noinput

echo "✅ Build completed successfully!"
