FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=donation.settings

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    postgresql-client \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire project
COPY . .

# Make scripts executable
RUN chmod +x manage.py start.sh || echo "Scripts not found or not executable"

# List files for debugging
RUN echo "Files in /app:" && ls -la

# Create staticfiles directory
RUN mkdir -p staticfiles media

# Expose port
EXPOSE 8000

# Use startup script
CMD ["./start.sh"]
