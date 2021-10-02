import subprocess
import time
from datetime import datetime, timedelta

from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import Chrome, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from settings import root_path, logger, login, password, company_number, email, driver_type
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

    username = login
    password = password
    reserve_email = email

    # }[input("Drivers\n1. chromedriver_win.exe\n2. chromedriver_linux\nEnter the number of the driver: ")]
    driver_path = f"{os.path.join(root_path, driver_type)}"

    def start(self):
        logger.info("Staring browser")
        try:
            subprocess.run([f"sudo chmod +x {self.driver_path}"], check=True)
        except Exception as err:
            logger.warning(f"Cant set chmod to driver, {err = }")

        self.driver = Chrome(executable_path=self.driver_path, options=self.options)
        logger.info("Getting page")
        self.driver.get(self.main_link)
        self.wait = WebDriverWait(self.driver, 30, poll_frequency=.3, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        logger.info("Checking if logged in")
        self.login()
        logger.info("Logged in")
        self.update_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#btn-update")))

    def set_time_from_order(self, order, bound, delta):
        try:
            date_parts = order[2].split(".")
            created_time = f"{date_parts[0]}.{date_parts[1]}.20{date_parts[2]}T{order[3]}"
            date = datetime.strptime(created_time, "%d.%m.%YT%H:%M") - delta

            filter_name = {"lower": "datetime_start", "upper": "datetime_end"}

            self.set_element_value(filter_name[bound], date.strftime("%Y-%m-%dT%H:%M"))
        except Exception as err:
            logger.error(f"Error while setting date from order {date = }, {err = }")

    def login(self):
        if "login" in self.driver.current_url:
            try:
                try:
                    link = self.driver.find_element(By.CSS_SELECTOR, "form > div > a")
                    logger.info("Trying logging in")
                except Exception as err:
                    raise Exception("Companies")

                logger.info(f"Redirecting to {link.get_attribute('href')}")

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
                    logger.info(f"Authentication, {tries = }")
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
                if "Companies" == str(err):
                    logger.info("Choosing company")

                    company_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, f"form > button:nth-child({company_number})")))
                    logger.info(f"Choose company {company_button.text}")
                    company_button.click()

                    time.sleep(.3)

                    logger.info(f"Redirecting to {self.parse_link}")

                    self.driver.get(self.parse_link)

                    logger.info(f"Waiting till page be loaded")
                    self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.request-error")))
                    logger.info(f"Patching website")
                    self.driver.execute_script('table1.datagrid({ url: "/report/items/company/" });')
                    logger.info(f"Updating page")
                    while True:
                        try:
                            self.update()
                            time.sleep(1)
                            break
                        except Exception as err:
                            print(str(err).replace("\n", ""))

                else:
                    raise Exception(err)

    def check_error(self):
        try:
            wait = WebDriverWait(self.driver, .5, poll_frequency=.1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
            try:
                wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.request-error")))
                return False
            except Exception as err:
                return True
        except Exception as err:
            logger.error(f"Error while checking, {err = }")
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
                    logger.warning(f"Error while getting order, {err = }")
        except Exception as err:
            logger.error(f"Error while getting orders from page, {err = }")
        logger.info(f"Found {len(orders)} orders")
        return orders

    def update(self):
        for x in range(4):
            try:
                logger.info(f"Trying to update, try = {x}")
                self.wait = WebDriverWait(self.driver, 30, poll_frequency=.3, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
                self.update_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#btn-update")))
                self.update_button.click()
                logger.info(f"Updated successfully")
                time.sleep(.5)
                return True
            except Exception as err:
                pass
        logger.error(f"Cant update, some error with website")
        return False

    def check_logged_in(self):
        if "login" in self.driver.current_url:
            print("Need to be logged in!")
            raise Exception("Not Logged in!")

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
            logger.info(f"Set filter {filter_name} to value {value}")
        except Exception as err:
            logger.error(f"Got error while setting filter {filter_name} to {value = }")
            return

    def get_last_order(self):
        try:
            last_order = list(self.get_orders())[-1]
            try:
                string = last_order.text.replace('\n', '')
                logger.info(f"Found last order {string}")
                return [cell.text for cell in last_order.select("td")]
            except Exception as err:
                logger.error(f"Error while getting data from order, {err = }")
        except Exception as err:
            logger.error(f"Error while getting last order, {err = }")
