import os
import logging.config

root_path = os.getcwd()

logging.config.fileConfig('logging.conf')
logger = logging.getLogger("app")

login = ""
password = ""
email = ""
company_number = 0

driver_type = {
    "1": "chromedriver_win.exe",
    "2": "chromedriver_linux"
}["1"]
