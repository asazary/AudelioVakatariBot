import sys

from init_bot import bot

import dbfuncs
import threading
import audio_funcs
import image_funcs
import logging
import time
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


@bot.message_handler(commands=["start", "help"])
def start(message):
    help_text = \
        '''Функции бота:
        Конвертирование аудио в wav 16 khz, запись в бд на сервере и возможность скачать их.
        Поиск лиц на отправленных фото и запись их в бд, если лица обнаружены.
        Команды:
        /help - Показать описание
        /audio_list - Показать список аудио файлов
        /get_audio - Скачать указанные аудио (через пробел или запятую)
        /remove_all_audio - Удалить все аудио
        /photos_list - Показать список фото
        /get_photo - Скачать указанные фото (через пробел или запятую)
        /remove_all_photos - Удалить все фото
        '''
    bot.send_message(message.from_user.id, help_text)


@bot.message_handler(commands=["audio_list"])
def command_get_list_of_audio(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: audio_list")
    threading.Thread(target=(lambda: audio_funcs.send_list_of_audio(message.from_user.id))).start()


@bot.message_handler(commands=["get_audio"])
def get_audio_command(message):
    file_list = message.text.replace(",", " ").strip().split()[1:]
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: get_audio (" +
                ", ".join(file_list) + ")")

    if len(file_list) == 0:
        bot.send_message(message.from_user.id, "Не указаны файлы")
        return

    threading.Thread(target=(lambda: audio_funcs.get_audio_files(message.from_user.id, file_list))).start()


@bot.message_handler(commands=["remove_all_audio"])
def remove_all_audio(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: remove_all_audio")
    threading.Thread(target=(lambda: audio_funcs.remove_all_audio_files(message.from_user.id))).start()


@bot.message_handler(commands=["remove_audio"])
def remove_audio(message):
    file_list = message.text.replace(",", " ").strip().split()[1:]
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: remove_audio (" +
                ", ".join(file_list) + ")")

    if len(file_list) == 0:
        bot.send_message(message.from_user.id, "Не указаны файлы")
        return
    threading.Thread(target=(lambda: audio_funcs.remove_audio_files(message.from_user.id, file_list))).start()


@bot.message_handler(content_types=["audio"])
def handle_audio_message(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: audio (" +
                f"{message.audio.mime_type}, {message.audio.file_size} bytes)")
    threading.Thread(target=(lambda: audio_funcs.process_audio(message.from_user.id, message.audio.file_id))).start()


@bot.message_handler(content_types=["voice"])
def handle_voice_message(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: voice (" +
                f"{message.voice.mime_type}, {message.voice.file_size} bytes)")
    threading.Thread(target=(lambda: audio_funcs.process_audio(message.from_user.id, message.voice.file_id))).start()


@bot.message_handler(commands=["photos_list"])
def command_get_list_of_photos(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: photos_list")
    threading.Thread(target=(lambda: image_funcs.send_list_of_photos(message.from_user.id))).start()


@bot.message_handler(content_types=["photo"])
def handle_photo_message(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: photo")
    threading.Thread(target=(lambda: image_funcs.upload_photo(message.from_user.id, message.photo[-1].file_id))).start()


@bot.message_handler(commands=["remove_all_photos"])
def remove_all_audio(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: remove_all_photos")
    threading.Thread(target=(lambda: image_funcs.remove_all_photo_files(message.from_user.id))).start()


@bot.message_handler(commands=["get_photo"])
def get_audio_command(message):
    file_list = message.text.replace(",", " ").strip().split()[1:]

    logger.info(f"{message.from_user.id} ({message.from_user.username}) - command: get_photo (" +
                ", ".join(file_list) + ")")

    if len(file_list) == 0:
        bot.send_message(message.from_user.id, "Не указаны файлы")
        return

    threading.Thread(target=(lambda: image_funcs.get_photo_files(message.from_user.id, file_list))).start()


@bot.message_handler(content_types=["document"])
def handle_document(message):
    #print(message)
    if message.document.mime_type.split('/')[0] == "audio":
        logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: audio as document (" +
                    f"{message.document.mime_type}, {message.document.file_size} bytes)")
        threading.Thread(
            target=(lambda: audio_funcs.process_audio(message.from_user.id, message.document.file_id))).start()
    elif message.document.mime_type.split('/')[0] == "image":
        logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: photo as document")
        threading.Thread(
            target=(lambda: image_funcs.upload_photo(message.from_user.id, message.document.file_id))).start()
    else:
        logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: document")
        bot.send_message(message.from_user.id, "Не знаю, что с этим делать.")


@bot.message_handler(content_types=["text"])
def get_text_messages(message):
    logger.info(f"{message.from_user.id} ({message.from_user.username}) - handle: text ({message.text})")

    if message.text.lower().strip() in ("привет", "приветствую", "здравствуй", "хай"):
        bot.send_message(message.from_user.id, "Приветствую")
    else:
        bot.send_message(message.from_user.id, "Хм...")


if __name__ == "__main__":
    dbfuncs.check_database_and_create()
    logger.info("Start bot")
    while True:
        try:
            # bot.polling(none_stop=True, interval=0)
            bot.infinity_polling(True)

        except KeyboardInterrupt as e:
            logger.warning("KeyboardInterrupt. Stop bot")
            sys.exit(0)
        except Exception as e:
            logger.error("ERROR while polling: " + str(e))
            time.sleep(5)


