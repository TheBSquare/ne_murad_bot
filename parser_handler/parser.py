import time
from selenium.common.exceptions import ElementNotVisibleException, ElementNotSelectableException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver import Chrome, Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support import expected_conditions as EC
from settings import root_path
import os


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

    username = "taxinaws"
    password = "newpar123456"
    reserve_email = "prime777@bk.ru"

    driver_type = {
        "1": "chromedriver_win.exe",
        "2": "chromedriver_linux"
    }[input("1. chromedriver_win.exe\n2. chromedriver_linux\nВвод: ")]
    # }[input("Drivers\n1. chromedriver_win.exe\n2. chromedriver_linux\nEnter the number of the driver: ")]
    driver_path = f"{os.path.join(root_path, driver_type)}"

    def start(self):
        print("starting browser")
        os.system(f"sudo chmod +x {self.driver_path}")
        self.driver = Chrome(executable_path=self.driver_path, options=self.options)
        print("getting page")
        self.driver.get(self.main_link)

        self.wait = WebDriverWait(self.driver, 30, poll_frequency=.3, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        print("checking if logged in")
        self.login()
        print("Logged in")
        self.update_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#btn-update")))

    def login(self):
        if "login" in self.driver.current_url:
            try:
                try:
                    link = self.driver.find_element(By.CSS_SELECTOR, "form > div > a")
                    print("Trying logging in")
                except Exception as err:
                    raise Exception("Companies")

                link.click()
                print("Redirecting")
                login_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='login']")))
                login_input.send_keys(self.username + Keys.ENTER)
                print("Sending username")
                password_input = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "input[name='passwd']")))
                password_input.send_keys(self.password + Keys.ENTER)
                print("Sending password")
                print(f"Waiting to be logged in")
                tries = 15
                passed_challenge = False
                while tries > 0:
                    print(self.driver.current_url)
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
                    print("Choosing company")
                    company_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "form > button:nth-child(2)")))
                    print(f"Chose {company_button.text}")
                    company_button.click()
                    time.sleep(.5)
                    print(f"Redirecting to {self.parse_link}")
                    self.driver.get(self.parse_link)
                    print(f"Waiting till page be loaded")
                    self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.request-error")))
                    print(f"Patching page")
                    self.driver.execute_script('table1.datagrid({ url: "/report/items/company/" });')
                    print(f"Updating page")
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
        wait = WebDriverWait(self.driver, .5, poll_frequency=.1, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        try:
            wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "div.request-error")))
            return False
        except Exception as err:
            return True

    def get_orders(self):
        orders = []
        try:
            for row in self.driver.find_elements(By.CSS_SELECTOR, "div.datagrid-content > table > tbody > tr"):
                try:
                    class_ = row.get_attribute("class")
                    if row.get_attribute("data-guid") is None or class_ is None or "group" in class_:
                        continue
                    orders.append(row)
                except Exception as err:
                    raise err
        except Exception as err:
            pass
        return orders

    def update(self):
        self.wait = WebDriverWait(self.driver, 30, poll_frequency=.3, ignored_exceptions=[ElementNotVisibleException, ElementNotSelectableException])
        self.update_button = self.wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR, "#btn-update")))
        self.update_button.click()

    def check_logged_in(self):
        if "login" in self.driver.current_url:
            print("Need to be logged in!")
            raise Exception("Not Logged in!")

    def set_element_value(self, filter_name, value):
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

    def get_last_order(self):
        last_order = list(self.get_orders())[-1]
        return [cell.text for cell in last_order.find_elements(By.CSS_SELECTOR, "td")]
