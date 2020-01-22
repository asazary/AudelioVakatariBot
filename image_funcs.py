from init_bot import bot
import dbfuncs
from io import BytesIO
import requests
import _config
import dlib
from skimage import io
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


def send_list_of_photos(uid):
    photos_list = dbfuncs.get_user_photos_list(uid)
    if len(photos_list) < 1:
        text = "У вас нет фото в базе"
    else:
        text = "Список ваших фото:\n"
        for item in photos_list:
            text += "\n" + item[2] + (" (%d байт)" % item[4])
    bot.send_message(uid, text)


def upload_photo(uid, file_id):
    file_info = bot.get_file(file_id)
    file_link = f'https://api.telegram.org/file/bot{_config.token}/{file_info.file_path}'
    try:
        r = requests.get(file_link, proxies=_config.proxies)
    except Exception as e:
        logger.error(f"{uid}: Error during getting file from telegram server: {str(e)}")
        bot.send_message(uid, "Не удалось получить файл с сервера telegram")
        return
    if r.status_code != 200:
        logger.error(f"{uid}: Can't get file from telegram server (not 200 code)")
        bot.send_message(uid, "Не удалось загрузить файл в базу")
        return
    logger.info(f"{uid}: file downloaded from telegram server")

    file_data = r.content
    file_name = "file_" + file_id + ".tmp"
    with open(file_name, "wb") as f:
        f.write(file_data)

    logger.info(f"{uid}: start processing photo file")
    face_detector = dlib.get_frontal_face_detector()
    image = io.imread(file_name)
    detected_faces = face_detector(image, 1)
    logger.info(f"{uid}: photo file processed")

    os.remove(file_name)

    if len(detected_faces) > 0:
        res = dbfuncs.insert_user_photo(uid, file_data)

        if res is not None:
            bot.send_message(uid, res)
        else:
            logger.info(f"{uid}: photo file added")
            bot.send_message(uid, "Фото добавлено")
    else:
        logger.info(f"{uid}: photo file not added (faces not detected)")
        bot.send_message(uid, "Лица не обнаружены, фото не добавлено")


def remove_all_photo_files(uid):
    result = dbfuncs.remove_all_photo_files(uid)
    logger.info(f"{uid}: removed {result} photo files")
    bot.send_message(uid, "Удалено %d файлов." % result)


def get_photo_files(uid, file_list):
    file_list = sorted(list(set(file_list)))

    result = dbfuncs.get_user_photo_files(uid, file_list)
    for item in result:
        file = BytesIO(item[1])
        bot.send_photo(uid, photo=file)
        file.close()

    dif = sorted(list(set(file_list) - set([x[0] for x in result])))
    if dif:
        logger.info(f"{uid}: not found: " + ", ".join(dif))
        bot.send_message(uid, "Следующие файлы не были найдены:\n" + "\n".join(dif))