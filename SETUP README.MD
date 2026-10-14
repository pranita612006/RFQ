# 🚀 FlowNexis (RFQ Tool) — Complete Setup Guide

> **FlowNexis** is a Django-based RFQ (Request for Quotation) management tool built on the AdminLTE dashboard template. This guide covers everything you need to get the project running from scratch.

---

## 📋 Table of Contents

1. [Prerequisites](#-prerequisites)
2. [Clone the Repository](#-clone-the-repository)
3. [Set Up Python Virtual Environment](#-set-up-python-virtual-environment)
4. [Install Dependencies](#-install-dependencies)
5. [Environment Configuration (.env)](#-environment-configuration-env)
6. [Database Setup](#-database-setup)
7. [Run the Development Server](#-run-the-development-server)
8. [Create a Superuser (Admin)](#-create-a-superuser-admin)
9. [Frontend Assets (Vite — Optional)](#-frontend-assets-vite--optional)
10. [Docker Deployment (Optional)](#-docker-deployment-optional)
11. [Project Structure Overview](#-project-structure-overview)
12. [Troubleshooting](#-troubleshooting)

---

## 🔧 Prerequisites

Make sure the following software is installed on your machine before proceeding:

| Software    | Minimum Version | Download Link                                           |
|-------------|----------------|---------------------------------------------------------|
| **Python**  | 3.9+           | [python.org/downloads](https://www.python.org/downloads/) |
| **pip**     | 21+            | Comes with Python                                        |
| **Git**     | 2.30+          | [git-scm.com](https://git-scm.com/)                     |
| **Node.js** | 16+ (optional) | [nodejs.org](https://nodejs.org/) — only for Vite/frontend assets |
| **Docker**  | 20+ (optional) | [docker.com](https://www.docker.com/) — only for Docker deployment |

### Verify Installations

```bash
python --version
pip --version
git --version
node --version       # optional
docker --version     # optional
```

---

## 📥 Clone the Repository

```bash
git clone <your-repo-url>
cd N-RFQ
```

> If you already have the project folder, simply `cd` into it.

---

## 🐍 Set Up Python Virtual Environment

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)

```cmd
python -m venv venv
venv\Scripts\activate.bat
```

### macOS / Linux

```bash
python3 -m venv venv
source venv/bin/activate
```

> ✅ You should see `(venv)` at the beginning of your terminal prompt once activated.

---

## 📦 Install Dependencies

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### Key Dependencies Installed

| Package                | Purpose                           |
|------------------------|-----------------------------------|
| `django==4.2.9`        | Core web framework                |
| `python-dotenv`        | Loads `.env` environment variables |
| `djangorestframework`  | REST API support                  |
| `django-jazzmin`       | Admin UI theme                    |
| `django-admin-adminlte`| AdminLTE dashboard integration    |
| `pandas`               | Data processing & Excel handling  |
| `anthropic`            | AI-powered features (Claude API)  |
| `whitenoise`           | Static file serving in production |
| `gunicorn`             | Production WSGI server            |
| `django-dbbackup`      | Database backup & restore         |

---

## ⚙️ Environment Configuration (.env)

Create a `.env` file in the project root (or copy from the sample):

```bash
copy env.sample .env
```

Then edit `.env` with your settings:

```env
# ─── General ───────────────────────────────────────
DEBUG=True
SECRET_KEY=your-secret-key-here

# ─── Database (leave ALL commented out to use SQLite) ───
# DB_ENGINE=postgresql
# DB_HOST=localhost
# DB_PORT=5432
# DB_USERNAME=postgres
# DB_NAME=rfqtool
# DB_PASS=your_password

# ─── Email (for password reset & notifications) ───
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-char-app-password
DEFAULT_FROM_EMAIL=your-email@gmail.com
```

### Database Options

| Option       | Configuration                                  |
|-------------|------------------------------------------------|
| **SQLite**  | Default — no DB config needed in `.env`         |
| **PostgreSQL** | Set `DB_ENGINE=postgresql` and fill DB credentials |
| **MySQL**   | Set `DB_ENGINE=mysql` and fill DB credentials (install `mysqlclient`) |

> **Note:** For SQLite (default), simply leave all `DB_*` variables commented out or remove them.

### Gmail App Password (for Email Features)

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**
3. Go to **App passwords** → Generate a new one
4. Use the 16-character password as `EMAIL_HOST_PASSWORD`

---

## 🗄️ Database Setup

### Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Collect Static Files

```bash
python manage.py collectstatic --no-input
```

---

## ▶️ Run the Development Server

```bash
python manage.py runserver
```

The app will be available at: **http://127.0.0.1:8000/**

> To run on a different port:
> ```bash
> python manage.py runserver 0.0.0.0:8080
> ```

---

## 👤 Create a Superuser (Admin)

```bash
python manage.py createsuperuser
```

You will be prompted to enter:
- **Username**
- **Email address**
- **Password** (enter twice)

Access the Django Admin panel at: **http://127.0.0.1:8000/admin/**

---

## 🎨 Frontend Assets (Vite — Optional)

If you need to modify SCSS/CSS frontend assets:

```bash
npm install
npm run dev       # Watch mode (development)
npm run build     # Production build
```

> This step is **optional** for normal usage. It's only needed if you're modifying the frontend styling.

---

## 🐳 Docker Deployment (Optional)

### Using Docker Compose

```bash
docker-compose up --build
```

The app will be accessible at: **http://localhost:5085/** (via Nginx reverse proxy)

### Using Dockerfile Only

```bash
docker build -t flownexis-rfq .
docker run -p 8000:8000 flownexis-rfq
```

---

## 🗂️ Project Structure Overview

```
N-RFQ/
├── config/                    # Django project settings
│   ├── settings.py            #   Main settings (DB, apps, middleware)
│   ├── urls.py                #   Root URL configuration
│   ├── middleware.py           #   Custom middleware (Active Customer)
│   ├── context_processors.py  #   Template context processors
│   └── wsgi.py / asgi.py      #   Server entry points
│
├── apps/                      # All Django applications
│   ├── pages/                 #   Dashboard pages (v1, v2, v3)
│   ├── customer_creation/     #   Customer selection & management
│   ├── item_creation/         #   Item/part creation & ECN requests
│   ├── opportunities/         #   Opportunity creation & tracking
│   ├── feasibility_form/      #   Feasibility assessment forms
│   ├── BOM/                   #   Bill of Materials
│   ├── BOP/                   #   Bill of Process
│   ├── BOC/                   #   Bill of Components
│   ├── CostingBCCal/          #   Costing & BC Calculations
│   ├── BlanketSales/          #   Blanket Sales Orders
│   ├── ApproveRec/            #   Record approval workflow
│   ├── Report/                #   Reports & analytics
│   ├── todo/                  #   To-Do list
│   ├── user_management/       #   User roles & permissions
│   ├── upload_data/           #   Data upload (Excel/CSV)
│   ├── erp_data/              #   ERP data integration
│   ├── charts/                #   Charts (ApexCharts)
│   ├── dyn_dt/                #   Dynamic DataTables
│   └── dyn_api/               #   Dynamic REST APIs
│
├── templates/                 # HTML templates
│   ├── layouts/               #   Base layout templates
│   ├── includes/              #   Sidebar, menu, footer partials
│   ├── accounts/              #   Login, register, password reset
│   └── pages/                 #   Dashboard page templates
│
├── static/                    # Static assets (CSS, JS, images)
├── manage.py                  # Django management script
├── requirements.txt           # Python dependencies
├── package.json               # Node.js dependencies (Vite)
├── .env                       # Environment variables (DO NOT commit)
├── Dockerfile                 # Docker container configuration
├── docker-compose.yml         # Docker Compose orchestration
├── gunicorn-cfg.py            # Gunicorn production server config
└── db.sqlite3                 # SQLite database file (auto-created)
```

---

## 🔄 Quick Start (All-in-One Commands)

### Windows (PowerShell)

```powershell
# 1. Create & activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
copy env.sample .env
# Edit .env with your settings

# 4. Setup database
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input

# 5. Create admin user
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

### macOS / Linux

```bash
# 1. Create & activate virtual environment
python3 -m venv venv
source venv/bin/activate

# 2. Install dependencies
python -m pip install --upgrade pip
pip install -r requirements.txt

# 3. Configure environment
cp env.sample .env
# Edit .env with your settings

# 4. Setup database
python manage.py makemigrations
python manage.py migrate
python manage.py collectstatic --no-input

# 5. Create admin user
python manage.py createsuperuser

# 6. Run the server
python manage.py runserver
```

---

## 🛠️ Troubleshooting

### Common Issues & Fixes

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: No module named 'django'` | Activate your virtual environment: `.\venv\Scripts\Activate.ps1` |
| `OperationalError: no such table` | Run `python manage.py makemigrations` then `python manage.py migrate` |
| `CSRF verification failed` | Add your domain to `CSRF_TRUSTED_ORIGINS` in `config/settings.py` |
| `Static files not loading` | Run `python manage.py collectstatic --no-input` |
| `Port already in use` | Use a different port: `python manage.py runserver 8080` |
| `Email sending fails` | Make sure you're using a Gmail **App Password** (not your regular password) |
| `pip install fails on Windows` | Try: `python -m pip install --upgrade pip setuptools wheel` first |
| `PowerShell script execution disabled` | Run: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned` |

### Resetting the Database

```bash
# Delete the SQLite database and re-create
del db.sqlite3          # Windows
rm db.sqlite3           # macOS/Linux

python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
```

---

## 📝 Git Workflow (for Team Development)

```bash
# Start of the day — pull latest changes
git pull

# Check what's modified
git status

# Stage all changes
git add .

# Commit with a message
git commit -m "your commit message here"

# Push to remote
git push
```

---

## 📌 Important Notes

- **Never commit the `.env` file** — it contains sensitive credentials
- **Always activate `venv`** before running any Python/Django commands
- The default database is **SQLite** (`db.sqlite3`) — suitable for development
- For production, switch to **PostgreSQL** or **MySQL** via `.env` configuration
- The app uses **session-based authentication** — sessions expire when the browser closes

---

## 🆘 Need Help?

- Check the [Django Documentation](https://docs.djangoproject.com/en/4.2/)
- Check the [AdminLTE Documentation](https://adminlte.io/docs/3.2/)
- Review the project's `CHANGELOG.md` for version history