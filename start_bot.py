import glob
import time
from datetime import datetime, timedelta
from logging import Formatter, FileHandler

from selenium.webdriver.common.by import By
from database_handler.db import Db
import telebot
from threading import Thread

from dispatcher import Dispatcher
from dispatcher_manager import DispatcherManager
from order_sender.order_sender import OrderSender
from settings import logger, token, logs_file_change_delay
from parser_handler.parser import Parser
import random

db = Db()

bot = telebot.TeleBot(token=token)

admin_keyboard = telebot.types.ReplyKeyboardMarkup(True)

admin_keyboard.row('🙉 Включить эфир 🙉')
admin_keyboard.row('✅ Добавить ✅', '❌ Удалить пользователя ❌')
admin_keyboard.row('🚖 Список водителей 🚖', '🤴 Список админов 🤴')

admin_keyboard1 = telebot.types.ReplyKeyboardMarkup(True)

admin_keyboard1.row('🙈 Выключить эфир 🙈')
admin_keyboard1.row('✅ Добавить ✅', '❌ Удалить пользователя ❌')
admin_keyboard1.row('🚖 Список водителей 🚖', '🤴 Список админов 🤴')

stop_keyboard = telebot.types.ReplyKeyboardMarkup(True)
stop_keyboard.row('🚫 Стоп 🚫')

add_users_keyboard = telebot.types.ReplyKeyboardMarkup(True)
add_users_keyboard.row('🚨 Добавить Админа 🚨')
add_users_keyboard.row('💥 Добавить водителя 💥')
add_users_keyboard.row('🚫 Стоп 🚫')

images = glob.glob("./images/*")


def get_users():
    try:
        token = db.create_connection()
        data = db.get_users(token)
        db.close_connection(token)
    except Exception as err:
        logger.error(f"Error while getting users from db, {err = }")

    for user in data:
        try:
            data[user]["chat_id"] = user
            logger.info(f"Got user {data[user]}")
        except Exception as err:
            logger.error(f"Error while processing, {err = }")

    return data


@bot.message_handler(commands=['start'])
def start_message(message):
    chat_id = message.chat.id

    user = users.get(chat_id)

    if user is None or user.get("rule") is None:
        for x in range(10):
            try:
                bot.send_message(message.chat.id, f'Извини но твой айди не в базе данных ({chat_id})')
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

    elif user["rule"] == "driver":
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Яххаааа, баля 👋. Добро пожаловать братишка')
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
            logger.error(f"Error while sending photo, {err = }")

        time.sleep(3)

    elif user["rule"] == "admin":
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Здарова, бро!', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
            logger.error(f"Error while sending photo, {err = }")

        bot.register_next_step_handler(message, admin_panel)


def admin_panel(message):
    if "Добавить" in message.text:
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Кого добавить?', reply_markup=add_users_keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, register_user)
    elif "Список водителей" in message.text:
        i = 0
        for user in users:
            user_ = users[user]
            if user_['rule'] == "driver":
                i += 1
                for x in range(10):
                    try:
                        message = bot.send_message(message.chat.id, f'{i}. {user} - {user_["taxi_id"]} - водитель')
                        break
                    except Exception as err:
                        logger.error(f"Error while sending message, {err = }")
                        time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)
    elif "Список админов" in message.text:
        i = 0
        for user in users:
            user_ = users[user]
            if user_['rule'] == "admin":
                i += 1
                for x in range(10):
                    try:
                        message = bot.send_message(message.chat.id, f'{i}. {user} - {user_["taxi_id"]} - админ')
                        break
                    except Exception as err:
                        logger.error(f"Error while sending message, {err = }")
                        time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)
    elif "Удалить пользователя" in message.text:
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, f'Введи номер айди чата для удаления.', reply_markup=stop_keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, delete_user)
    elif "Включить эфир" in message.text:
        if users[message.chat.id]["is_thread"]:
            string = "Нельзя включить поток повторно!"
            keyboard = admin_keyboard1
        else:
            string = "Поток успешно включен!"
            users[message.chat.id]["is_thread"] = True
            keyboard = admin_keyboard1

        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, string, reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)

    elif "Выключить эфир" in message.text:
        if users[message.chat.id]["is_thread"]:
            string = "Поток успешно выключен!"
            users[message.chat.id]["is_thread"] = False
            keyboard = admin_keyboard
        else:
            string = "Нельзя выключить поток повторно!"
            keyboard = admin_keyboard

        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, string, reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)

    elif message.text == "/start":
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Здарова, бро!', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
            logger.error(f"Error while sending photo, {err = }")

        bot.register_next_step_handler(message, admin_panel)
    else:
        bot.register_next_step_handler(message, admin_panel)
        for x in range(10):
            try:
                bot.delete_message(message.chat.id, message.message_id)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)


def delete_user(message):
    chat_id = message.text

    if "Стоп" in message.text:
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Возвращаю в меню', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)
    elif message.text == "/start":
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Здарова, бро!', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
            logger.error(f"Error while sending photo, {err = }")

        bot.register_next_step_handler(message, admin_panel)
    else:
        try:
            chat_id = int(chat_id)
        except ValueError:
            for x in range(10):
                try:
                    message = bot.send_message(message.chat.id, 'Айди чата должен содержать только цифры. Введи номер айди чата для удаления')
                    break
                except Exception as err:
                    logger.error(f"Error while sending message, {err = }")
                    time.sleep(.2)

            bot.register_next_step_handler(message, delete_user)
            return

        if chat_id not in users:
            for x in range(10):
                try:
                    message = bot.send_message(message.chat.id, 'Айди чата не в списке пользователей. Введи номер айди чата для удаления')
                    break
                except Exception as err:
                    logger.error(f"Error while sending message, {err = }")
                    time.sleep(.2)

            bot.register_next_step_handler(message, delete_user)
            return

        try:
            token = db.create_connection()
            db.delete_user(token, chat_id=chat_id)
            db.commit_connection(token)
            db.close_connection(token)
            del users[chat_id]
            string = "Успешно удален пользователь"
        except Exception as err:
            string = f"Не получилось удалить пользователя, ошибка {err}"

        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, string, reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)


def register_user(message):
    if "Добавить Админа" in message.text:
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Введи номер чата', reply_markup=stop_keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, register_admin)
    elif message.text == "/start":
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Здарова, бро!', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
            logger.error(f"Error while sending photo, {err = }")

        bot.register_next_step_handler(message, admin_panel)
    elif "Добавить водителя" in message.text:
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Нужно ввести id телеграмм пользователя, номер авто водителя через запятую (12123124, Е862УЗ123)', reply_markup=stop_keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, register_driver)
    elif "Стоп" in message.text:
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Возвращаю в меню', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)
    else:
        bot.register_next_step_handler(message, register_user)


def register_driver(message):
    data = message.text.replace(" ", "").split(",")

    if "Стоп" in message.text:
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Возвращаю в меню', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)
    elif message.text == "/start":
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Здарова, бро!', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
                logger.error(f"Error while sending photo, {err = }")

        bot.register_next_step_handler(message, admin_panel)
    elif len(data) != 2:
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Неправильно введены данные', reply_markup=stop_keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, register_driver)
    elif len(data) == 2:
        chat_id, taxi_id = data

        try:
            chat_id = int(chat_id)

            if chat_id in users:
                for x in range(10):
                    try:
                        message = bot.send_message(message.chat.id, 'Такой пользователь уже есть', reply_markup=stop_keyboard)
                        break
                    except Exception as err:
                        logger.error(f"Error while sending message, {err = }")
                        time.sleep(.2)

                bot.register_next_step_handler(message, register_driver)
                return

            try:
                token = db.create_connection()

                db.add_user(token, chat_id=chat_id, taxi_id=taxi_id, rule="driver")

                db.commit_connection(token)
                db.close_connection(token)

                users[chat_id] = {"rule": 'driver', "taxi_id": taxi_id}
                string = "Успешно добавлено пользователя"
            except Exception as err:
                string = f"Не получилось добавить пользователя, ошибка {err}"

            keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
            for x in range(10):
                try:
                    message = bot.send_message(message.chat.id, string, reply_markup=keyboard)
                    break
                except Exception as err:
                    logger.error(f"Error while sending message, {err = }")
                    time.sleep(.2)

            bot.register_next_step_handler(message, admin_panel)

        except ValueError:
            for x in range(10):
                try:
                    message = bot.send_message(message.chat.id, 'Айди телеграм чата должен содержать только цифры', reply_markup=stop_keyboard)
                    break
                except Exception as err:
                    logger.error(f"Error while sending message, {err = }")
                    time.sleep(.2)

            bot.register_next_step_handler(message, register_admin)


def register_admin(message):
    if "Стоп" in message.text:
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Возвращаю в меню', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        bot.register_next_step_handler(message, admin_panel)
    elif message.text == "/start":
        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
        for x in range(10):
            try:
                message = bot.send_message(message.chat.id, 'Здарова, бро!', reply_markup=keyboard)
                break
            except Exception as err:
                logger.error(f"Error while sending message, {err = }")
                time.sleep(.2)

        try:
            yaha_image = open(random.choice(images), "rb")
            message = bot.send_photo(message.chat.id, yaha_image)
        except Exception as err:
            logger.error(f"Error while sending photo, {err = }")

        bot.register_next_step_handler(message, admin_panel)
    else:
        try:
            chat_id = int(message.text)

            if chat_id in users:
                for x in range(10):
                    try:
                        message = bot.send_message(message.chat.id, 'Такой пользователь уже есть')
                        break
                    except Exception as err:
                        logger.error(f"Error while sending message, {err = }")
                        time.sleep(.2)

                bot.register_next_step_handler(message, register_driver)
                return

            tries = 5

            while True:
                try:
                    token = db.create_connection()

                    db.add_user(token, chat_id=chat_id, taxi_id=0, rule="admin")

                    db.commit_connection(token)
                    db.close_connection(token)

                    users[chat_id] = {"rule": 'admin', "taxi_id": 0, "is_thread": False}
                    string = "Успешно добавлено пользователя"

                    keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard
                    for x in range(10):
                        try:
                            message = bot.send_message(message.chat.id, string, reply_markup=keyboard)
                            break
                        except Exception as err:
                            logger.error(f"Error while sending message, {err = }")
                            time.sleep(.2)

                    bot.register_next_step_handler(message, admin_panel)
                    break
                except Exception as err:
                    string = f"Не получилось добавить пользователя, ошибка {err}"
                    tries -= 1
                    if tries == 0:
                        keyboard = admin_keyboard1 if users[message.chat.id]["is_thread"] else admin_keyboard

                        for x in range(10):
                            try:
                                message = bot.send_message(message.chat.id, string, reply_markup=keyboard)
                                break
                            except Exception as err:
                                logger.error(f"Error while sending message, {err = }")
                                time.sleep(.2)

                        bot.register_next_step_handler(message, admin_panel)
                        break
                    time.sleep(.25)

        except ValueError:
            for x in range(10):
                try:
                    message = bot.send_message(message.chat.id, 'Айди телеграм чата должен содержать только цифры')
                    break
                except Exception as err:
                    logger.error(f"Error while sending message, {err = }")
                    time.sleep(.2)

            bot.register_next_step_handler(message, register_admin)


def update_bot_chats():
    temp_users = users.copy()
    token = db.create_connection()
    for user in temp_users:
        user_ = temp_users[user]
        for x in range(3):
            try:
                if user_["rule"] == "admin":
                    message = bot.send_message(user, 'Привет, я перезапускался. Теперь я снова здесь', reply_markup=admin_keyboard)
                    bot.register_next_step_handler(message, admin_panel)
                    break
                else:
                    message = bot.send_message(user, 'Привет, я перезапускался. Теперь я снова здесь')
                    break
            except Exception as err:
                logger.info(f"Cant send message, {err = }")
                if "chat not found" in str(err) or "bot was blocked by the user" in str(err):
                    try:
                        db.delete_user(token, chat_id=user)
                        del users[user]
                        logger.info(f"Removed user {user_}")
                    except Exception as err:
                        logger.error(f"Cant remove user {user_}, {err = }")
                    break

            time.sleep(.15)

    db.commit_connection(token)
    db.close_connection(token)


def main():
    update_bot_chats()
    dispatcher_manager = DispatcherManager(bot=bot, users=users)
    dispatcher_manager.add(Dispatcher(name="Первый Партнер", username='novaPP', password='123456qwerqwe'))
    #dispatcher_manager.add(Dispatcher(name="Агент такси", username='novagentbb', password='12345nov', company_number=-1))

    dispatcher_manager.start_parsers()
    dispatcher_manager.start_order_sender()


if __name__ == '__main__':
    users = get_users()
    Thread(target=main).start()
    bot.polling(none_stop=True, timeout=123)
