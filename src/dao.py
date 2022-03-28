import sqlite3
from params import *

conn = sqlite3.connect(db_file, check_same_thread=False)
cursor = conn.cursor()


def insert_new_user(user_id: int, name: str, surname: str, username: str):
    cursor.execute('INSERT INTO users (user_id, name, surname, username) VALUES(?, ?, ?, ?)',
                   (user_id, name, surname, username))
    conn.commit()


def user_exists(user_id: int):
    for row in cursor.execute('SELECT COUNT(*) FROM users where user_id={}'.format(user_id)):
        return True if row[0] == 1 else False


def insert_new_message(user_id: int, content: str):
    cursor.execute('INSERT INTO messages (user_id, content) VALUES(?, ?)',
                   (user_id, content))
    conn.commit()


def insert_new_customer(user_id: int, name: str):
    cursor.execute('INSERT INTO customers (user_id, name) VALUES(?, ?)',
                   (user_id, name))
    conn.commit()


def get_customers(user_id: int):
    return cursor.execute("SELECT id, name FROM customers  WHERE user_id={}".format(user_id))


def insert_new_project(user_id: int, name: str):
    cursor.execute('INSERT INTO projects (user_id, name) VALUES(?, ?)',
                   (user_id, name))
    conn.commit()
    return cursor.lastrowid


def get_projects(user_id: int):
    return cursor.execute("SELECT id, name FROM projects  WHERE user_id={}".format(user_id))


def update_project_with_customer(project_id: int, customer_id: int):
    cursor.execute('UPDATE projects SET customer_id={} WHERE id={}'.format(customer_id, project_id))
    conn.commit()


def set_active_project(user_id, project_id):
    cursor.execute('INSERT OR REPLACE INTO active_projects (user_id, project_id) VALUES(?, ?)',
                   (user_id, project_id))
    conn.commit()


def user_has_active_project(user_id: int):
    for row in cursor.execute('SELECT COUNT(*) FROM active_projects WHERE user_id={}'.format(user_id)):
        return True if row[0] == 1 else False


def get_active_project(user_id: int):
    for row in cursor.execute('SELECT project_id FROM active_projects WHERE user_id={} LIMIT 1'.format(user_id)):
        return row[0]


def add_record(user_id: int, project_id: int):
    cursor.execute('INSERT INTO records (user_id, project_id, start) VALUES(?, ?, DATETIME(CURRENT_TIMESTAMP, \'-5 hours\'))',
                   (user_id, project_id))
    conn.commit()


def user_has_active_record(user_id: int):
    for row in cursor.execute('SELECT COUNT(*) FROM records WHERE finish IS NULL and user_id={}'.format(user_id)):
        return True if row[0] == 1 else False


def get_active_task_start_time(user_id: int):
    for row in cursor.execute('SELECT start FROM records WHERE finish IS NULL and user_id={}'.format(user_id)):
        return row[0]


def finish_active_task(user_id: int, description: str):
    cursor.execute('UPDATE records SET finish=DATETIME(CURRENT_TIMESTAMP, \'-5 hours\'), description=\'{}\' WHERE user_id={} and finish IS NULL;'.format(description, user_id))
    conn.commit()