import sqlite3
from _config import dbname, audio_name_prefix, audio_file_extension, photo_name_prefix, photo_file_extension
import os
import logging
from _config import log_c_format, log_f_format, log_file_name

logger = logging.getLogger(__name__)
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(log_file_name)
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)
c_format = logging.Formatter(log_c_format)
f_format = logging.Formatter(log_f_format)
c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)
logger.setLevel(logging.INFO)


def connect():
    conn = sqlite3.connect(dbname)
    return conn


def create_database():
    try:
        conn = connect()
        cursor = conn.cursor()

        cursor.execute("create table user_audio " \
                       "(id integer primary key AUTOINCREMENT, " \
                       "uid integer not null, " \
                       "name text not null, " \
                       "num integer not null, " \
                       "data blob not null)" \
                       )
        cursor.execute("create table user_photos " \
                       "(id integer primary key AUTOINCREMENT, " \
                       "uid integer not null, " \
                       "name text not null, " \
                       "num integer not null, " \
                       "data blob not null)" \
                       )
        cursor.execute("create index user_audio_uid_i on user_audio(uid)")
        cursor.execute("create index user_photos_uid_i on user_photos(uid)")
        cursor.close()
        conn.close()
        logger.info("Database created")
    except Exception as e:
        logger.critical("Error during creating database: " + str(e))


def check_database_and_create():
    if not os.path.exists(dbname):
        create_database()


def recreate_database():
    os.remove(dbname)
    create_database()


def insert_user_audio(uid, data):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select max(num) from user_audio where uid=?", (uid,))
    current_max_num = cursor.fetchone()[0]
    if current_max_num is not None:
        new_num = current_max_num + 1
    else:
        new_num = 0
    name = audio_name_prefix + str(new_num) + "." + audio_file_extension

    cursor.execute("insert into user_audio (uid, name, num, data) values (?, ?, ?, ?);",
                   (uid, name, new_num, data))
    if cursor.rowcount < 1:
        logger.warning(f"{uid}: audio not added (rowcount = 0)")
        return "Не удалось добавить файл в базу"
    conn.commit()
    cursor.close()
    conn.close()
    return None


def get_user_audio_list(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select id, uid, name, num, length(data) from user_audio where uid=? order by num", (uid,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def get_user_audio_files(uid, file_list):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select name, data from user_audio " \
                   "where uid=? and name in (%s) order by num" % ",".join("?"*len(file_list)), (uid, *file_list))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def remove_all_audio_files(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("delete from user_audio where uid=?", (uid,))
    result = cursor.rowcount
    logger.info(f"{uid}: Audio files removed: {result}")
    conn.commit()
    cursor.close()
    conn.close()
    return result


def remove_audio_files(uid, file_list):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("delete from user_audio "\
                   "where uid=? and name in (%s)" % ",".join("?"*len(file_list)), (uid, *file_list))
    result = cursor.rowcount
    logger.info(f"{uid}: Audio files removed: {result}")
    conn.commit()
    cursor.close()
    conn.close()
    return result


def get_user_photos_list(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select id, uid, name, num, length(data) from user_photos where uid=? order by num", (uid,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


def insert_user_photo(uid, file_data):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select max(num) from user_photos where uid=?", (uid,))
    current_max_num = cursor.fetchone()[0]
    if current_max_num is not None:
        new_num = current_max_num + 1
    else:
        new_num = 0
    name = photo_name_prefix + str(new_num) + "." + photo_file_extension

    cursor.execute("insert into user_photos (uid, name, num, data) values (?, ?, ?, ?);",
                   (uid, name, new_num, file_data))
    if cursor.rowcount < 1:
        log.warning(f"{uid}: Photo not added (rowcount = 0)")
        return "Не удалось добавить файл в базу"
    conn.commit()
    cursor.close()
    conn.close()
    return None


def remove_all_photo_files(uid):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("delete from user_photos where uid=?", (uid,))
    result = cursor.rowcount
    logger.info(f"{uid}: Photo files removed: {result}")
    conn.commit()
    cursor.close()
    conn.close()
    return result


def get_user_photo_files(uid, file_list):
    conn = connect()
    cursor = conn.cursor()
    cursor.execute("select name, data from user_photos " \
                   "where uid=? and name in (%s) order by num" % ",".join("?"*len(file_list)), (uid, *file_list))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result


if __name__ == "__main__":
    if not os.path.exists(dbname):
        create_database()
        print("DB created")
    else:
        recreate_database()
        print("DB recreated")

