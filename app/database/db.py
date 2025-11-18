import sqlite3
import os
from datetime import datetime

os.makedirs("data", exist_ok=True)
conn = sqlite3.connect("data/database.db", check_same_thread=False)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 0,
    joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS withdraw_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    card TEXT,
    amount INTEGER,
    commission INTEGER,
    status TEXT DEFAULT '🕓 Kutilmoqda',
    date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_link TEXT,
    channel_username TEXT,
    reward INTEGER,
    description TEXT,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS user_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    task_id INTEGER,
    status TEXT DEFAULT 'pending',
    completed_date TIMESTAMP,
    FOREIGN KEY (task_id) REFERENCES tasks (id)
)
""")

conn.commit()

def add_user(user_id, username):
    cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
    conn.commit()

def get_user(user_id):
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    return cursor.fetchone()

def update_balance(user_id, amount):
    cursor.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()

def add_withdraw_request(user_id, card, amount, commission):
    cursor.execute("""
        INSERT INTO withdraw_requests (user_id, card, amount, commission)
        VALUES (?, ?, ?, ?)
    """, (user_id, card, amount, commission))
    conn.commit()
    return cursor.lastrowid

def get_withdraw_requests():
    cursor.execute("SELECT * FROM withdraw_requests WHERE status = '🕓 Kutilmoqda' ORDER BY date DESC")
    return cursor.fetchall()

def get_all_withdraw_requests():
    cursor.execute("SELECT * FROM withdraw_requests ORDER BY date DESC LIMIT 50")
    return cursor.fetchall()

def update_withdraw_status(req_id, new_status):
    cursor.execute("UPDATE withdraw_requests SET status = ? WHERE id = ?", (new_status, req_id))
    conn.commit()

def add_task(channel_link, channel_username, reward, description):
    cursor.execute("""
        INSERT INTO tasks (channel_link, channel_username, reward, description)
        VALUES (?, ?, ?, ?)
    """, (channel_link, channel_username, reward, description))
    conn.commit()
    return cursor.lastrowid

def get_active_tasks():
    cursor.execute("SELECT * FROM tasks WHERE is_active = 1 ORDER BY created_date DESC")
    return cursor.fetchall()

def get_task(task_id):
    cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
    return cursor.fetchone()

def get_user_completed_tasks(user_id):
    cursor.execute("""
        SELECT t.* FROM tasks t
        JOIN user_tasks ut ON t.id = ut.task_id
        WHERE ut.user_id = ? AND ut.status = 'completed'
    """, (user_id,))
    return cursor.fetchall()

def add_user_task(user_id, task_id):
    cursor.execute("""
        INSERT OR IGNORE INTO user_tasks (user_id, task_id)
        VALUES (?, ?)
    """, (user_id, task_id))
    conn.commit()

def complete_user_task(user_id, task_id):
    cursor.execute("""
        UPDATE user_tasks 
        SET status = 'completed', completed_date = CURRENT_TIMESTAMP
        WHERE user_id = ? AND task_id = ?
    """, (user_id, task_id))
    conn.commit()

def check_user_task_completion(user_id, task_id):
    cursor.execute("""
        SELECT * FROM user_tasks 
        WHERE user_id = ? AND task_id = ? AND status = 'completed'
    """, (user_id, task_id))
    return cursor.fetchone() is not None

def get_user_pending_tasks(user_id):
    cursor.execute("""
        SELECT t.* FROM tasks t
        LEFT JOIN user_tasks ut ON t.id = ut.task_id AND ut.user_id = ?
        WHERE ut.id IS NULL AND t.is_active = 1
    """, (user_id,))
    return cursor.fetchall()

def get_user_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    return result[0] if result else 0

# Admin statistikasi uchun funksiyalar
def get_total_users():
    cursor.execute("SELECT COUNT(*) FROM users")
    return cursor.fetchone()[0]

def get_pending_withdraw_count():
    cursor.execute("SELECT COUNT(*) FROM withdraw_requests WHERE status = '🕓 Kutilmoqda'")
    return cursor.fetchone()[0]

def get_active_tasks_count():
    cursor.execute("SELECT COUNT(*) FROM tasks WHERE is_active = 1")
    return cursor.fetchone()[0]

def get_total_balance():
    cursor.execute("SELECT SUM(balance) FROM users")
    result = cursor.fetchone()[0]
    return result if result else 0

def get_today_users():
    cursor.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_date) = DATE('now')")
    return cursor.fetchone()[0]

def get_weekly_withdraw_total():
    cursor.execute("""
        SELECT SUM(amount) FROM withdraw_requests 
        WHERE status = '✅ To\'landi' AND date >= DATE('now', '-7 days')
    """)
    result = cursor.fetchone()[0]
    return result if result else 0

# Admin topshiriqlarini boshqarish
def get_all_tasks():
    cursor.execute("SELECT * FROM tasks ORDER BY created_date DESC")
    return cursor.fetchall()

def update_task_status(task_id, is_active):
    cursor.execute("UPDATE tasks SET is_active = ? WHERE id = ?", (is_active, task_id))
    conn.commit()

def delete_task(task_id):
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
    conn.commit()