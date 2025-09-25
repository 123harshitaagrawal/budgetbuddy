BudgetBuddy
===========

Smart expense tracker with user login, bill splitting, analytics, and charts.

Quick start (2 terminals)
1) Terminal 1 (backend):
```
cd backend
./venv/Scripts/activate  # or: .\\backend\\venv\\Scripts\\Activate.ps1 in PowerShell
python app.py
```
2) Terminal 2 (frontend):
```
cd frontend
npm install
npm run start
```

Tech stack
- Frontend: React, react-router, chart.js (react-chartjs-2)
- Backend: Flask (Python), MySQL, Flask-CORS, Werkzeug (password hashing)
- Auth: Cookie-based server sessions

Features
- Login/logout with secure server sessions
- Add expenses, split across users; each user sees their own share
- Expense list with delete and split labels (e.g., “You”, other usernames)
- Daily trends line chart and monthly spending bar chart
- Basic next-month spending prediction (linear regression demo)

Screenshots
- Add images under `docs/screenshots/` and reference them here, for example:
  - `docs/screenshots/login.png`
  - `docs/screenshots/expenses.png`
  - `docs/screenshots/charts.png`

Local development
Prerequisites
- Python 3.13
- Node.js 18+
- MySQL 8+

1) Backend
```
cd backend
# Install deps (if using a venv, activate it first)
pip install -r requirements.txt  # if present; otherwise ensure Flask, mysql-connector-python, pandas, scikit-learn, numpy, flask-cors are installed

# Create database tables
python schema.sql  # or run the SQL inside MySQL Workbench/CLI

# Seed demo data (users and sample expenses)
python seed.py

# Run server (Windows PowerShell example)
$env:DEV_RESET_SESSIONS='1'  # dev only; rotates SECRET_KEY on each restart
python app.py
```
Backend API base: `http://localhost:5000/api`

2) Frontend
```
cd frontend
npm install
npm start
```
Frontend: `http://localhost:3000`

Environment
- Backend (Flask)
  - `SECRET_KEY`: Secret key for sessions (set in prod)
  - `DEV_RESET_SESSIONS=1`: Dev-only; rotates secret and clears sessions on restart
- Frontend (React)
  - API base is configured in `frontend/src/utils/api.js` (`http://localhost:5000/api` by default)

Database
- Apply `backend/schema.sql` or run `backend/seed.py` for demo data
- Tables: `users`, `expenses` (with `user_share`, `split_user_ids`, and `created_at`)

Security notes
- Passwords are verified using Werkzeug hashing. A plaintext fallback exists for legacy rows; plan to remove when all passwords are migrated.
- CORS allows `http://localhost:3000` in development.

Project structure
```
backend/
  app.py             # Flask API
  schema.sql         # DB schema
  seed.py            # Demo data
frontend/
  src/
    components/      # React components (forms, lists, charts)
    utils/api.js     # Axios client
```

Deployment (outline)
- Backend: Render/Fly.io/Heroku or a VPS (set `SECRET_KEY`, database URL, CORS)
- Frontend: Netlify/Vercel (set API base URL to deployed backend)

License
MIT (or your preferred license)

