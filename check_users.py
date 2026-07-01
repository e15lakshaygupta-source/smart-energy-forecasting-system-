import sqlite3

conn = sqlite3.connect("energy.db")
cursor = conn.cursor()

cursor.execute("SELECT * FROM users")

users = cursor.fetchall()

print("\nRegistered Users:\n")

for user in users:
    print(user)

conn.close() 