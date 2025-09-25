import os
from flask import Flask, request, jsonify, session
from werkzeug.security import check_password_hash
from flask_cors import CORS
import mysql.connector
from datetime import datetime
import pandas as pd
from sklearn.linear_model import LinearRegression
import numpy as np
from urllib.parse import urlparse

app = Flask(__name__)
if os.environ.get('DEV_RESET_SESSIONS') == '1':
    import secrets
    app.secret_key = secrets.token_hex(32)
    print("[Startup] DEV_RESET_SESSIONS=1 -> using random SECRET_KEY; sessions will be cleared on restart.")
else:
    app.secret_key = os.environ.get('SECRET_KEY', 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6')  # Use env var in production
    print("[Startup] Using static SECRET_KEY; sessions persist across restarts.")
CORS(app, resources={r"/api/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)

def get_db_connection():
    if 'DATABASE_URL' in os.environ:
        url = urlparse(os.environ['DATABASE_URL'])
        config = {
            'user': url.username,
            'password': url.password,
            'host': url.hostname,
            'database': url.path[1:],
            'port': url.port
        }
    else:
        # Update these credentials based on your local MySQL setup
        config = {
            'user': 'root',  # Replace with your MySQL username
            'password': 'admin123',  # Replace with your MySQL password
            'host': '127.0.0.1',  # Use 127.0.0.1 instead of localhost if needed
            'database': 'budgetbuddy_db',
            'raise_on_warnings': True
        }
    try:
        return mysql.connector.connect(**config)
    except mysql.connector.Error as err:
        print(f"Database connection failed: {err}")
        raise

# 1. Login
@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    username = data['username']
    password = data['password']

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    # Fetch by username and verify password hash in Python to support hashed passwords
    cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    if user:
        # Support both hashed and legacy plaintext passwords during migration
        stored_password = user.get('password') or user.get('password_hash')
        is_valid = False
        if stored_password is not None:
            try:
                is_valid = check_password_hash(stored_password, password)
            except Exception:
                is_valid = False
        # Fallback for legacy rows where password is stored in plaintext column
        if not is_valid and user.get('password') == password:
            is_valid = True

        if is_valid:
            session['user_id'] = user['id']
            print(f"Logged in user_id: {session['user_id']}")
            return jsonify({'message': 'Login successful', 'user_id': user['id']})
    return jsonify({'message': 'Invalid credentials'}), 401

# 2. Logout
@app.route('/api/logout', methods=['POST'])
def logout():
    session.pop('user_id', None)
    return jsonify({'message': 'Logged out'})

# 3. Add Expense (with split for all users)
@app.route('/api/add_expense', methods=['POST'])
def add_expense():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    data = request.json
    amount = float(data['amount'])
    category = data['category']
    date = data.get('date', datetime.now().strftime('%Y-%m-%d'))
    split_user_ids = data.get('split_user_ids', '').split(',')  # Split into list
    split_user_ids = [sid.strip() for sid in split_user_ids if sid.strip()]
    user_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Insert expense for each involved user
    total_people = len(split_user_ids) + 1  # Including the current user
    user_share = amount / total_people

    # Insert for current user (payer). Store other participants in split_user_ids
    cursor.execute("""
        INSERT INTO expenses (amount, category, date, split_user_ids, user_share, user_id)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (amount, category, date, ','.join(split_user_ids), user_share, user_id))

    # Insert for each split user. For their row, store payer and other participants except themselves
    for split_id in split_user_ids:
        if split_id:
            others_for_this_user = [str(user_id)] + [sid for sid in split_user_ids if sid != split_id]
            cursor.execute("""
                INSERT INTO expenses (amount, category, date, split_user_ids, user_share, user_id)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (amount, category, date, ','.join(others_for_this_user), user_share, split_id))

    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Expense added for all users!'}), 201

# 4. Current user info
@app.route('/api/me', methods=['GET'])
def me():
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'user_id': None}), 200
    return jsonify({'user_id': user_id}), 200

@app.route('/api/expenses', methods=['GET'])
def get_expenses():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    print(f"Fetching expenses for user_id: {session['user_id']}")  # Debug
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM expenses WHERE user_id = %s ORDER BY date DESC", (session['user_id'],))
    expenses = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(expenses)

# 5. Delete Expense (only for the user's own record)
@app.route('/api/delete_expense/<int:id>', methods=['DELETE'])
def delete_expense(id):
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses WHERE id = %s AND user_id = %s", (id, session['user_id']))
    conn.commit()
    cursor.close()
    conn.close()
    return jsonify({'message': 'Expense deleted!'})

# 6. Predict Monthly Spending
@app.route('/api/predict', methods=['GET'])
def predict():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT date, user_share FROM expenses WHERE user_id = %s", (session['user_id'],))
    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if len(data) < 5:
        return jsonify({'prediction': 'Need more data'})

    df = pd.DataFrame(data)
    df['date'] = pd.to_datetime(df['date'])
    df['days'] = (df['date'] - df['date'].min()).dt.days

    X = np.array(df['days']).reshape(-1, 1)
    y = df['user_share']

    model = LinearRegression()
    model.fit(X, y)

    next_days = np.array([df['days'].max() + 30]).reshape(-1, 1)
    prediction = model.predict(next_days)[0] * 30
    return jsonify({'prediction': round(prediction, 2)})

# 7. Get Surprise Savings
@app.route('/api/savings', methods=['GET'])
def savings():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT category, AVG(user_share) as avg_share
        FROM expenses WHERE user_id = %s AND date >= CURDATE() - INTERVAL 7 DAY
        GROUP BY category
    """, (session['user_id'],))
    avgs = cursor.fetchall()
    cursor.close()
    conn.close()

    alerts = [f"Saved on {a['category']}: Avg {round(a['avg_share'], 2)} INR" for a in avgs if a['avg_share'] < 100]
    return jsonify({'alerts': alerts})

# 8. Get Users (excluding current user)
@app.route('/api/users', methods=['GET'])
def get_users():
    if 'user_id' not in session:
        return jsonify({'message': 'Unauthorized'}), 401
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT id, username FROM users WHERE id != %s", (session['user_id'],))
    users = cursor.fetchall()
    cursor.close()
    conn.close()
    return jsonify(users)

if __name__ == '__main__':
    app.run(debug=True)