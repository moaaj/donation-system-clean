#!/bin/bash

echo "🐳 Starting Docker Deployment for Django Donation App..."

# Stop any existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Build and start services
echo "🔨 Building and starting services..."
docker-compose up --build -d

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations
echo "🗄️ Running database migrations..."
docker-compose exec web python manage.py migrate

# Create superuser (optional)
echo "👤 Creating superuser (optional)..."
docker-compose exec web python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
    print('Superuser created: admin/admin123')
else:
    print('Superuser already exists')
"

# Show running containers
echo "📊 Docker containers status:"
docker-compose ps

echo "✅ Deployment complete!"
echo "🌐 Your Django app is running at: http://localhost:8000"
echo "🔧 Admin panel: http://localhost:8000/admin (admin/admin123)"
echo "📋 To stop: docker-compose down"
echo "📋 To view logs: docker-compose logs -f web"
