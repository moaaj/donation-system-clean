# PostgreSQL Migration Guide for Django Donation App

This guide will help you migrate your Django app from SQLite to PostgreSQL for better scalability and performance.

## Prerequisites

- Windows 10/11
- Python 3.8+
- Git (optional but recommended)

## Step 1: Install PostgreSQL

### Download and Install PostgreSQL
1. Go to https://www.postgresql.org/download/windows/
2. Download the latest PostgreSQL version for Windows
3. Run the installer as Administrator
4. **Important:** Remember the password you set for the `postgres` user
5. Keep default port (5432)
6. Install all components (PostgreSQL Server, pgAdmin, Stack Builder)

### Verify Installation
1. Open Command Prompt
2. Navigate to PostgreSQL bin directory (usually `C:\Program Files\PostgreSQL\[version]\bin`)
3. Test connection:
   ```bash
   psql -U postgres -h localhost
   ```
4. Enter your password when prompted
5. You should see the PostgreSQL prompt: `postgres=#`
6. Type `\q` to exit

## Step 2: Set Up Database and User

### Option A: Using pgAdmin (GUI)
1. Open pgAdmin (installed with PostgreSQL)
2. Connect to your PostgreSQL server
3. Right-click on "Databases" → "Create" → "Database"
   - Name: `donation_db`
4. Right-click on "Login/Group Roles" → "Create" → "Login/Group Role"
   - Name: `donation_user`
   - Password: `your_secure_password_here`
   - Privileges tab: Check "Can login?"
5. Right-click on `donation_db` → "Properties" → "Security"
   - Add `donation_user` with all privileges

### Option B: Using SQL Script
1. Open Command Prompt
2. Navigate to PostgreSQL bin directory
3. Run the setup script:
   ```bash
   psql -U postgres -f "C:\path\to\your\project\setup_postgres.sql"
   ```
4. Update the password in the script before running

## Step 3: Install Python Dependencies

1. Navigate to your project directory:
   ```bash
   cd "C:\Users\dell\Desktop\Final freelance project\donation"
   ```

2. Activate your virtual environment (if using one):
   ```bash
   venv\Scripts\activate
   ```

3. Install the new dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Step 4: Configure Environment Variables

1. Create a `.env` file in your project root (copy from `env_example.txt`):
   ```bash
   copy env_example.txt .env
   ```

2. Edit the `.env` file with your actual values:
   ```env
   # Django Settings
   DJANGO_SECRET_KEY=
   DEBUG=False

   # Database Settings
   DB_NAME=donation_db
   DB_USER=donation_user
   DB_PASSWORD=your_secure_password_here
   DB_HOST=localhost
   DB_PORT=5432

   # Other settings...
   ```

3. Install python-dotenv to load environment variables:
   ```bash
   pip install python-dotenv
   ```

4. Update your `settings.py` to load environment variables:
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

## Step 5: Test Database Connection

1. Run the migration script:
   ```bash
   python migrate_to_postgres.py
   ```

2. Or test manually:
   ```bash
   python manage.py check
   ```

## Step 6: Migrate Data (if you have existing data)

### Option A: Fresh Start (Recommended for development)
1. Delete your old `db.sqlite3` file
2. Run migrations:
   ```bash
   python manage.py migrate
   ```
3. Create a new superuser:
   ```bash
   python manage.py createsuperuser
   ```

### Option B: Migrate Existing Data
1. Install `django-extensions`:
   ```bash
   pip install django-extensions
   ```

2. Add to `INSTALLED_APPS` in settings.py:
   ```python
   INSTALLED_APPS = [
       # ... existing apps
       'django_extensions',
   ]
   ```

3. Export data from SQLite:
   ```bash
   python manage.py dumpdata --exclude auth.permission --exclude contenttypes > data_backup.json
   ```

4. Run migrations on PostgreSQL:
   ```bash
   python manage.py migrate
   ```

5. Load data to PostgreSQL:
   ```bash
   python manage.py loaddata data_backup.json
   ```

## Step 7: Test Your Application

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Visit http://127.0.0.1:8000/admin/
3. Log in with your superuser credentials
4. Test creating, reading, updating, and deleting records

## Step 8: Production Deployment

### Update Settings for Production
1. Use the production settings:
   ```bash
   export DJANGO_SETTINGS_MODULE=donation.settings_production
   ```

2. Or create a `.env` file with production settings

### Install and Configure Redis (for caching)
1. Download Redis for Windows from: https://github.com/microsoftarchive/redis/releases
2. Install and start Redis service
3. Test Redis connection:
   ```bash
   redis-cli ping
   ```

### Install Gunicorn (for production server)
1. Install Gunicorn:
   ```bash
   pip install gunicorn
   ```

2. Test Gunicorn:
   ```bash
   gunicorn donation.wsgi:application --bind 0.0.0.0:8000
   ```

## Troubleshooting

### Common Issues

1. **Connection Error:**
   - Check if PostgreSQL service is running
   - Verify credentials in `.env` file
   - Check firewall settings

2. **Permission Denied:**
   - Ensure `donation_user` has proper privileges
   - Check database ownership

3. **Migration Errors:**
   - Delete migration files and recreate them
   - Check for conflicting migrations

4. **Import Error for psycopg2:**
   - Install Visual C++ Build Tools
   - Or use `psycopg2-binary` instead

### Useful Commands

```bash
# Check PostgreSQL status
sc query postgresql-x64-15

# Start PostgreSQL service
net start postgresql-x64-15

# Stop PostgreSQL service
net stop postgresql-x64-15

# Connect to database
psql -U donation_user -d donation_db -h localhost

# List databases
psql -U postgres -c "\l"

# Backup database
pg_dump -U donation_user -h localhost donation_db > backup.sql

# Restore database
psql -U donation_user -h localhost donation_db < backup.sql
```

## Performance Optimization

1. **Database Indexes:**
   - Add indexes to frequently queried fields
   - Use Django's `db_index=True` in models

2. **Connection Pooling:**
   - Already configured in settings
   - Consider using `django-db-connection-pool`

3. **Query Optimization:**
   - Use `select_related()` and `prefetch_related()`
   - Monitor slow queries with `django-debug-toolbar`

4. **Caching:**
   - Configure Redis caching
   - Use Django's cache framework

## Security Considerations

1. **Environment Variables:**
   - Never commit `.env` files to version control
   - Use strong, unique passwords

2. **Database Security:**
   - Limit database user privileges
   - Use SSL connections in production
   - Regular security updates

3. **Application Security:**
   - Keep Django and dependencies updated
   - Use HTTPS in production
   - Implement proper authentication

## Next Steps for Scalability

1. **Load Balancing:**
   - Set up multiple Django instances
   - Use Nginx as reverse proxy

2. **CDN:**
   - Serve static files via CDN
   - Use AWS S3 for media files

3. **Monitoring:**
   - Set up application monitoring
   - Database performance monitoring
   - Error tracking with Sentry

4. **Background Tasks:**
   - Configure Celery for async tasks
   - Email sending, report generation

---

## Support

If you encounter issues during migration:

1. Check the Django documentation: https://docs.djangoproject.com/
2. PostgreSQL documentation: https://www.postgresql.org/docs/
3. Common Django deployment issues: https://docs.djangoproject.com/en/stable/howto/deployment/

---

**Congratulations!** Your Django app is now running on PostgreSQL and ready for production deployment. 