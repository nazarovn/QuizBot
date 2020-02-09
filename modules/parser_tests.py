import yaml
import os
import sqlite3
from datetime import datetime
import random
import string


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
    author = author or ''
    
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT key FROM tests")
        keys = set([v[0] for v in cursor.fetchall()])
        key = random_string(4)
        while key in keys:
            key = random_string(4)

        values = [filename, testname, createdate, begindate, enddate, key, author]
        cursor.execute("INSERT INTO tests VALUES (?,?,?,?,?,?,?)", values)
        conn.commit()


def save_file(doc):
    pass


def check_file(doc):
    pass


def process_new_file(doc):
    check_file(doc)
    save_file(doc)
    write_info(doc)



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


