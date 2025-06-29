# Django Donation & School Fees Management System

A comprehensive Django web application for managing donations, school fees, and financial transactions with AI-powered analytics and a modern UI.

## 🚀 Features

- **Donation Management**: Track donations, generate receipts, and manage donation events
- **School Fees Management**: Student fee tracking, payment processing, and reporting
- **Waqaf Asset Management**: Islamic endowment asset tracking and contributions
- **AI-Powered Analytics**: Insights for donation predictions and fraud detection
- **QR Code Generation**: Automatic QR code generation for donation events
- **Multi-language Support**: Internationalization (Malay/English)
- **Multiple Payment Methods**: Stripe, FPX, SSLCommerz, PayPal, Bank Transfer
- **User Authentication**: Secure login, registration, and user management
- **PostgreSQL Database**: Robust database support for production deployments

## 🛠️ Setup Instructions

### Option 1: Local Development Setup

1. **Clone the repository:**
   ```sh
   git clone https://github.com/moaaj/donation-system-clean.git
   cd donation-system-clean/donation
   ```

2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```sh
   pip install -r requirements.txt
   ```

4. **Set up PostgreSQL:**
   ```sh
   # Install PostgreSQL (Ubuntu/Debian)
   sudo apt-get install postgresql postgresql-contrib
   
   # Or use the setup script
   python setup_postgres.py
   ```

5. **Configure environment variables:**
   ```sh
   cp env_example.txt .env
   # Edit .env with your database credentials and API keys
   ```

6. **Apply migrations:**
   ```sh
   python manage.py migrate
   ```

7. **Create a superuser:**
   ```sh
   python manage.py createsuperuser
   ```

8. **Run the development server:**
   ```sh
   python manage.py runserver
   ```

### Option 2: Docker Setup (Recommended)

1. **Clone the repository:**
   ```sh
   git clone https://github.com/moaaj/donation-system-clean.git
   cd donation-system-clean/donation
   ```

2. **Start with Docker Compose:**
   ```sh
   docker-compose up -d
   ```

3. **Run migrations:**
   ```sh
   docker-compose exec web python manage.py migrate
   ```

4. **Create superuser:**
   ```sh
   docker-compose exec web python manage.py createsuperuser
   ```

5. **Access the application:**
   - Web: http://localhost:8000
   - Admin: http://localhost:8000/admin

## 🗄️ Database Configuration

### PostgreSQL Setup

The application is configured to use PostgreSQL by default. You can configure it using environment variables:

```bash
DB_NAME=donation_db
DB_USER=donation_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432
```

### Database Migration

If you're migrating from SQLite to PostgreSQL:

```sh
# Export data from SQLite
python manage.py dumpdata > data_backup.json

# Apply migrations to PostgreSQL
python manage.py migrate

# Import data to PostgreSQL
python manage.py loaddata data_backup.json
```

## 🐳 Docker Deployment

### Production Docker Setup

1. **Build the production image:**
   ```sh
   docker build -t donation-system .
   ```

2. **Run with production settings:**
   ```sh
   docker run -d \
     -p 8000:8000 \
     -e DEBUG=False \
     -e DATABASE_URL=postgresql://user:pass@host:5432/db \
     donation-system
   ```

### Docker Compose for Production

```sh
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d
```

## 📂 Project Structure

```
donation/
├── donation/          # Main Django project
├── myapp/            # Core application
├── donation2/        # Donation management app
├── waqaf/           # Waqaf asset management
├── accounts/        # User authentication
├── templates/       # HTML templates
├── static/          # Static files
├── media/           # Uploaded files
├── requirements.txt # Python dependencies
├── docker-compose.yml # Docker configuration
├── Dockerfile       # Docker image definition
└── setup_postgres.py # Database setup script
```

## 🔧 Environment Variables

Create a `.env` file with the following variables:

```bash
# Django Settings
DJANGO_SECRET_KEY=your_secret_key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=donation_db
DB_USER=donation_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Payment Gateway Settings
STRIPE_PUBLIC_KEY=your_stripe_public_key
STRIPE_SECRET_KEY=your_stripe_secret_key
STRIPE_WEBHOOK_SECRET=your_webhook_secret

# Email Settings
EMAIL_HOST_USER=your_email
EMAIL_HOST_PASSWORD=your_email_password
```

## 🚀 Deployment

### Heroku Deployment

1. **Create Heroku app:**
   ```sh
   heroku create your-app-name
   ```

2. **Add PostgreSQL addon:**
   ```sh
   heroku addons:create heroku-postgresql:hobby-dev
   ```

3. **Deploy:**
   ```sh
   git push heroku main
   ```

### Railway Deployment

1. **Connect your GitHub repository**
2. **Add PostgreSQL service**
3. **Deploy automatically**

## 📄 License

This project is licensed under the MIT License.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

For more details, see the code and comments, or open an issue if you have questions!

## 📋 Prerequisites

- Python 3.8+
- pip (Python package installer)
- Git
- Virtual environment (recommended)

## 🚀 Installation

1. **Clone the repository**
   ```bash
   git clone <your-github-repo-url>
   cd donation
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   # On Windows
   venv\Scripts\activate
   # On macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env_example.txt .env
   # Edit .env file with your configuration
   ```

5. **Run database migrations**
   ```bash
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## 📁 Project Structure

```
donation/
├── donation/                 # Main Django project
│   ├── settings.py          # Django settings
│   ├── urls.py              # Main URL configuration
│   └── wsgi.py              # WSGI configuration
├── myapp/                   # School fees management app
│   ├── models.py            # Database models
│   ├── views.py             # View functions
│   ├── urls.py              # URL routing
│   └── templates/           # HTML templates
├── donation2/               # Donation management app
│   ├── models.py            # Donation models
│   ├── views.py             # Donation views
│   └── templates/           # Donation templates
├── waqaf/                   # Waqaf asset management app
│   ├── models.py            # Waqaf models
│   ├── views.py             # Waqaf views
│   └── templates/           # Waqaf templates
├── accounts/                # User authentication app
├── static/                  # Static files (CSS, JS, images)
├── media/                   # User-uploaded files
├── templates/               # Base templates
└── requirements.txt         # Python dependencies
```

## 🔧 Configuration

### Environment Variables
Create a `.env` file in the project root with the following variables:

```env
SECRET_KEY=
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
DATABASE_URL=sqlite:///db.sqlite3
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

### Database Configuration
- **Development**: SQLite (default)
- **Production**: PostgreSQL (recommended)

## 🎯 Usage

### Accessing the Application
- **Main URL**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin
- **Donation Portal**: http://localhost:8000/donation2/
- **School Fees**: http://localhost:8000/myapp/

### Key Features Usage

1. **Donation Management**
   - Create donation events
   - Generate QR codes for events
   - Process donations with multiple payment methods
   - Track donation analytics

2. **School Fees Management**
   - Add students and fee structures
   - Process fee payments
   - Generate payment receipts
   - View payment reports and analytics

3. **Waqaf Asset Management**
   - Manage waqaf assets
   - Track contributions
   - Generate contribution certificates

## 📊 AI Features

The system includes AI-powered features:
- **Donation Prediction**: Predict future donation amounts
- **Fraud Detection**: Identify potentially fraudulent transactions
- **Donor Insights**: Analyze donor behavior patterns
- **Fee Analytics**: Predict fee collection trends

## 🔒 Security Features

- User authentication and authorization
- CSRF protection
- SQL injection prevention
- XSS protection
- Secure payment processing
- Audit logging for all transactions

## 📈 Reporting & Analytics

- Real-time dashboard with key metrics
- Payment reports with date filtering
- Export functionality (CSV, PDF)
- Monthly and yearly summaries
- Category-wise analytics
- Student payment history

## 🚀 Deployment

### Production Deployment
1. Set `DEBUG=False` in settings
2. Configure production database
3. Set up static file serving
4. Configure web server (Nginx/Apache)
5. Set up SSL certificate
6. Configure email settings

### Docker Deployment (Optional)
```bash
docker build -t donation-system .
docker run -p 8000:8000 donation-system
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support and questions:
- Create an issue in the GitHub repository
- Contact the development team
- Check the documentation

## 🔄 Recent Updates

- Fixed CM Islam payment status from pending to completed
- Enhanced payment tracking system
- Improved AI analytics dashboard
- Added comprehensive reporting features

## 📞 Contact

- **Project Maintainer**: [Your Name]
- **Email**: [your-email@example.com]
- **GitHub**: [your-github-profile]

---

**Note**: This is a comprehensive school fees and donation management system designed for educational institutions and charitable organizations. 