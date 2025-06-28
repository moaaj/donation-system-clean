# Django Donation & School Fees Management System

A comprehensive Django web application for managing donations, school fees, and financial transactions with AI-powered analytics and modern UI.

## 🚀 Features

### Core Functionality
- **Donation Management**: Complete donation tracking with multiple payment methods
- **School Fees Management**: Student fee tracking, payment processing, and reporting
- **Waqaf Asset Management**: Islamic endowment asset tracking and contributions
- **AI-Powered Analytics**: Machine learning insights for donation predictions and fraud detection
- **QR Code Generation**: Automatic QR code generation for donation events
- **Multi-language Support**: Internationalization support (Malay/English)

### Payment Features
- Multiple payment methods (SSLCommerz, Stripe, PayPal, Bank Transfer, etc.)
- Payment receipt generation and email notifications
- Fee waiver and discount management
- Overdue payment tracking and reminders
- Real-time payment status updates

### Administrative Features
- Comprehensive dashboard with analytics
- Student management system
- Fee structure and category management
- Payment reports and exports
- User authentication and authorization
- Audit logging for all transactions

## 🛠️ Technology Stack

- **Backend**: Django 5.1.7
- **Database**: SQLite (development) / PostgreSQL (production)
- **Frontend**: Bootstrap 5, jQuery, Chart.js
- **AI/ML**: Python machine learning libraries
- **Payment**: Multiple payment gateway integrations
- **Email**: SMTP with Gmail integration

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