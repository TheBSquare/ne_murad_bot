import random
import time
from datetime import datetime, timedelta
from threading import Thread

from selenium.webdriver.common.by import By

from settings import logger
from multiprocessing.dummy import Pool


class OrderSender:
    parsed_orders = set()
    message_skeleton = "Адрес (от): {}\n" \
                       "Адрес (куда): {}\n" \
                       "Способ оплаты: {}\n" \
                       "Номер машины: {}\n" \
                       "Сообщение удалиться через: {} секунд"

    tries = 3
    delay = 1
    sending_messages_threads = 1
    parsing_threads = 10

    def __init__(self, bot, parser):
        self.bot = bot
        self.parser = parser

    def send_message(self, data, user, is_format=True):
        for x in range(self.tries):
            logger.info(f"Trying to send message, try = {x}")
            try:
                string = self.message_skeleton.format(
                    data['pickup_place'], data['destination_place'], data['type'], data['licence_plate'], data['life_time']) \
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
                    data['pickup_place'], data['destination_place'], data['type'], data['licence_plate'], data['life_time']
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
            if not user["is_thread"] or user["rule"] != "admin" and data["licence_plate"] != user["taxi_id"]:
                logger.info(f"Cant send message to user {user}")
                return
        except Exception as err:
            logger.error(f"{user['chat_id']} Error while checking user, {err = }")

        message = self.send_message(data, user)
        Thread(target=vanishing_part, args=(message.message_id, )).start()

    @staticmethod
    def create_pool(threads):
        try:
            pool = Pool(threads)
            logger.info(f"Created pool, {threads = }")
            return pool
        except Exception as err:
            logger.error(f"Error while creating pool, {err = }")

    def send_orders(self, users, orders):

        for order in orders:
            logger.info(f"Sending order {order}")
            pool = self.create_pool(self.sending_messages_threads)

            try:
                data = [[order, users[user], 3, 10] for user in users]
                logger.info(f"Created order data object, {data = }")
            except Exception as err:
                logger.error(f"Error while creating data object {err = }")

            try:
                pool.map(self.send_vanishing_message, data)
            except Exception as err:
                logger.error(f"Error while mapping {pool = }, {err = }")

    def mark_old_orders(self, orders):
        def parse_order(order_element):
            try:
                order_id = order_element.get("data-guid")
            except Exception as err:
                logger.error(f"Error with order, {err = }")

            try:
                if order_id is None:
                    return
                elif order_id in self.parsed_orders:
                    try:
                        logger.info(f"Order has already been parsed {order_element.text}")
                    except Exception as err:
                        logger.error(f"Error while getting data from order {err = }")
                    return
                else:
                    self.parsed_orders.add(order_id)
            except Exception as err:
                logger.error(f"Error while parsing order, {err = }")
        pool = self.create_pool(self.parsing_threads)
        try:
            pool.map(parse_order, orders)
        except Exception as err:
            logger.error(f"Error while mapping {err = }")

        logger.info(f"Marked {len(self.parsed_orders)} orders")

    def process_orders(self, users, orders):
        def parse_order(order_element):
            try:
                order_id = order_element.get("data-guid")
            except Exception as err:
                logger.error(f"Error with order, {err = }")

            try:
                if order_id is None:
                    return
                elif order_id in self.parsed_orders:
                    try:
                        string = order_element.text.replace("\n", "")
                        logger.info(f"Order has already been parsed {string}")
                    except Exception as err:
                        logger.error(f"Error while getting data from order {err = }")
                    return
                else:
                    self.parsed_orders.add(order_id)

                    try:
                        cells = [cell.text for cell in order_element.select("td")]
                        date_parts = cells[2].split(".")
                        created_time = f"{date_parts[0]}.{date_parts[1]}.20{date_parts[2]}T{cells[3]}"
                    except Exception as err:
                        logger.error(f"Error while parsing order, {err = }")
                        return

                    try:
                        self.last_datetime = datetime.strptime(created_time, "%d.%m.%YT%H:%M") - timedelta(minutes=35)
                    except Exception as err:
                        logger.error(f"Error while creating last_datetime {err = }")

                    parsed_orders.append({
                        "time": created_time,
                        "licence_plate": cells[10],
                        "pickup_place": cells[8],
                        "destination_place": cells[9],
                        "type": cells[15],
                        "life_time": 30
                    })
            except Exception as err:
                logger.error(f"Error while parsing order, {err = }")

        parsed_orders = []

        pool = self.create_pool(self.parsing_threads)
        try:
            pool.map(parse_order, orders)
        except Exception as err:
            logger.error(f"Error while mapping {err = }")

        logger.info(f"Parsed {len(parsed_orders)} orders")
        return parsed_orders
