import telebot
from telebot import apihelper
from _config import token


apihelper.proxy = {'https': "https://127.0.0.1:9080"}
bot = telebot.TeleBot(token)