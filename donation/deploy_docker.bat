@echo off
echo 🐳 Starting Docker Deployment for Django Donation App...

REM Stop any existing containers
echo 📦 Stopping existing containers...
docker-compose down

REM Build and start services
echo 🔨 Building and starting services...
docker-compose up --build -d

REM Wait for database to be ready
echo ⏳ Waiting for database to be ready...
timeout /t 10 /nobreak

REM Run migrations
echo 🗄️ Running database migrations...
docker-compose exec web python manage.py migrate

REM Show running containers
echo 📊 Docker containers status:
docker-compose ps

echo ✅ Deployment complete!
echo 🌐 Your Django app is running at: http://localhost:8000
echo 🔧 Admin panel: http://localhost:8000/admin
echo 📋 To stop: docker-compose down
echo 📋 To view logs: docker-compose logs -f web

pause
