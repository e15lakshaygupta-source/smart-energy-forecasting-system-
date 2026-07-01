import sqlite3

conn = sqlite3.connect("energy.db")

cursor = conn.cursor()

# Users Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT
)
""")

# Prediction History Table
cursor.execute("""
CREATE TABLE IF NOT EXISTS predictions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    hour INTEGER,
    consumption REAL,
    cost REAL,
    status TEXT,
    prediction_date TEXT
)
""")

conn.commit()
conn.close()

print("Database Created Successfully") 