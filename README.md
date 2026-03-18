# ProfitPulse - AI-Powered Investment Platform 🚀

[![Django](https://img.shields.io/badge/Django-5.1.2-green.svg)](https://www.djangoproject.com/)
[![Python](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![Deployment](https://img.shields.io/badge/Deployed%20on-Render-brightgreen)](https://codecrafters2025.onrender.com)

## 🌟 Overview

**ProfitPulse** is a comprehensive AI-powered investment platform that combines real-time stock market analytics, machine learning-based predictions, automated risk management, and gamified paper trading. Built with Django and integrated with cutting-edge AI technologies, it provides users with intelligent investment insights, portfolio tracking, and risk assessment tools.

Live Demo: [https://codecrafters2025.onrender.com](https://codecrafters2025.onrender.com)

---

## ✨ Core Features

### 📊 Investment Management

- **Real-Time Stock Data** - Live stock quotes, market data, and price updates via Finnhub API
- **Portfolio Tracking** - Comprehensive dashboard to monitor investments, profits, and losses
- **Stock Analysis** - Detailed stock information with company profiles and historical data
- **Transaction History** - Complete record of all buy/sell transactions with timestamps

### 🤖 AI & Machine Learning

- **ML Stock Price Predictor** - 7-day price prediction using Scikit-learn Linear Regression
- **Google Gemini AI Integration** - AI-powered chat assistant for investment advice and queries
- **Predictive Analytics** - Interactive price prediction charts using Plotly
- **Historical Data Analysis** - Analyzes stock patterns using Yahoo Finance data

### 🎮 Paper Trading (Simulation Mode)

- **Virtual Wallet System** - Practice trading with virtual money without real risk
- **Simulated Stock Trading** - Buy/sell stocks in a risk-free environment
- **Performance Statistics** - Track your simulated portfolio performance
- **Test Scenarios** - Pre-configured market scenarios for learning

### 🛡️ Risk Management System

- **AI-Powered Risk Analysis** - Automated risk assessment using Gemini AI
- **Stock Alerts** - Real-time notifications for price movements and volatility
- **Exit Strategies** - Intelligent stop-loss and take-profit recommendations
- **Volatility Detection** - Monitors market volatility and sends alerts
- **Email & SMS Notifications** - Multi-channel alert system (Email + Twilio SMS)

### 🔐 Authentication & Security

- **Google OAuth Integration** - Secure login with Google accounts via django-allauth
- **Traditional Authentication** - Email/username and password login
- **User Profiles** - Customizable profiles with photo uploads
- **Session Management** - Secure session handling and CSRF protection

### 💼 Insurance Management

- **Insurance Policies** - View and manage insurance portfolios
- **Policy Comparison** - Compare different insurance options
- **Integration** - Seamlessly integrated with investment portfolio

### 📞 Video Call System

- **KYC Verification** - Video call functionality for identity verification
- **Virtual Meeting Rooms** - Integrated video conferencing for consultations
- **Real-time Communication** - Connect with advisors and support

### 📈 Market Analytics

- **Market Stocks Browser** - Explore and search through US stock market
- **Stock Suggestions** - AI-powered recommendations based on portfolio
- **Market Insights** - Real-time market trends and analytics
- **Custom Filters** - Filter stocks by sector, market cap, and performance

---

## 🛠️ Tech Stack

### Backend

- **Django 5.1.2** - High-level Python web framework
- **Python 3.12** - Core programming language
- **Gunicorn 21.2.0** - Production WSGI server
- **WhiteNoise 6.6.0** - Static file serving
- **dj-database-url 2.1.0** - Database configuration

### Machine Learning & Data Science

- **Scikit-learn 1.5.1** - Machine learning algorithms for stock prediction
- **NumPy 1.26.4** - Numerical computing and array operations
- **Pandas 2.2.0** - Data manipulation and analysis
- **Plotly 5.13.1** - Interactive data visualization and charts
- **yfinance 0.2.18** - Yahoo Finance API for historical stock data

### AI & APIs

- **Google Generative AI** - Gemini AI for intelligent chat and analysis
- **Finnhub API** - Real-time stock market data and company information
- **Twilio** - SMS notifications and alerts
- **SMTP (Gmail)** - Email notifications

### Frontend

- **HTML5** - Semantic markup
- **CSS3** - Styling and responsive design
- **JavaScript** - Interactive UI elements
- **Bootstrap** - Responsive framework (via templates)

### Authentication & Social

- **django-allauth** - Social authentication (Google OAuth)
- **Google OAuth 2.0** - Secure Google login integration

### Database

- **SQLite** - Development database

### Image Processing

- **Pillow 10.4.0** - Image handling for profile photos

### Utilities

- **python-dotenv 1.0.0** - Environment variable management
- **PyPDF2** - PDF processing capabilities

### Deployment

- **Render** - Cloud platform for deployment
- **Git/GitHub** - Version control and CI/CD

---

## 📁 Project Structure

```
CodeCrafters2025/
├── investing/                  # Main Django project directory
│   ├── investing/             # Project settings
│   │   ├── settings.py       # Django configuration with environment variables
│   │   ├── urls.py           # Main URL routing
│   │   └── wsgi.py           # WSGI configuration
│   │
│   ├── User/                  # User management & authentication
│   │   ├── models.py         # UserProfile, StockTransaction, StockPreference
│   │   ├── views.py          # Auth, portfolio, stock trading, Gemini AI chat
│   │   ├── urls.py           # User-related routes
│   │   └── templates/        # User interface templates
│   │
│   ├── simulation/            # Paper trading system
│   │   ├── models.py         # UserWallet, Stock, StockHolding, Transactions
│   │   ├── views.py          # Virtual trading, wallet management
│   │   └── management/       # Test scenario generation commands
│   │
│   ├── risksystem/            # Risk management module
│   │   ├── models.py         # RiskProfile, StockAlert, ExitStrategy
│   │   ├── views.py          # Risk analysis, alerts, Gemini AI integration
│   │   ├── forms.py          # Risk profile configuration
│   │   └── templatetags/     # Custom template tags
│   │
│   ├── insurance/             # Insurance management
│   │   ├── models.py         # Insurance policies
│   │   ├── views.py          # Insurance views and comparisons
│   │   └── templates/        # Insurance interface
│   │
│   ├── videocall/             # Video conferencing
│   │   ├── models.py         # Video call rooms
│   │   └── views.py          # Video call functionality
│   │
│   ├── requirements.txt       # Python dependencies
│   ├── manage.py             # Django management script
│   └── .env                  # Environment variables (not in git)
│
├── .gitignore                # Git ignore rules
├── ENV_SETUP.md              # Environment setup documentation
├── RENDER_DEPLOYMENT_GUIDE.md # Deployment instructions
└── README.md                 # This file
```

---

## 🚀 Installation & Setup

### Prerequisites

- Python 3.12 or higher
- pip (Python package manager)
- Git
- Virtual environment (recommended)

### 1. Clone the Repository

```bash
git clone https://github.com/rohanbagel/CodeCrafters2025.git
cd CodeCrafters2025/investing
```

### 2. Create Virtual Environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Setup Environment Variables

Create a `.env` file in the `investing/` directory:

```env
# Django Settings
SECRET_KEY=your-django-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# API Keys
GEMINI_API_KEY=your-gemini-api-key
FINNHUB_API_KEY=your-finnhub-api-key

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=ProfitPulse <your-email@gmail.com>

# Twilio (SMS Notifications)
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=your-twilio-number
TWILIO_TRIAL_MODE=True
```

**Get API Keys:**

- **Gemini AI**: [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Finnhub**: [Finnhub Dashboard](https://finnhub.io/dashboard)
- **Gmail App Password**: [Google Account Settings](https://myaccount.google.com/apppasswords)
- **Twilio**: [Twilio Console](https://www.twilio.com/console)

### 5. Run Database Migrations

```bash
python manage.py migrate
```

### 6. Create Superuser (Admin)

```bash
python manage.py createsuperuser
```

### 7. Collect Static Files

```bash
python manage.py collectstatic --no-input
```

### 8. Run Development Server

```bash
python manage.py runserver
```

Visit: `http://127.0.0.1:8000/`

---

## 🌐 Deployment (Render)

### Quick Deploy to Render

1. **Push to GitHub**

   ```bash
   git add .
   git commit -m "Initial commit"
   git push origin main
   ```
2. **Create Web Service on Render**

   - Go to [Render Dashboard](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Configure:
     - **Root Directory**: `investing`
     - **Build Command**: `pip install -r requirements.txt && python manage.py collectstatic --no-input && python manage.py migrate`
     - **Start Command**: `gunicorn investing.wsgi:application`
3. **Set Environment Variables**

   - Add all variables from your `.env` file
   - Update `ALLOWED_HOSTS` with your Render URL
   - Update `CSRF_TRUSTED_ORIGINS` with `https://your-app.onrender.com`
   - Set `PYTHON_VERSION=3.12.0`
4. **Deploy!**

   - Render will automatically build and deploy
   - Visit your app at: `https://your-app-name.onrender.com`

---

## 📖 Usage

### User Features

1. **Sign Up/Login** - Create account or login with Google
2. **Explore Stocks** - Browse real-time stock market data
3. **Portfolio Management** - Track your investments and performance
4. **AI Chat** - Ask investment questions to Gemini AI assistant
5. **Paper Trading** - Practice trading with virtual money
6. **Stock Predictions** - View 7-day ML price predictions
7. **Set Alerts** - Configure price and volatility alerts
8. **Risk Analysis** - Get AI-powered risk assessments

### Admin Features

1. Access admin panel: `/admin/`
2. Manage users, stocks, and transactions
3. Configure site settings and social auth
4. Monitor system alerts and logs

---

## 🔑 Key Integrations

### Finnhub API

- Real-time stock quotes
- Company profiles and financials
- Stock symbols and market data
- Historical price data

### Google Gemini AI

- Investment advice chatbot
- Risk analysis and recommendations
- Portfolio insights
- Natural language queries

### Twilio

- SMS alerts for price movements
- Risk notifications
- Transaction confirmations

### Yahoo Finance (yfinance)

- Historical stock data
- Price predictions training data
- Market trends analysis

---

## 📊 Machine Learning Model

The stock price prediction feature uses:

- **Algorithm**: Linear Regression (Scikit-learn)
- **Input Features**: Historical stock prices (Close, High, Low, Volume)
- **Output**: 7-day future price predictions
- **Visualization**: Interactive Plotly charts
- **Data Source**: Yahoo Finance API

---

## 🔒 Security Features

- ✅ Environment variable management with python-dotenv
- ✅ CSRF protection
- ✅ Secure password hashing
- ✅ Google OAuth 2.0 authentication
- ✅ Session-based authentication
- ✅ SQL injection prevention (Django ORM)
- ✅ HTTPS in production (Render)

---

**⭐ Star this repo if you find it helpful!**

🔥 **Built with Django, AI, and passion for smarter investments!** 🚀
