import os
import mysql.connector
from urllib.parse import urlparse
from werkzeug.security import generate_password_hash


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
        config = {
            'user': 'root',
            'password': 'admin123',
            'host': '127.0.0.1',
            'database': 'budgetbuddy_db',
            'raise_on_warnings': True
        }
    return mysql.connector.connect(**config)


def seed():
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NULL,
            password_hash VARCHAR(255) NULL
        )
        """
    )

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount DECIMAL(10,2) NOT NULL,
            category VARCHAR(255) NOT NULL,
            date DATE NOT NULL,
            split_user_ids TEXT NULL,
            user_share DECIMAL(10,2) NOT NULL,
            user_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """
    )

    users = [
        ("user1", generate_password_hash("pass1")),
        ("user2", generate_password_hash("pass2")),
    ]

    for username, pwd_hash in users:
        cur.execute(
            "INSERT INTO users (username, password_hash) VALUES (%s, %s) ON DUPLICATE KEY UPDATE password_hash=VALUES(password_hash)",
            (username, pwd_hash),
        )

    conn.commit()
    cur.close()
    conn.close()


if __name__ == "__main__":
    seed()


