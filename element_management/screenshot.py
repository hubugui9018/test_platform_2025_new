import os
import time
import datetime
from appium import webdriver
from django.conf import settings

from element_management.appium_utils import AppiumDriverManager


class ScreenshotManager:
    """管理创建文件夹与截图"""

    def __init__(self, driver=None):
        self.driver = driver
        self.base_folder = os.path.join(settings.BASE_DIR, 'static', 'screenshots')

    def create_screenshot_folder(self):
        """创建截图文件夹"""
        # 获取当前日期
        today = datetime.date.today().strftime("%Y-%m-%d")

        # 拼接总文件夹路径
        base_folder_path = os.path.join(self.base_folder, today)
        if not os.path.exists(base_folder_path):
            os.makedirs(base_folder_path)

        # 用例文件路径
        case_folder_path = os.path.join(base_folder_path,
                                        f"{time.strftime('%H')}-{time.strftime('%M')}-{time.strftime('%S')}")
        if not os.path.exists(case_folder_path):
            os.makedirs(case_folder_path)

        return case_folder_path

    def take_screenshot(self, case_folder_path):
        """进行截屏"""

        timestamp = int(time.time() * 1000)

        # 拼接路径与文件名
        screenshot_path = os.path.join(case_folder_path, f"{timestamp}.png")

        # 截屏
        self.driver.get_screenshot_as_file(screenshot_path)

        # 返回相对路径
        relative_screenshot_path = os.path.relpath(screenshot_path, settings.BASE_DIR)

        return relative_screenshot_path

    def capture_and_save(self, case_folder_path):

        # 执行截屏
        screenshot_path = self.take_screenshot(case_folder_path)

        return screenshot_path

# start_time = time.strftime("%Y%m%d%H%M%S", time.localtime())
# screenshot = ScreenshotManager(driver=None, test_case_name='test1', start_time=start_time)
# screenshot_path = screenshot.capture_and_save()
# print(screenshot_path)
