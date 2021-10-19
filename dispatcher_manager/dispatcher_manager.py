import time
from datetime import datetime, timedelta
from logging import Formatter, FileHandler
from multiprocessing.dummy import Pool
from threading import Thread

from settings import logger, sending_message_threads


class DispatcherManager:
    message_skeleton = "Адрес (от): {}\n" \
                       "Адрес (куда): {}\n" \
                       "Способ оплаты: {}\n" \
                       "Номер машины: {}\n" \
                       "Диспетчерская: {}\n" \
                       "Сообщение удалиться через: {} секунд"

    tries = 3
    delay = 1

    def __init__(self, bot, users):
        self.dispatchers = []
        self.orders = []
        self.users = users
        self.bot = bot

    def add(self, dispatcher):
        self.dispatchers.append(dispatcher)

    def send_message(self, data, user, is_format=True):
        for x in range(self.tries):
            logger.info(f"Trying to send message, try = {x}")
            try:
                string = self.message_skeleton.format(
                    data['pickup_place'], data['destination_place'], data['type'], data['licence_plate'], data["dispatcher"], data['life_time']) \
                    if is_format else data
                message = self.bot.send_message(user["chat_id"], string)
                logger.info(f"Send message successfully")
                return message
            except Exception as err:
                logger.error(f"Error while sending message {err = }")
                time.sleep(self.delay)

    def remove_message(self, user, message_id):
        for x in range(self.tries):
            logger.info(f"Trying to delete message, try = {x}")
            try:
                message_ = self.bot.delete_message(user["chat_id"], message_id)
                logger.info(f"Removed message successfully")
                break
            except Exception as err:
                logger.error(f"Error while removing message {err = }")
                time.sleep(self.delay)

    def edit_message(self, data, user, message_id):
        for x in range(1):
            logger.info(f"{user['chat_id']} Trying to edit message, try = {x}")
            try:

                string = self.message_skeleton.format(
                    data['pickup_place'], data['destination_place'], data['type'], data['licence_plate'], data["dispatcher"], data['life_time']
                )
                message = self.bot.edit_message_text(chat_id=user["chat_id"], message_id=message_id, text=string)
                logger.info(f"{user['chat_id']} Edited message successfully {message_id}, life_time = {data['life_time']}")
                break
            except Exception as err:
                logger.error(f"{user['chat_id']} Error while editing message {err = }")
                time.sleep(self.delay)

    def send_vanishing_message(self, object_data):
        def vanishing_part(message_id):
            try:
                while data["life_time"] > 0:
                    time.sleep(step_time)
                    data["life_time"] -= step_time
                    self.edit_message(data, user, message_id)
            except Exception as err:
                logger.error(f"{user['chat_id']} Error while processing editing message, {err = }")

            self.remove_message(user, message_id)

        try:
            data, user, life_time, step_time = object_data
            data = data.copy()
            logger.info(f"{user['chat_id']} Got data object {object_data}")
        except Exception as err:
            logger.error(f"Error while getting data from object, {object_data = }")

        try:
            if not user["is_thread"] and user["rule"] == "admin":
                logger.info(f"Cant send message to user {user}")
                return
            elif user["rule"] == "driver" and data["licence_plate"] != user["taxi_id"]:
                logger.info(f"Cant send message to user {user}")
                return
        except Exception as err:
            logger.error(f"{user['chat_id']} Error while checking user, {err = }")

        message = self.send_message(data, user)
        Thread(target=vanishing_part, args=(message.message_id,)).start()

    def start_order_sender(self):
        def start():
            while True:
                for i, order in enumerate(self.orders.copy()):
                    try:
                        del self.orders[i]
                    except Exception as err:
                        logger.error("Error while deleting order")

                    logger.info(f"Sending order {order}")
                    pool = self.create_pool(sending_message_threads)

                    try:
                        data = [[order, self.users[user], 3, 10] for user in self.users]
                        logger.info(f"Created order data object, {data = }")
                    except Exception as err:
                        logger.error(f"Error while creating data object {err = }")

                    try:
                        pool.map(self.send_vanishing_message, data)
                    except Exception as err:
                        logger.error(f"Error while mapping {pool = }, {err = }")

                time.sleep(.3)

        thread = Thread(target=start)
        thread.start()

    def update(self):
        delay = 60
        temp_time = datetime.now() + timedelta(minutes=delay)
        while True:
            if temp_time < datetime.now():
                temp_time = datetime.now() + timedelta(minutes=delay)
                log_file = f"./logs/logs_{temp_time.strftime('%m.%d.%Y-%H.%M')}.log"
                logger.info(f"Changed log file to {log_file}")
                try:
                    formatter = Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
                    handler = FileHandler(log_file, "w+", "utf-8")
                    handler.setFormatter(formatter)
                    logger.handlers[0] = handler
                except Exception as err:
                    print(err)
                    logger.error(f"cant change log file to new, {err = }")

            for dispatcher in self.dispatchers:
                self.orders.extend(dispatcher.fetch_orders())
            time.sleep(.35)

    def start_parsers(self):
        def start():
            for dispatcher in self.dispatchers:
                dispatcher.start()

            self.update()

        thread = Thread(target=start)
        thread.start()

    @staticmethod
    def create_pool(threads):
        try:
            pool = Pool(threads)
            logger.info(f"Created pool, {threads = }")
            return pool
        except Exception as err:
            logger.error(f"Error while creating pool, {err = }")
