import logging
import os
from time import strftime,localtime

from selenium.common.exceptions import TimeoutException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver import Edge
from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

class BaseEasySeleniumException(Exception):
    def __init__(self,msg):
        self.msg=msg
        Log("Error").logger.error(msg)

    def __str__(self):
        return self.msg
class NoSuchDriverException(BaseEasySeleniumException):...
class PathInvalid(BaseEasySeleniumException):...
class NoSuchCaseException(BaseEasySeleniumException):...
class NoSuchElement(BaseEasySeleniumException):...

class Log:
    def __init__(self, log_name, mode: str = "i") -> None:
        log_level = logging.DEBUG if mode == "d" else logging.INFO
        log_file_name = strftime("%Y-%m-%d", localtime())
        if not os.path.exists("./log/" + log_file_name + ".txt"):

            os.makedirs("../log", exist_ok=True)
            with open("./log/" + log_file_name + ".txt", "w") as f:
                f.write("*********EasySelenium Log************\n")
                f.close()
        handler = logging.FileHandler("./log/" + log_file_name + ".txt")
        handler.setLevel(level=logging.DEBUG)
        formatter = logging.Formatter(
            "%(asctime)s - %(funcName)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        console = logging.StreamHandler()
        console.setLevel(log_level)
        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(level=log_level)
        self.logger.addHandler(handler)
        self.logger.addHandler(console)

def only_chained_calls(func):
    def wrapper(self, *args, **kwargs):
        if self.temp_element is not None:
            result = func(self, *args, **kwargs)
            self.temp_element = None
            self.temp_locator = None
            return result
        else:
            raise NoSuchElement("被处理的元素不存在")

    return wrapper

class Driver:

    def __init__(self) -> None:

        self.log = Log("EasySelenium", "d").logger

        if self._driver_isavailable(target_driver=Chrome):
            __driver = Chrome
            options = ChromeOptions()
            self.log.debug("chrome")
        elif self._driver_isavailable(target_driver=Edge):
            __driver = Edge
            options = EdgeOptions()
            self.log.debug("edge")
        else:
            self.log.error("无支持的浏览器，安装edge或chrome。")
            raise NoSuchDriverException("无支持的浏览器，安装edge或chrome。")

        self.download_location = os.path.join(os.getcwd(), "temp")
        self.prefs = {"download.default_directory": os.path.join(os.getcwd(), "temp")}
        self.userdata_dir = os.path.join(os.getcwd(), "env")
        self.timeout_seconds = 12
        self.temp_element = None
        self.temp_locator = None

        options.add_experimental_option("prefs", self.prefs)
        options.add_experimental_option("detach", True)
        options.add_argument("--user-data-dir=" + self.userdata_dir)
        options.add_argument("--remote-debugging-port=9222")
        options.add_experimental_option("excludeSwitches", ["enable-logging"])
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_argument("log-level=3")
        self.driver = __driver(options=options)
        self.driver.set_page_load_timeout(10)

    def _driver_isavailable(self, target_driver) -> bool:
        try:
            __driver = target_driver()
        except Exception as e:
            self.log.error(e)
            return False
        else:
            __driver.quit()
            return True

    def get(self, url):
        self.driver.get(url)

    def wait(self, case: str, path: str, target_string="", timeout=-1):
        case_dict = {
            "visible": EC.presence_of_element_located,
            "clickable": EC.element_to_be_clickable,
            "iframe_available": EC.frame_to_be_available_and_switch_to_it,
            "string_visible": EC.text_to_be_present_in_element,
        }
        if timeout == -1:
            timeout = self.timeout_seconds
        if path[0] == "#":
            locator = (By.CSS_SELECTOR, path)
        elif path[0] == "/":
            locator = (By.XPATH, path)
        else:
            raise PathInvalid("非法的CSS或XPATH格式 Path: " + path)

        if case not in case_dict.keys():
            raise NoSuchCaseException("case错误，可用case列表: " + str(case_dict.keys()))

        for key, value in case_dict.items():
            if case == key:
                case_handler = value
                case_handler_value = locator
                break

        if case_handler == EC.text_to_be_present_in_element:
            case_handler_value = (locator, target_string)

        self.driver.implicitly_wait(timeout)

        self.log.info("正在寻找元素: " + str(path) + " 寻找成功条件: " + str(case) + " 等待时间(秒): " + str(timeout))
        try:
            element = WebDriverWait(self.driver, timeout).until(case_handler(case_handler_value))
        except TimeoutException as e:
            self.log.error("等待元素超时")
            raise e
        else:
            self.temp_element = element
            self.temp_locator = locator
        return self

    @only_chained_calls
    def remove(self):
        self.driver.execute_script("document.querySelector('" + self.temp_element + "').remove()")

    @only_chained_calls
    def click(self):
        self.temp_element.click()

    @only_chained_calls
    def send_keys(self, keys):
        self.temp_element.send_keys(keys)

    @only_chained_calls
    def get_attribute(self, attr):
        return self.temp_element.get_attribute(attr)

    @only_chained_calls
    def get_text(self):
        return self.temp_element.text

    @only_chained_calls
    def force_click(self):
        self.driver.execute_script("arguments[0].click()", self.temp_element)

    def switch_to_last_window(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def close(self):
        self.driver.close()

    def refresh(self):
        self.driver.refresh()

    def get_page_source(self):
        return self.driver.page_source

    def switch_to_default_frame(self):
        try:
            self.driver.switch_to.default_content()
        except Exception as e:
            self.log.error("错误：" + str(e))



