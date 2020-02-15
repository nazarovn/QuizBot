import yaml
import os
import sqlite3
from datetime import datetime
import random
import string
from io import BytesIO

from checker_correct_test import Checker


# #####     PROCESS NEW FILE      ######

def random_string(string_length):
    """Generate a random string of fixed length """
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for _ in range(string_length))


def write_info(path_test: str, path_db: str, author=None):
    """Write test info to table 'tests'

    :param path_test: path to test file
    :param path_db: path to database
    :param author (str): who create test
    """
    with open(path_test, 'r') as f:    
        data = yaml.load(f, Loader=yaml.FullLoader)
    filename = os.path.split(path_test)[1]
    testname = data['testname']
    createdate = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    begindate = data['begindate'] or ''
    enddate = data['enddate'] or ''
    duration = str(data['duration']) or ''
    author = author or ''
    
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT key FROM tests")
        keys = set([v[0] for v in cursor.fetchall()])
        key = random_string(4)
        while key in keys:
            key = random_string(4)

        values = [filename, testname, createdate, begindate, enddate, duration, key, author]
        cursor.execute("INSERT INTO tests VALUES (?,?,?,?,?,?,?,?)", values)
        conn.commit()


async def upload_file(bot, fileid, filename, path_tests):
    downloaded = await bot.download_file_by_id(fileid)
    b = BytesIO()
    b.write(downloaded.getvalue())
    with open(os.path.join(path_tests, filename), 'wb') as f:
        f.write(b.getvalue())


def update_db_tests(correct_flg, filename, path_db, path_tests):
    """Update database table 'tests'"""
    # delete row with dame filename
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tests WHERE filename=?", (filename, ))
        conn.commit()
    if correct_flg:
        # write new test info
        write_info(os.path.join(path_tests, filename), path_db)


def check_file(filename):
    """Check test file.

    :return:
        correct_flag (bool)
        error_messages (str)
    """
    try:
        test_data = load_test(filename)
    except Exception:
        return False, "File don't read"

    checker = Checker()
    error_messages = checker(test_data)
    correct_flg = error_messages == ''
    return correct_flg, error_messages



# #####     FUNCTIONS FOR RUN TEST      ######

def load_test(filename):
    cur_dir = os.path.dirname(os.path.abspath(__file__))
    path_file = os.path.join(os.path.split(cur_dir)[0], 'data', 'tests', filename)
    if not os.path.exists(path_file):
        print(f'file do not exist {path_file}')
        return

    with open(path_file, 'r') as f:    
        data = yaml.load(f, Loader=yaml.FullLoader)
        # print(data)
    return data


