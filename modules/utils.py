import sqlite3
from datetime import datetime, timedelta
import random

from parser_tests import load_test


def is_admin(message, path_db: str):
    """Check messege from Admin or not"""
    login = message.from_user.username
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT login FROM users WHERE status='admin'")
        admin_logins = [v[0] for v in cursor.fetchall()]
    return login in admin_logins


def get_info_show_tests(path_db: str, filename=None):
    """Return string with info about tests for printing in bot's message"""
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        if filename:
            cursor.execute("SELECT filename, testname, createdate, key FROM tests WHERE filename=?", (filename, ))
        else:
            cursor.execute("SELECT filename, testname, createdate, key FROM tests")
        data = cursor.fetchall()
    data = sorted(data, key=lambda x: x[2])
    string = '---\n'.join([
        f'file: {row[0]}\nname: {row[1]}\ncreate: {row[2]}\nkey: {row[3]}\n'
        for row in data
    ])
    return string


def get_user_info(user):
    """Return info about user.

    :param user: object with attributes: username, first_name, last_name, id
    :return: userlogin, username, userid
    """
    userlogin = user.username
    username = user.first_name + ' ' + user.last_name
    userid = user.id
    return userlogin, username, userid


def generate_new_password(path_db):
    new_passwd = str(random.randint(1e5, 1e6 - 1))
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM passwords")
        conn.commit()
        cursor.execute(
            "INSERT INTO passwords VALUES (?,?,?,?) ",
            ("test", "any", new_passwd, current_date, )
        )
        conn.commit()
    return new_passwd


def get_password(path_db):
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM passwords")
        passwd = cursor.fetchone()
    return passwd


######################################################################
#######################    PROCESS TEST    ###########################
######################################################################

def check_test_permission(arguments, message, filename, test_data, path_db):
    """Check permission by login, test was written in the past.

    return: permission: bool, answer: str, errors or filename
    """
    if len(arguments) == 2:
        with sqlite3.connect(path_db) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT password FROM passwords")
            passwd = cursor.fetchone()[0]
        if passwd == arguments[1]:
            return True, filename
        else:
            return False, "Permission denied. Wrong password."
    elif len(arguments) == 1:
        userlogin, username, userid = get_user_info(message.from_user)
        with sqlite3.connect(path_db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT userlogin FROM tests_status WHERE filename=? AND userlogin=?",
                (filename, userlogin, )
            )
            past_test_attempts = cursor.fetchall()

        # first check. Login in user_logins
        if test_data['user_logins'] is not None:
            if userlogin not in test_data['user_logins']:
                return False, "Permission denied. Your login is missing in test's user_logins."
        # second check. Test has already been written.
        if past_test_attempts:
            return False, "Permission denied. You have already passed the test."
        return True, filename


def process_test_command_argumens(arguments, message, path_db: str):
    """Check run quiz or not

    :param arguments:  (List[str]) arguments /test
    :param path_db: path to database
    :return:
        permission (bool);
        answer (str), if permission==True, then answer is filename, else error string.
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

    filename = data[0]
    test_data = load_test(filename)

    permission, answer = check_test_permission(arguments, message, filename, test_data, path_db)
    return permission, answer


def update_db_test_status_begin(filename, test_data, callback_query, path_db):
    userlogin, username, userid = get_user_info(callback_query.from_user)
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    status = 'begin'
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tests_status VALUES (?,?,?,?,?,?,?)",
            [filename, userlogin, username, userid, current_date, status, '']
        )
        conn.commit()


def update_db_test_status_end(message, path_db):
    userlogin, username, userid = get_user_info(message.from_user)
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
    status = 'end'
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, date FROM tests_status WHERE userlogin = ? AND status = 'begin'", [userlogin])
        # take filename with max date
        filename, date_start_test = sorted(cursor.fetchall(), key=lambda x: x[1])[-1]

        cursor.execute(
            "INSERT INTO tests_status VALUES (?,?,?,?,?,?,?)",
            [filename, userlogin, username, userid, current_date, status, '']
        )
        conn.commit()


def ask_question(callback_query, path_db):
    userlogin, username, userid = get_user_info(callback_query.from_user)
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    # get info about test
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, date FROM tests_status WHERE userlogin = ? AND status = 'begin'", [userlogin])
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
    if next_question['question_type'] == 'text':
        text_question = f"[{next_question_id + 1}/{count_questions}] {next_question['question']}"
    elif next_question['question_type'] == 'button':
        text_question = f"[{next_question_id + 1}/{count_questions}] {next_question['question']}"
        for idx, variant in enumerate(next_question['variants']):
            text_question += f"\n    {idx+1}) {variant}"
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
    """Write answer to db.

    :return:
        success (bool): False if time ended, else True
        answer (str): message for send to user"""
    userlogin, username, userid = get_user_info(message.from_user)
    current_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')

    message_type = 'answer'
    next_question_id = ''
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, date FROM tests_status WHERE userlogin = ? AND status = 'begin'", [userlogin])
        # take filename with max date
        filename, date_start_test = sorted(cursor.fetchall(), key=lambda x: x[1])[-1]

        # check time limit
        cursor.execute("SELECT duration FROM tests WHERE filename=?", (filename, ))

        duration = cursor.fetchone()[0]
        if duration:
            duration = int(duration)
            date_start_test_ = datetime.fromisoformat(date_start_test)
            current_date = datetime.now()
            time_to_end_timelimit = date_start_test_ + timedelta(minutes=duration) - current_date
            if time_to_end_timelimit < timedelta(0):
                return False, 'Time end.'
            minutes_timelimit, senonds_timelimit = divmod(time_to_end_timelimit.total_seconds(), 60)
            minutes_timelimit, senonds_timelimit = round(minutes_timelimit), round(senonds_timelimit)

        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO answers VALUES (?,?,?,?,?,?,?,?,?)",
            [userlogin, username, userid, filename, date_start_test, current_date, next_question_id, message_type, message.text]
        )
        conn.commit()
    # return text message
    answer = 'The answer has been written.'
    if duration:
        answer += f" Remaining time {minutes_timelimit}:{senonds_timelimit}."
    return True, answer


def get_test_score(message, path_db):
    """Calculate test score for user after test."""
    userlogin, username, userid = get_user_info(message.from_user)
    with sqlite3.connect(path_db) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT filename, date FROM tests_status WHERE userlogin = ? AND status = 'begin'", [userlogin,])
        # take filename with max date
        filename, date_start_test = sorted(cursor.fetchall(), key=lambda x: x[1])[-1]

        test_data = load_test(filename)

        cursor.execute(
            "SELECT date, question_id, message_type, message FROM answers WHERE userlogin=? AND datebegin=? AND filename=?",
            [userlogin, date_start_test, filename])
        test_messages = sorted(cursor.fetchall(), key=lambda x: x[0])
        answers_user = [row[3] for row in test_messages[1::2]]
        answers_id = [row[1] for row in test_messages[0::2]][:len(answers_user)]
        answers_true = [test_data['questions'][idx]['answer'] for idx in answers_id]

    count_question = len(test_data['questions'])
    count_true_answer = 0
    for answer_user, answer_true in zip(answers_user, answers_true):
        if answer_user.lower() == answer_true.lower():
            count_true_answer += 1
    message_for_user = f"Score {round(count_true_answer / count_question * 100)}%, {count_true_answer}/{count_question}"
    return message_for_user
