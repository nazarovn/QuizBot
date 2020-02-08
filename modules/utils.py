import sqlite3


def is_admin(message, path_db: str):
    """Check messege from Admin or not"""
    login = message.from_user.username
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT login FROM users WHERE status='admin'")
        admin_logins = [v[0] for v in cursor.fetchall()]
    return login in admin_logins


def get_info_show_tests(path_db: str):
    """Return string with info about tests"""
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, testname, createdate, key FROM tests")
        data = cursor.fetchall()
    data = sorted(data, key=lambda x: x[2])
    string = '---\n'.join([
        f'file: {row[0]}\nname: {row[1]}\ncreate: {row[2]}\nkey: {row[3]}\n'
        for row in data
    ])
    return string


######################################################################
#######################    PROCESS QUIZ    ###########################
######################################################################

def load_tests_info(path_db: str):


def process_test_command_argumens(arguments, path_db: str):
    """Check run quiz or not

    :param arguments (List[str]): arguments /test
    :param path_db: path to database
    :return: permission (bool), answer (str)
    """
    if len(arguments) == 0:
        answer = "Write key test. Example: /test <key>"
        return False, answer
    if len(arguments) > 2:
        answer = "Too many arguments. Example: /test <key>"
        return False, answer

    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, testname, createdate, begindate, enddate, key FROM tests WHERE key=?", (arguments[0], ))
        data = cursor.fetchone()
        # ToDo: if few row (not unique key)
    if not data:
        answer = "Key don't find, try other key"
        return False, answer

    if len(arguments) == 2:
        #with sqlite3.connect(path_db) as conn:
        #    cursor = conn.cursor()
        #    cursor.execute("SELECT filename, testname, createdate, key FROM tests WHERE key=?", (arguments[0], ))
        #    data = cursor.fetchall()
        # ToDo: if test password
        pass
    # ToDo: other checks: begindate, enddate, userlogins

    return True, None




