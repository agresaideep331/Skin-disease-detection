import sqlite3
import os
from werkzeug.security import generate_password_hash

DB_FILE = 'skin_disease.db'

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            age INTEGER NOT NULL,
            gender TEXT NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            is_admin BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            image_name TEXT NOT NULL,
            disease TEXT NOT NULL,
            confidence REAL NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    
    conn.commit()
    conn.close()

def user_exists(username=None, email=None):
    conn = get_connection()
    cursor = conn.cursor()
    
    if username:
        cursor.execute('SELECT id FROM users WHERE username = ?', (username,))
        if cursor.fetchone():
            conn.close()
            return True
    
    if email:
        cursor.execute('SELECT id FROM users WHERE email = ?', (email,))
        if cursor.fetchone():
            conn.close()
            return True
    
    conn.close()
    return False

def create_user(email, age, gender, username, password, is_admin=False):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        hashed_password = generate_password_hash(password)
        cursor.execute('''
            INSERT INTO users (email, age, gender, username, password, is_admin)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (email, age, gender, username, hashed_password, int(is_admin)))
        
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, email, age, gender, username FROM users WHERE id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def add_history(user_id, image_name, disease, confidence):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO history (user_id, image_name, disease, confidence)
            VALUES (?, ?, ?, ?)
        ''', (user_id, image_name, disease, confidence))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user_history(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT id, image_name, disease, confidence, date FROM history WHERE user_id = ? ORDER BY date DESC', (user_id,))
    history = cursor.fetchall()
    conn.close()
    return history

def delete_history_record(record_id, user_id):
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('DELETE FROM history WHERE id = ? AND user_id = ?', (record_id, user_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_prediction_count(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as count FROM history WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0
