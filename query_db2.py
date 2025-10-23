import sqlite3

conn = sqlite3.connect('instance/jewel_system.db')
cursor = conn.cursor()

# Get table names
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print("Tables:", tables)

# If user table exists, get users
if ('user',) in tables:
    cursor.execute("SELECT email, password FROM user")
    users = cursor.fetchall()
    print("Users:", users)
else:
    print("No user table found.")

conn.close()
