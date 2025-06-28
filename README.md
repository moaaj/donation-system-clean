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

## 🛠️ Setup Instructions

1. **Clone the repository:**
   ```sh
   git clone https://github.com/moaaj/donation-system-clean.git
   cd donation-system-clean
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
4. **Configure environment variables:**
   - Copy `donation/env_example.txt` to `.env` and fill in your secrets and keys
5. **Apply migrations:**
   ```sh
   python donation/manage.py migrate
   ```
6. **Create a superuser:**
   ```sh
   python donation/manage.py createsuperuser
   ```
7. **Run the development server:**
   ```sh
   python donation/manage.py runserver
   ```

## 📂 Project Structure

- `donation/` - Main Django project folder
- `myapp/`, `donation2/`, `waqaf/`, `accounts/` - Django apps
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS, images)
- `media/` - Uploaded files

## 📄 License

This project is licensed under the MIT License.

---

For more details, see the code and comments, or open an issue if you have questions! 