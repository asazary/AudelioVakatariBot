import os
from io import BytesIO
import requests
import subprocess

from init_bot import bot
import dbfuncs
import _config
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


def send_list_of_audio(uid):
    audio_list = dbfuncs.get_user_audio_list(uid)
    if len(audio_list) < 1:
        text = "У вас нет аудио в базе"
    else:
        text = "Список ваших аудио:\n"
        for item in audio_list:
            text += "\n" + item[2] + (" (%d байт)" % item[4])
    bot.send_message(uid, text)


def get_audio_files(uid, file_list):
    file_list = sorted(list(set(file_list)))

    result = dbfuncs.get_user_audio_files(uid, file_list)
    for item in result:
        file = BytesIO(item[1])
        bot.send_audio(uid, file, title=item[0])
        file.close()

    dif = sorted(list(set(file_list) - set([x[0] for x in result])))
    if dif:
        logger.info(f"{uid}: not found: " + ", ".join(dif))
        bot.send_message(uid, "Следующие файлы не были найдены:\n" + "\n".join(dif))


def process_audio(uid, file_id):
    audio_id = file_id
    file_info = bot.get_file(audio_id)
    file_link = f'https://api.telegram.org/file/bot{_config.token}/{file_info.file_path}'
    try:
        r = requests.get(file_link, proxies=_config.proxies)
    except Exception as e:
        bot.send_message(uid, "Не удалось получить файл с сервера telegram")
        logger.error(f"{uid}: Error during getting file from telegram server: {str(e)}")
        return
    if r.status_code != 200:
        bot.send_message(uid, "Не удалось загрузить файл в базу")
        logger.error(f"{uid}: Can't get file from telegram server (not 200 code)")
        return
    logger.info(f"{uid}: file downloaded from telegram server")

    input_filename = f"{file_id}.tmp"
    output_filename = f"{file_id}." + _config.audio_file_extension
    with open(input_filename, "wb") as fin:
        fin.write(r.content)

    try:
        logger.info(f"{uid}: start processing audio file")
        process = subprocess.check_call(f"ffmpeg -i {input_filename} -f wav -acodec pcm_s16le -ar 16000 {output_filename}")
        logger.info(f"{uid}: file processed")
    except subprocess.CalledProcessError as e:
        logger.error(f"{uid}: Error during processing file: {str(e)}")
        bot.send_message(uid, "Не удалось обработать файл")
        return
    # os.system(f"ffmpeg -i {input_filename} -f wav -acodec pcm_s16le -ar 16000 {output_filename}")

    os.remove(input_filename)

    with open(output_filename, "rb") as res_file:
        file_data = res_file.read()
        res = dbfuncs.insert_user_audio(uid, file_data)

    os.remove(output_filename)

    if res is not None:
        bot.send_message(uid, res)
    else:
        logger.info(f"{uid}: audio file added")
        bot.send_message(uid, "Аудио добавлено")


def remove_all_audio_files(uid):
    result = dbfuncs.remove_all_audio_files(uid)
    logger.info(f"{uid}: removed {result} audio files")
    bot.send_message(uid, "Удалено %d файлов." % result)


def remove_audio_files(uid, file_list):
    file_list = sorted(list(set(file_list)))
    result = dbfuncs.remove_audio_files(uid, file_list)
    logger.info(f"{uid}: removed {result} audio files")
    bot.send_message(uid, "Удалено %d файлов." % result)