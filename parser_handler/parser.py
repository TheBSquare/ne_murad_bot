import subprocess
import time
from datetime import datetime, timedelta

from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import Chrome, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from settings import root_path, logger, driver_type
import os
from bs4 import BeautifulSoup


class Parser:
    options = Options()
    options.add_argument("--headless")
    options.add_argument("--enable-javascript")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-setuid-sandbox")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--window-size=1920x1080")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-plugins-discovery")
    options.add_argument("--disable-gpu")

    main_link = "https://lk.taximeter.yandex.ru/report/company/"
    parse_link = "https://lk.taximeter.yandex.ru/report/company/"

    driver_path = f"{os.path.join(root_path, 'drivers', driver_type)}"

    def __init__(self, name, login, password, email, company_number):
        self.name = name
        self.username = login
        self.password = password
        self.reserve_email = email
        self.company_number = company_number

    def start(self):
        logger.info("Staring browser")
        try:
            subprocess.run([f"sudo chmod +x {self.driver_path}"], check=True)
        except Exception as err:
            logger.warning(f"{self.name}. Cant set chmod to driver, {err = }")

        self.driver = Chrome(executable_path=self.driver_path, options=self.options)
        logger.info(f"{self.name}. Getting page")
        self.driver.get(self.main_link)
        self.wait = WebDriverWait(self.driver, 30, poll_frequency=.3, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        logger.info(f"{self.name}. Checking if logged in")
        self.login()
        logger.info(f"{self.name}. Logged in")
        self.update_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#btn-update")))

    def set_time_from_order(self, order, bound, delta):
        try:
            date_parts = order[2].split(".")
            created_time = f"{date_parts[0]}.{date_parts[1]}.20{date_parts[2]}T{order[3]}"
            date = datetime.strptime(created_time, "%d.%m.%YT%H:%M") - delta

            filter_name = {"lower": "datetime_start", "upper": "datetime_end"}

            self.set_element_value(filter_name[bound], date.strftime("%Y-%m-%dT%H:%M"))
        except Exception as err:
            logger.error(f"{self.name}. Error while setting date from order {date = }, {err = }")

    def login(self):
        if "login" in self.driver.current_url:
            try:
                try:
                    link = self.driver.find_element(By.CSS_SELECTOR, "form > div > a")
                    logger.info(f"{self.name}. Trying logging in")
                except Exception as err:
                    raise Exception("Companies")

                logger.info(f"{self.name}. Redirecting to {link.get_attribute('href')}")

                link.click()

                login_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='login']")))
                login_input.send_keys(self.username + Keys.ENTER)

                logger.info("Sending username")
                password_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='passwd']")))
                password_input.send_keys(self.password + Keys.ENTER)

                logger.info("Sending password")

                tries = 15
                passed_challenge = False
                while tries > 0:
                    logger.info(f"{self.name}. Authentication, {tries = }")
                    if "https://lk.taximeter.yandex.ru" in self.driver.current_url:
                        raise Exception("Companies")
                    elif not passed_challenge and "https://passport.yandex.ru/auth/challenge" in self.driver.current_url:
                        email_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='email']")))
                        email_input.send_keys(self.reserve_email + Keys.ENTER)
                        tries = 15
                        passed_challenge = True
                    time.sleep(.15)
                    tries -= 1

            except Exception as err:
                if self.company_number < 0:
                    logger.info(f"{self.name}. Patching website")
                    self.driver.execute_script('table1.datagrid({ url: "/report/items/company/" });')
                    logger.info(f"{self.name}. Updating page")
                    while True:
                        try:
                            self.update()
                            time.sleep(1)
                            break
                        except Exception as err:
                            logger.error(f"{self.name}. {err = }")

                elif "Companies" == str(err):
                    logger.info(f"{self.name}. Choosing company")

                    company_button = self.wait.until(EC.visibility_of_element_located(
                        (By.CSS_SELECTOR, f"form > button:nth-child({self.company_number})")
                    ))
                    logger.info(f"{self.name}. Choose company {company_button.text}")
                    company_button.click()

                    time.sleep(.3)

                    logger.info(f"{self.name}. Redirecting to {self.parse_link}")

                    self.driver.get(self.parse_link)

                    logger.info(f"{self.name}. Waiting till page be loaded")
                    self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.request-error")))
                    logger.info(f"{self.name}. Patching website")
                    self.driver.execute_script('table1.datagrid({ url: "/report/items/company/" });')
                    logger.info(f"{self.name}. Updating page")
                    while True:
                        try:
                            self.update()
                            time.sleep(1)
                            break
                        except Exception as err:
                            logger.error(f"{self.name}. {err = }")

    def check_error(self):
        try:
            wait = WebDriverWait(self.driver, .5, poll_frequency=.1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.request-error")))
                return False
            except Exception as err:
                return True
        except Exception as err:
            logger.error(f"{self.name}. Error while checking, {err = }")
            return True

    def get_orders(self):
        orders = []
        try:
            soup = BeautifulSoup(self.driver.page_source, "html.parser")
            for row in soup.select_one("div.datagrid-content").select_one("table").select("tr"):
                try:
                    if not row.get("data-guid") is None:
                        orders.append(row)
                except Exception as err:
                    logger.warning(f"{self.name}. Error while getting order, {err = }")
        except Exception as err:
            logger.error(f"{self.name}. Error while getting orders from page, {err = }")
        logger.info(f"{self.name}. Found {len(orders)} orders")
        return orders

    def update(self):
        for x in range(4):
            try:
                logger.info(f"{self.name}. Trying to update, try = {x}")
                self.wait = WebDriverWait(self.driver, 30, poll_frequency=.3, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
                self.update_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#btn-update")))
                self.update_button.click()
                logger.info(f"{self.name}. Updated successfully")
                time.sleep(.5)
                return True
            except Exception as err:
                pass
        logger.error(f"{self.name}. Cant update, some error with website")
        return False

    def set_element_value(self, filter_name, value):
        try:
            filter_ = {
                "datetime_start": self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#filter-datetime-start"))),
                "datetime_end": self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#filter-datetime-end"))),
                "filter_status": self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#filter-status"))),
                "date_field": self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#datefield"))),
                "payment": self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#payment"))),
            }.get(filter_name)

            if filter_ is None:
                raise Exception("No such filter")
            else:
                self.driver.execute_script("arguments[0].value=arguments[1]", filter_, value)
            logger.info(f"{self.name}. Set filter {filter_name} to value {value}")
        except Exception as err:
            logger.error(f"{self.name}. Got error while setting filter {filter_name} to {value = }")
            return

    def get_last_order(self):
        try:
            last_order = list(self.get_orders())[-1]
            try:
                string = last_order.text.replace('\n', '')
                logger.info(f"{self.name}. Found last order {string}")
                return [cell.text for cell in last_order.select("td")]
            except Exception as err:
                logger.error(f"{self.name}. Error while getting data from order, {err = }")
                return None
        except Exception as err:
            logger.error(f"{self.name}. Error while getting last order, {err = }")
            return None
