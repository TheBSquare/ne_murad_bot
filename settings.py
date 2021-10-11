import os
import logging.config

root_path = os.getcwd()

logging.config.fileConfig('logging.conf')
logger = logging.getLogger("app")

token = "1867537649:AAG-1ZsBDzcOtpHVgOadjua4KUK3G_Sq9CU"
logs_file_change_delay = 30
parser_update_delay = 0.1
parsing_threads = 5
sending_message_threads = 1

driver_type = {
    "1": "chromedriver_win.exe",
    "2": "chromedriver_linux"
}["1"]
