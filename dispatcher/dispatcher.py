import time
from datetime import timedelta, datetime
from multiprocessing.dummy import Pool
from threading import Thread

from parser_handler.parser import Parser
from settings import logger, parser_update_delay, parsing_threads, sending_message_threads


class Dispatcher:

    def __init__(self, name, username, password, email="none@gmail.com", company_number=2):
        self.name = name

        self.username = username
        self.password = password
        self.email = email
        self.parser = Parser(
            name=self.name, login=self.username,
            password=self.password, email=self.email,
            company_number=company_number
        )

        self.parsed_orders = set()
        self.orders = []
        self.parsing = False
        self.count = 0

    def start(self):
        thread = Thread(target=self.update)
        thread.start()

    def update(self):
        logger.info(f'{self.name}. Parser updater has been started.')
        self.prepare_parser()

        while True:
            try:
                if self.count == 0:
                    self.count = 10
                    self.update_time()
                else:
                    self.count -= 1

                if not self.parser.check_error() or not self.parser.update():
                    logger.info(f"{self.name}. Restarting bot, error with website or cookies")
                    try:
                        self.parser.driver.quit()
                    except Exception as err:
                        pass
                    self.prepare_parser()

                self.parsing = True
                self.process_orders()
                self.parsing = False

            except Exception as err:
                logger.error(f"{self.name}. Occurred some error while updating parser, {err = }")

            time.sleep(parser_update_delay)

    def update_time(self, wait=False):
        while True:
            last_order = self.parser.get_last_order()
            if not last_order is None:
                date_start = self.parser.set_time_from_order(last_order, "lower", timedelta(minutes=30))
                date_start = self.parser.set_time_from_order(last_order, "upper", timedelta(days=-3))
                return
            else:
                logger.error(f"Cant change datetime bounds, last order is None")

            if wait:
                logger.info(f"Waiting till first order appears")
                time.sleep(1)
                continue

            break
        logger.error(f"{self.name}. Got None order, cant set time")

    def prepare_parser(self):
        self.parser.start()

        for filter_ in [
            ["filter_status", "0"],
            ["date_field", "0"],
            ["payment", ""]
        ]: self.parser.set_element_value(*filter_)
        self.update_time(wait=True)
        self.parser.update()
        time.sleep(1)
        self.mark_old_orders()

    def process_orders(self):
        def parse_order(order_element):
            nonlocal count

            try:
                order_id = order_element.get("data-guid")
            except Exception as err:
                logger.error(f"{self.name}. Error with order, {err = }")

            if order_id is None:
                return
            elif order_id in self.parsed_orders:
                return
            else:
                try:
                    cells = [cell.text for cell in order_element.select("td")]

                    if cells[9] == "" or cells[15] == "":
                        return

                    self.parsed_orders.add(order_id)
                    date_parts = cells[2].split(".")
                    created_time = f"{date_parts[0]}.{date_parts[1]}.20{date_parts[2]}T{cells[3]}"
                except Exception as err:
                    logger.error(f"{self.name}. Error while parsing order, {err = }")
                    return

                self.orders.append({
                    "dispatcher": self.name,
                    "time": created_time,
                    "licence_plate": cells[10],
                    "pickup_place": cells[8],
                    "destination_place": cells[9],
                    "type": cells[15],
                    "life_time": 30
                })
                count += 1

        count = 0
        orders = self.parser.get_orders()
        pool = self.create_pool(parsing_threads)
        try:
            pool.map(parse_order, orders)
            logger.info(f"{self.name}. Added {count} orders")
        except Exception as err:
            logger.error(f"{self.name}. Error while mapping {err = }")

    def mark_old_orders(self):
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

        orders = self.parser.get_orders()
        pool = self.create_pool(parsing_threads)
        try:
            pool.map(parse_order, orders)
        except Exception as err:
            logger.error(f"Error while mapping {err = }")

        logger.info(f"Marked {len(self.parsed_orders)} orders")

    def fetch_orders(self):
        try:
            orders = self.orders[::]
            if not self.parsing:
                try:
                    self.orders = []
                except Exception as err:
                    logger.error(f"{self.name}. Cant clear orders, {err = }")

            count = len(orders)
            if count > 0:
                logger.info(f"{self.name}. Fetch {len(orders)}")
            return orders
        except Exception as err:
            logger.error(f"{self.name}. Error while fetching orders, {err = }")
            return []

    @staticmethod
    def create_pool(threads):
        try:
            pool = Pool(threads)
            logger.info(f"Created pool, {threads = }")
            return pool
        except Exception as err:
            logger.error(f"Error while creating pool, {err = }")
