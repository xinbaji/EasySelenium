import json
import os
import ctypes
import logging
import re
import sys
from datetime import datetime
from selenium.common import ScreenshotException
from selenium.common.exceptions import TimeoutException,NoSuchDriverException,NoSuchElementException
from selenium.webdriver import Chrome, ChromeOptions
from selenium.webdriver import Edge
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webdriver import WebDriver

from selenium.webdriver.common.by import By
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Log:
    """统一日志类：彩色控制台输出 + 可选项目级日志文件。

    用法:
        log = Log("app")                 # INFO 级别
        log = Log("app", mode="d")       # DEBUG 级别
        log.logger.info("任务完成")
        log.logger.error("出错")      
    """

    # ============================================================
    #  颜色 / 样式
    # ============================================================
    class C:
        RST = "\033[0m"
        DIM = "\033[2m"
        RED = "\033[31m"
        GRN = "\033[32m"
        YLW = "\033[33m"
        BLU = "\033[34m"
        CYN = "\033[36m"
        B_RED = "\033[91m"
        B_YLW = "\033[93m"

    LEVEL_COLOR = {
        "DEBUG": C.CYN,
        "INFO": C.GRN,
        "WARNING": C.B_YLW,
        "ERROR": C.RED,
        "CRITICAL": C.B_RED,
    }

    _CJK_PATTERN = re.compile(
        r"[\u3400-\u4dbf"      # 汉字 扩展A
        r"\u4e00-\u9fff"       # 汉字 基本区
        r"\uf900-\ufaff"       # 汉字 兼容区
        r"\u3000-\u303f"       # 中文标点 / CJK 符号
        r"\uff00-\uffef"       # 全角数字/字母/符号
        r"\u3040-\u309f"       # 平假名
        r"\u30a0-\u30ff"       # 片假名
        r"\uff66-\uff9d"       # 半角片假名
        r"\uac00-\ud7a3"       # 韩文音节
        r"\u3130-\u318f"       # 韩文兼容字母
        r"\u1100-\u11ff]"      # 韩文 Jamo
    )

    _PROJECT_FH = None  # 项目级 FileHandler

    # ============================================================
    #  初始化（类加载时启用 Windows ANSI 颜色）
    # ============================================================
    @classmethod
    def _enable_ansi(cls) -> None:
        """启用 Windows 10+ 控制台 ANSI 转义序列"""
        if sys.platform == "win32":
            try:
                kernel32 = ctypes.windll.kernel32
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
            except Exception:
                pass

    

    # ============================================================
    #  工具方法
    # ============================================================
    @staticmethod
    def get_app_root() -> str:
        """返回 EXE / py 文件所在的真实目录（兼容 Nuitka/PyInstaller onefile）"""
        argv0 = os.path.abspath(sys.argv[0])
        base = os.path.basename(argv0).lower()
        if base in ("python.exe", "pythonw.exe", "python3.exe"):
            return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        return os.path.dirname(argv0)

    @staticmethod
    def count_cjk(text: str) -> int:
        """统计：汉字 + 中文标点 + 全角字符 + 日文假名 + 韩文 的个数"""
        return len(Log._CJK_PATTERN.findall(text))

    # ============================================================
    #  格式化器
    # ============================================================
    class ConsoleFormatter(logging.Formatter):
        """控制台格式: [LEVEL] message │ HH:MM:SS filename:lineno"""

        def format(self, record: logging.LogRecord) -> str:
            color = Log.LEVEL_COLOR.get(record.levelname, Log.C.RST)
            ts = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
            lv = f"{record.levelname:<5}"
            loc = f"{record.filename}:{record.lineno}"

            left = f"{color}[{lv}]{Log.C.RST} {record.getMessage()}"
            right = f"{Log.C.DIM}{ts}  {loc}{Log.C.RST}"

            left_vis = len(f"[{record.levelname:<5}] {record.getMessage()}") + Log.count_cjk(
                record.getMessage()
            )
            pad = max(2, 59 - left_vis)
            msg = f"{left}{' ' * pad}│ {right}"

            if record.exc_info and record.exc_info[0]:
                msg += "\n" + self.formatException(record.exc_info)
            return msg

    _FILE_FMT = logging.Formatter(
        "%(asctime)s | %(levelname)-5s | %(filename)s:%(lineno)d | %(message)s"
    )

    @classmethod
    def setup_project_log(cls,path: str = "log/project.log") -> None:
        """初始化项目级日志文件（覆盖写）。

        在程序启动 / 所有 Log 实例创建前调用一次即可，
        之后各 logger 通过 propagate 传播到 root，统一写入该文件。

        :param path: 日志文件路径，默认 log/project.log
        """
        # 防止重复初始化：已存在则先关闭并移除旧 handler
        if cls._PROJECT_FH is not None:
            try:
                logging.root.removeHandler(cls._PROJECT_FH)
                cls._PROJECT_FH.close()
            except Exception:
                pass


        cls._PROJECT_FH = logging.FileHandler(path, mode="w", encoding="utf-8")
        cls._PROJECT_FH.setLevel(logging.DEBUG)      # 文件记录全级别日志
        cls._PROJECT_FH.setFormatter(cls._FILE_FMT)  # 复用项目文件格式
        logging.root.addHandler(cls._PROJECT_FH)

    # ============================================================
    #  实例：控制台彩色 logger
    # ============================================================
    def __init__(self, log_name: str, mode: str = "d") -> None:
        Log.setup_project_log() 
        Log._enable_ansi()
        console_level = logging.DEBUG if mode == "d" else logging.INFO

        self.logger = logging.getLogger(log_name)
        self.logger.setLevel(logging.DEBUG)  # 始终生成全级别日志，传播到 root→文件
        self.logger.propagate = True         # 向上传播到 root（统一文件输出）

        # 防止重复添加 handler（多次实例化同一 logger 名时）
        if self.logger.handlers:
            self.logger.handlers.clear()

        ch = logging.StreamHandler(sys.stdout)
        ch.setLevel(console_level)           # 控制台按 mode 过滤显示级别
        ch.setFormatter(self.ConsoleFormatter())
        self.logger.addHandler(ch)

    # =========================================================

def only_chained_calls(func):
    def wrapper(self, *args, **kwargs):
        if self.temp_element is not None:
            result = func(self, *args, **kwargs)
            self.temp_element = None
            self.temp_locator = None
            return result
        else:
            raise NoSuchElementException("被处理的元素不存在")

    return wrapper

SETTING_PATH = "data/setting.json"




class Driver:

    def __init__(self) -> None:
        dirs=["data","data\\download","data\\env","data\\screenshots","log"]
        
        for dir in dirs:
            if not os.path.exists(dir):
                os.makedirs(dir,exist_ok=True)
        self.log = Log("EasySelenium", "d").logger
        
        __driver, __driver_options = self.find_available_browser()
        self.download_location = os.path.join(os.getcwd(), "data","download")
        self.userdata_dir = os.path.join(os.getcwd(), "data","env")
        self.prefs = {"download.default_directory": self.download_location}
        self.timeout_seconds = 60
        self.temp_element:WebElement = None
        self.temp_locator:tuple = None
        
        __driver_options.add_experimental_option("prefs", self.prefs)
        __driver_options.add_experimental_option("detach", False)
        __driver_options.add_argument("--user-data-dir=" + self.userdata_dir)
        __driver_options.add_experimental_option("excludeSwitches", ["enable-logging", "enable-automation"])
        __driver_options.add_argument("--log-level=3")
        
        self.driver:WebDriver = __driver(options=__driver_options)
        self.driver.maximize_window()
        self.driver.set_page_load_timeout(self.timeout_seconds)
        self.log.info("EasySelenium 初始化完成")
        
        
    def find_available_browser(self):
        """寻找可用浏览器，优先读取 setting.json，没有则自动探测并持久化。

        :return: (browser_class, options_obj) 如 (Chrome, ChromeOptions())
        :raises NoSuchDriverException: 无可用浏览器
        """
        # 1. 先读 setting.json
        if os.path.exists(SETTING_PATH):
            try:
                with open(SETTING_PATH, "r", encoding="utf-8") as f:
                    setting = json.load(f)
                browser = setting.get("browser", "")
                if browser == "chrome":
                    return Chrome, ChromeOptions()
                elif browser == "edge":
                    return Edge, EdgeOptions()
            except (json.JSONDecodeError, KeyError):
                pass

        # 2. 没有或无效，自动探测
        for name, cls in [("chrome", Chrome), ("edge", Edge)]:
            try:
                driver = cls()
                driver.quit()
            except Exception:
                continue
            else:
                with open(SETTING_PATH, "w", encoding="utf-8") as f:
                    json.dump({"browser": name}, f, indent=2)
                if cls == Chrome:
                    options = ChromeOptions()
                else:
                    options = EdgeOptions()
                return cls,options

        raise NoSuchDriverException("无支持的浏览器，请安装 Edge 或 Chrome。")

    def get(self, url):
        self.driver.get(url)
        self.log.info("正在打开页面："+url)

    def wait(self, condition, path: str, timeout: float = -1, mode: str = "appear"):
        """等待元素出现或消失。

        :param condition: EC 条件，如 EC.presence_of_element_located、EC.element_to_be_clickable 等
        :param path:      元素路径，以 / 开头为 XPath，否则为 CSS Selector
        :param timeout:   超时秒数，默认使用 self.timeout_seconds
        :param mode:      "appear"(默认) 等待元素出现；"disappear" 等待元素消失
        :return:          self（支持链式调用）
        """
        if timeout < 0:
            timeout = self.timeout_seconds

        if mode not in ("appear", "disappear"):
            raise ValueError("mode 只能是 'appear' 或 'disappear'")

        if path.startswith("/"):
            locator = (By.XPATH, path)
        else:
            locator = (By.CSS_SELECTOR, path)

        self.log.debug(f"正在寻找元素: {path}  条件: {condition.__name__}  模式: {mode}  等待时间(秒): {timeout}")
        try:
            if mode == "appear":
                element = WebDriverWait(self.driver, timeout).until(condition(locator))
            else:
                # 等待元素消失：元素不在 DOM / 不可见 / 不可点击即返回
                WebDriverWait(self.driver, timeout).until_not(condition(locator))
                element = None
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
        self.log.info("元素已移除："+str(self.temp_locator))

    @only_chained_calls
    def click(self):
        self.temp_element.click()
        self.log.info("元素已点击："+str(self.temp_locator))

    @only_chained_calls
    def send_keys(self, keys):
        self.temp_element.send_keys(keys)
        self.log.info("按键已输入："+keys+" 到 "+str(self.temp_locator))
    @only_chained_calls
    def get_attribute(self, attr):
        return self.temp_element.get_attribute(attr)

    @only_chained_calls
    def get_text(self):
        return self.temp_element.text

    @only_chained_calls
    def force_click(self):
        self.driver.execute_script("arguments[0].click()", self.temp_element)
        self.log.info("元素已点击："+str(self.temp_locator))

    @only_chained_calls
    def clear(self):
        self.temp_element.clear()
    @only_chained_calls
    def screenshot(self):
        
        filename=datetime.now().strftime("%Y-%m-%d-%H-%M-%S-%f")[:-4]+".png"
        filepath=os.path.join(os.getcwd(),"data","screenshots",filename).replace("\\","/")
        self.log.debug("element: "+str(self.temp_locator)+" save_path: "+filepath)
        result=self.temp_element.screenshot(filepath)
        return result
    def switch_to_last_window(self):
        self.driver.switch_to.window(self.driver.window_handles[-1])

    def close(self):
        try:
            self.driver.close()
        except Exception:
            pass

    def quit(self):
        try:
            self.driver.quit()
        except Exception:
            pass

    def refresh(self):
        self.driver.refresh()

    def get_page_source(self):
        return self.driver.page_source

    def switch_to_default_frame(self):
        try:
            self.driver.switch_to.default_content()
        except Exception as e:
            self.log.error("错误：" + str(e))

if __name__ == "__main__":
    driver = Driver()
    driver.get("http://www.qq.com")
    driver.wait(EC.presence_of_element_located, "/html/body").screenshot()
    driver.quit()

