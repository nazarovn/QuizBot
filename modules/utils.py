import sqlite3
from datetime import datetime

from parser_tests import load_test



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

# def load_tests_info(path_db: str):


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
    
    answer = data[0]   # filename
    return True, answer


def update_db_test_status(filename, test_data, callback_query, path_db):
    userlogin = callback_query.from_user.username
    username = callback_query.from_user.first_name + ' ' + callback_query.from_user.last_name
    userid = callback_query.from_user.id
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    status = 'open'
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO tests_status VALUES (?,?,?,?,?)", [filename, userlogin, current_date, status, ''])
        conn.commit()


def ask_question(callback_query, path_db):
    userlogin = callback_query.from_user.username
    username = callback_query.from_user.first_name + ' ' + callback_query.from_user.last_name
    userid = callback_query.from_user.id
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # get info about test
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, date FROM tests_status WHERE userlogin = ? AND status = 'open'", [userlogin])
        # take filename with max date
        filename, date_start_test = sorted(cursor.fetchall(), key=lambda x: x[1])[-1]
        
        # find asked questions
        cursor.execute(
            "SELECT question_id FROM answers WHERE userlogin = ? AND filename = ? AND  datebegin = ?",
            [userlogin, filename, date_start_test]
        )
        asked_question = [v[0] for v in cursor.fetchall()]

    test_data = load_test(filename)
    count_questions = len(test_data['questions'])
    all_question = list(range(count_questions))
    not_asked_question = list(set(all_question) - set(asked_question))
    
    if not not_asked_question:
        return


    next_question_id = min(not_asked_question)
    next_question = test_data['questions'][next_question_id]
    # write to db
    text_question = f"[{next_question_id + 1}/{count_questions}] {next_question['question']}"
    message_type = 'question'
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO answers VALUES (?,?,?,?,?,?,?,?,?)",
            [userlogin, username, userid, filename, date_start_test, current_date, next_question_id, message_type, text_question]
        )
        conn.commit()
    # return text message
    return text_question
   

def write_answer(message, path_db):
    userlogin = message.from_user.username
    username = message.from_user.first_name + ' ' + message.from_user.last_name
    userid = message.from_user.id
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    message_type = 'answer'
    next_question_id = ''
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, date FROM tests_status WHERE userlogin = ? AND status = 'open'", [userlogin])
        # take filename with max date
        filename, date_start_test = sorted(cursor.fetchall(), key=lambda x: x[1])[-1]
        
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO answers VALUES (?,?,?,?,?,?,?,?,?)",
            [userlogin, username, userid, filename, date_start_test, current_date, next_question_id, message_type, message.text]
        )
        conn.commit()
    # return text message
    return 'The answer has been written'
   


