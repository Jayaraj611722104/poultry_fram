# 🐔 PeruFarm — Poultry Farm Management System

A full-stack web application for managing poultry farm operations with chicken tracking, feed management, and advanced sales management.

---

## 🚀 Quick Start

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Run the application
```bash
python run.py
```

### 4. Open in browser
```
http://localhost:5000
```

### 5. Register first user
Go to `/register` to create your admin account.

---

## 🗂️ Project Structure

```
poultry_farm/
├── run.py                    # Entry point
├── requirements.txt          # Dependencies
├── .env.example              # Environment template
├── app/
│   ├── __init__.py           # App factory
│   ├── models.py             # Database models
│   ├── routes/
│   │   ├── auth.py           # Login, register, users
│   │   ├── farms.py          # Farm CRUD
│   │   ├── chickens.py       # Daily monitoring
│   │   ├── feed.py           # Feed stock & usage
│   │   ├── sales.py          # Sales management
│   │   └── reports.py        # Excel, PDF exports
│   ├── templates/
│   │   ├── base.html         # Main layout + sidebar
│   │   ├── auth/             # Login, register, users
│   │   ├── farms/            # Farm list & form
│   │   ├── chickens/         # Batch & daily entry
│   │   ├── feed/             # Feed management
│   │   ├── sales/            # Sales cards UI
│   │   └── reports/          # Report view
│   └── static/
│       ├── css/style.css     # Full stylesheet
│       └── js/main.js        # Language, sidebar, helpers
```

---

## 🌟 Features

### ✅ User Management
- Register / Login / Logout
- Reset password
- Delete users
- Role-based (admin / user)

### ✅ Farm Management
- Add, edit, delete farms
- Fields: Name, Village, District, Phone
- Search & filter

### ✅ Daily Chicken Monitoring (45–50 days)
- Create batch with initial count
- Daily deaths entry (grid UI)
- Auto-calculates remaining chickens
- Live mortality stats

### ✅ Feed Management
- Add feed stock (multiple entries with date)
- Daily usage tracking (50-day grid)
- Auto totals: Added / Used / Remaining
- Low stock warning (< 5 bags)
- Prevents usage exceeding stock

### ✅ Advanced Sales Management
- Card-based entry UI (add/delete cards)
- Step 1: Empty Box + Load details per card
- Step 2: Customer details
- Save as Draft → Continue later
- Complete → Locked
- Live summary panel (Net weight, avg, tonnage, amount)

### ✅ Reports
- On-screen report with full table
- Export to **Excel (.xlsx)** — styled with colors
- Export to **PDF** — professional layout
- Print-friendly view

### ✅ Multi-language
- English / Tamil toggle
- Persists via localStorage

---

## 🗄️ Database

Default: SQLite (zero config)

For MySQL, update `.env`:
```
DATABASE_URL=mysql+pymysql://user:pass@localhost/poultry_db
```
Also install: `pip install PyMySQL`

---

## 🧮 Sales Calculations

| Field | Formula |
|-------|---------|
| Total Chickens | Σ(empty_boxes × chickens_per_box) |
| Net Weight | Total Load Wt − Total Empty Wt |
| Average Weight | Net Weight ÷ Total Chickens |
| Tonnage | Net Weight ÷ 1000 |
| Total Amount | Net Weight × Price per kg |

---

## 📱 Mobile Support
Responsive sidebar collapses on mobile. All grids and cards adapt to small screens.

---

## 🔐 Demo Credentials
Register at `/register` to create:
- Username: `admin01`  
- Password: `admin@123`

---

## 🚀 Deployment (Render.com)

1. Push to GitHub
2. New Web Service → connect repo
3. Build: `pip install -r requirements.txt`
4. Start: `gunicorn run:app`
5. Add env vars in dashboard

Add `gunicorn` to requirements.txt for production.
