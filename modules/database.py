import os
import sqlite3

from conf import ADMINS


cur_dir = os.path.dirname(os.path.abspath(__file__))
path_db = os.path.join(os.path.split(cur_dir)[0], 'data', 'database', 'bot.db')

if os.path.exists(path_db):
    print('Database exist')
else:
    print('Database do not exist')
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()

        cursor.execute("""CREATE TABLE tests
            (filename text, testname text, createdate text,
            begindate text, enddate text, key text)""")

        cursor.execute("CREATE TABLE users (login text, status text)")
    
        cursor.execute("""CREATE TABLE passwords
            (type text, filename text, password text, createdate text)""")

        cursor.execute("""CREATE TABLE answers
            (login text, filename text, date text,
            question_id integer, question text, answer text)""")

        cursor.execute("""CREATE TABLE tests_status
            (filename text, userlogin text, date text, status text, info text)""")

        for admin in ADMINS:
            cursor.execute("INSERT INTO users VALUES (?, 'admin')", [admin])
            conn.commit()

        print(f'Create database: {path_db}')
        
with sqlite3.connect(path_db) as conn:
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    print(f'Users: {cursor.fetchall()}')

