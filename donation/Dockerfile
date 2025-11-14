FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y postgresql-client gcc libpq-dev && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Simple start - NO collectstatic, NO migrations during build
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
