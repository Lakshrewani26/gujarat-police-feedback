# Gujarat Police Citizen Feedback System

A modern, professional full-stack web application built for the Gujarat Police Department to collect, manage, and analyze citizen feedback through QR codes at police stations.

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | HTML5, CSS3, JavaScript, Bootstrap 5, Chart.js |
| Backend | Python Flask |
| Database | MySQL (via SQLAlchemy + PyMySQL) |
| Auth | Flask-Login + Werkzeug password hashing |
| QR Codes | qrcode (Python) |
| Reports | CSV export via Python csv module |

---

## Folder Structure

```
gujarat-police-feedback/
│
├── static/
│   ├── css/main.css          # All styles
│   ├── js/main.js            # Dashboard JS
│   ├── js/feedback.js        # Feedback form JS
│   ├── qr_codes/             # Generated QR images (auto-created)
│   └── uploads/              # Citizen image uploads (auto-created)
│
├── templates/
│   ├── base.html             # Base template
│   ├── index.html            # Public landing page
│   ├── admin/
│   │   ├── base_dashboard.html   # Dashboard layout with sidebar
│   │   ├── dashboard.html        # Analytics dashboard
│   │   ├── feedbacks.html        # Feedback management table
│   │   ├── stations.html         # Police station management
│   │   └── officers.html         # Officer management
│   ├── auth/
│   │   └── login.html            # Secure login page
│   └── citizen/
│       └── feedback_form.html    # 3-step feedback form
│
├── app.py                    # Main Flask application
├── models.py                 # SQLAlchemy database models
├── config.py                 # Configuration
├── database.sql              # MySQL schema
├── requirements.txt          # Python dependencies
└── README.md
```

---

## Installation & Setup

### 1. Clone / Extract the project

```bash
cd gujarat-police-feedback
```

### 2. Create a Python virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Set up MySQL Database

```sql
-- In MySQL client:
CREATE DATABASE gujarat_police_feedback CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 5. Configure database connection

Edit `config.py` or create a `.env` file:

```env
SECRET_KEY=your-very-secure-random-key-here
DATABASE_URL=mysql+pymysql://YOUR_MYSQL_USER:YOUR_MYSQL_PASSWORD@localhost/gujarat_police_feedback
BASE_URL=http://localhost:5000
```

### 6. Initialize the database with demo data

```bash
flask init-db
```

This will:
- Create all database tables
- Add 5 sample police stations
- Generate QR codes for each station
- Create the admin account

### 7. Run the application

```bash
flask run
# or
python app.py
```

Open http://localhost:5000 in your browser.

---

## Default Login

| Role | Email | Password |
|---|---|---|
| Admin | admin@gujaratpolice.gov.in | Admin@1234 |

⚠️ **Change the admin password after first login in production!**

---

## Key Features

### 🏠 Public Landing Page
- Hero section with Gujarat Police branding
- Animated statistics counters
- How It Works section
- Station listing with direct feedback links
- Emergency contact numbers
- Mobile-responsive design

### 📱 QR Code System
- Each police station has a unique QR code
- QR codes link to `/feedback/<station_code>`
- QR codes downloadable as PNG
- Auto-generated on station creation

### 📝 3-Step Feedback Form
- **Step 1**: Citizen information (all optional for anonymity)
- **Step 2**: 5-category star ratings + overall rating with emoji
- **Step 3**: Written feedback + complaint + image upload
- Auto-generates unique acknowledgment ID (e.g., GPF-A1B2C3D4)
- AI-based sentiment analysis (keyword + rating based)
- Mobile-first responsive design

### 🔐 Secure Authentication
- Role-based access (Admin / Officer)
- Password hashing with Werkzeug scrypt
- Session management
- Audit logging for all admin actions

### 📊 Analytics Dashboard
- KPI cards: Total feedback, avg rating, complaints, sentiment
- Weekly trend line chart
- Sentiment doughnut chart
- Rating distribution bar chart
- Station performance comparison
- Recent feedback table

### 📋 Feedback Management
- Search, filter by station/rating/sentiment/date
- View complaint details
- Mark complaints as resolved with notes
- Flag inappropriate feedback
- Delete feedback (admin only)
- CSV export

### 🏢 Station Management
- Add/view police stations
- Auto-generate and download QR codes
- Station statistics (feedback count, avg rating, officer count)
- QR code preview

### 👮 Officer Management
- Add officers with roles and station assignments
- Rank selection
- View login history

---

## API Endpoints

| Method | Route | Description |
|---|---|---|
| GET | `/` | Public landing page |
| GET/POST | `/feedback/<station_code>` | Citizen feedback form |
| GET/POST | `/login` | Officer login |
| GET | `/logout` | Logout |
| GET | `/dashboard` | Analytics dashboard |
| GET | `/feedbacks` | Feedback management |
| POST | `/feedback/resolve/<id>` | Resolve complaint |
| POST | `/feedback/flag/<id>` | Flag feedback |
| POST | `/feedback/delete/<id>` | Delete feedback (admin) |
| GET | `/stations` | Station management (admin) |
| POST | `/stations/add` | Add station (admin) |
| GET | `/stations/qr/<id>` | Download QR code |
| GET | `/officers` | Officer management (admin) |
| POST | `/officers/add` | Add officer (admin) |
| GET | `/export/csv` | Export feedback as CSV |
| GET | `/api/stats` | JSON stats for dashboard |
| POST | `/api/notifications/mark-read` | Mark notifications read |

---

## Security Features

- ✅ SQL injection prevention (SQLAlchemy ORM)
- ✅ Password hashing (Werkzeug scrypt)
- ✅ Input sanitization (bleach library)
- ✅ Session management (Flask-Login)
- ✅ Role-based access control
- ✅ Audit logging
- ✅ File upload validation (type + size limits)
- ✅ CSRF token support (Flask-WTF ready)

---

## Customization

### Add more police stations
Use the Admin dashboard → Police Stations → Add Station, or run:
```python
flask shell
>>> from models import db, PoliceStation
>>> # add your station
```

### Change theme colors
Edit CSS variables in `static/css/main.css`:
```css
:root {
  --navy: #1a237e;       /* Primary blue */
  --saffron: #FF9800;    /* Accent orange */
}
```

### Disable anonymous feedback
In `templates/citizen/feedback_form.html`, make name/mobile required fields.

---

## Production Deployment

1. Set `FLASK_ENV=production` in environment
2. Use Gunicorn: `gunicorn -w 4 -b 0.0.0.0:5000 app:app`
3. Set up Nginx as reverse proxy
4. Enable HTTPS (SSL certificate)
5. Set `SESSION_COOKIE_SECURE = True` in config
6. Use a strong `SECRET_KEY`
7. Set up MySQL with proper user permissions

---

## License

Built for Gujarat Police Digital India Initiative. For hackathon and educational use.
