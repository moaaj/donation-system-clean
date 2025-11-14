# 🔄 Project Restoration Guide

## After Your Laptop is Repaired

### Option 1: Restore from Git (Recommended)

1. **Clone the repository:**
   ```bash
   git clone <your-repository-url>
   cd "Final freelance project"
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database:**
   ```bash
   python manage.py migrate
   ```

4. **Create a superuser (if needed):**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server:**
   ```bash
   python manage.py runserver
   ```

### Option 2: Restore from Backup Archive

1. **Extract the backup:**
   - Right-click on the backup ZIP file
   - Select "Extract All..."
   - Choose a destination folder

2. **Navigate to the extracted folder:**
   ```bash
   cd "Final freelance project"
   ```

3. **Follow steps 2-5 from Option 1**

### Option 3: Restore from External Drive/Cloud

1. **Copy the backup file to your computer**
2. **Follow Option 2 steps**

## 🔧 Environment Setup

### Required Software:
- Python 3.8+
- pip
- Git
- PostgreSQL (if using PostgreSQL)
- Virtual environment (recommended)

### Virtual Environment Setup:
```bash
python -m venv venv
venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

## 📋 Important Files to Check:

1. **Settings files:**
   - `donation/settings.py`
   - `donation/settings_production.py`
   - `config/settings.py`

2. **Database configuration:**
   - Check database settings in settings files
   - Ensure database credentials are correct

3. **Environment variables:**
   - Create `.env` file if needed
   - Add any required API keys or secrets

## 🚀 Quick Start Commands:

```bash
# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

## 📞 If You Need Help:

1. Check the `README.md` file for project-specific instructions
2. Review the `requirements.txt` for all dependencies
3. Check the `Dockerfile` and `docker-compose.yml` if using Docker

## 🔒 Security Notes:

- Update any API keys or secrets after restoration
- Change database passwords if they were stored locally
- Review and update any hardcoded credentials

---

**Last backup created:** [Date will be shown when backup script runs]
**Backup file location:** [Will be shown when backup script runs]

