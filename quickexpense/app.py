"""
QuickExpense - A simple multi-user expense tracker web application.

This app demonstrates the SaaS (Software as a Service) model:
- One single deployed instance of this application serves many different
  users at the same time, over the web, with no installation required.
- Each user logs in with their own account and only sees their own data.
- The app is accessed purely through a web browser via a public URL
  (once deployed to a PaaS platform such as Render).

Author: <YOUR NAME HERE>
"""

import os
from datetime import datetime, date

from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager, UserMixin, login_user, login_required,
    logout_user, current_user
)
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import func

# ---------------------------------------------------------------------------
# App configuration
# ---------------------------------------------------------------------------
app = Flask(__name__)

# SECRET_KEY is used by Flask to sign session cookies. In production this
# should come from an environment variable set on the PaaS platform, not be
# hard-coded. We fall back to a default only for local development.
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')

# Use DATABASE_URL if the platform provides one (e.g. Postgres on Render),
# otherwise fall back to a local SQLite file for development.
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL', 'sqlite:///quickexpense.db'
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Please log in to access this page.'

# Categories offered to every user
CATEGORIES = ['Food', 'Transport', 'Bills', 'Shopping', 'Health', 'Entertainment', 'Other']


# ---------------------------------------------------------------------------
# Database models
# ---------------------------------------------------------------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    expenses = db.relationship('Expense', backref='owner', lazy=True,
                                cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    note = db.Column(db.String(200))
    date = db.Column(db.Date, nullable=False, default=date.today)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------------------------------------------------------------------
# Routes: authentication
# ---------------------------------------------------------------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if not username or not password:
            flash('Username and password are required.', 'error')
            return redirect(url_for('register'))

        if User.query.filter_by(username=username).first():
            flash('That username is already taken.', 'error')
            return redirect(url_for('register'))

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Account created! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('dashboard'))

        flash('Invalid username or password.', 'error')
        return redirect(url_for('login'))

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


# ---------------------------------------------------------------------------
# Routes: expenses (require login — each user only ever sees their own data)
# ---------------------------------------------------------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    expenses = (Expense.query
                .filter_by(user_id=current_user.id)
                .order_by(Expense.date.desc())
                .all())

    total = sum(e.amount for e in expenses)

    # Total spent per category, for the summary chart
    category_totals = (
        db.session.query(Expense.category, func.sum(Expense.amount))
        .filter_by(user_id=current_user.id)
        .group_by(Expense.category)
        .all()
    )
    chart_labels = [c for c, _ in category_totals]
    chart_values = [round(v, 2) for _, v in category_totals]

    return render_template(
        'dashboard.html',
        expenses=expenses,
        total=total,
        chart_labels=chart_labels,
        chart_values=chart_values,
    )


@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_expense():
    if request.method == 'POST':
        try:
            amount = float(request.form.get('amount'))
        except (TypeError, ValueError):
            flash('Please enter a valid amount.', 'error')
            return redirect(url_for('add_expense'))

        category = request.form.get('category', 'Other')
        note = request.form.get('note', '').strip()
        date_str = request.form.get('date')
        expense_date = (datetime.strptime(date_str, '%Y-%m-%d').date()
                         if date_str else date.today())

        expense = Expense(
            amount=amount,
            category=category,
            note=note,
            date=expense_date,
            user_id=current_user.id,
        )
        db.session.add(expense)
        db.session.commit()

        flash('Expense added.', 'success')
        return redirect(url_for('dashboard'))

    return render_template('add_expense.html', categories=CATEGORIES,
                            today=date.today().isoformat())


@app.route('/delete/<int:expense_id>', methods=['POST'])
@login_required
def delete_expense(expense_id):
    expense = Expense.query.get_or_404(expense_id)

    # Security check: users may only delete their own expenses.
    if expense.user_id != current_user.id:
        flash('You are not allowed to do that.', 'error')
        return redirect(url_for('dashboard'))

    db.session.delete(expense)
    db.session.commit()
    flash('Expense deleted.', 'success')
    return redirect(url_for('dashboard'))


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
with app.app_context():
    db.create_all()

if __name__ == '__main__':
    # debug=True is fine for local development only; Render will instead
    # run this app through Gunicorn (see Procfile), not this block.
    app.run(debug=True)
