# QuickExpense

A simple multi-user expense tracker built with Python and Flask, demonstrating
the SaaS (Software as a Service) model. Users register an account, log in
through their browser, and track personal expenses by category. Each user's
data is private to their account.

## Features
- User registration and login (passwords hashed with Werkzeug)
- Add, view, and delete expenses
- Dashboard with total spend and a category breakdown chart
- Multi-user, multi-tenant data isolation (each user sees only their own data)

## Tech Stack
- **Python 3 / Flask** — web framework, routing, request handling
- **Flask-SQLAlchemy** — ORM for the database (SQLite locally, easily swapped
  for Postgres in production)
- **Flask-Login** — session-based authentication
- **Chart.js** — client-side chart rendering
- **Gunicorn** — production WSGI server used in deployment
- **Render** — PaaS platform used for deployment
- **GitHub** — source control and the trigger for automatic redeployment

## Running Locally

```bash
# 1. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the app
python app.py
```

Then open http://127.0.0.1:5000 in your browser. Register a new account and
start adding expenses.

## Deploying to Render (PaaS)

1. Push this project to a new GitHub repository.
2. Go to https://render.com and sign in (you can sign in with GitHub).
3. Click **New +** → **Web Service**.
4. Connect your GitHub account and select this repository.
5. Configure the service:
   - **Environment**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Add an environment variable `SECRET_KEY` with a random secret value.
7. Click **Create Web Service**. Render will build and deploy the app.
8. Once deployed, Render gives you a public URL, e.g.
   `https://quickexpense-yourname.onrender.com`
9. Open that URL in a browser — the live SaaS app is now accessible to
   anyone with the link.

## Demonstrating Automatic Redeployment

1. Make a small change locally (e.g. edit some text in `templates/index.html`).
2. Commit and push the change to GitHub:
   ```bash
   git add .
   git commit -m "Update landing page text"
   git push
   ```
3. Render automatically detects the new commit, rebuilds, and redeploys the
   app — refresh the public URL to see the change live.

## Notes on SQLite in Production

SQLite is used here for simplicity. On some PaaS platforms the filesystem is
ephemeral, so for a persistent production deployment you would normally
attach a managed Postgres database and set the `DATABASE_URL` environment
variable — the app already reads this variable if present.
