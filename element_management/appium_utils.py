import threading

import numpy as np
import requests
import subprocess
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from device_management.models import Devices
from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from appium.options.android import UiAutomator2Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import easyocr
import cv2
import time
import json
import logging
from concurrent.futures import ThreadPoolExecutor

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class AppiumDriverPool:
    """维护appium驱动实例池"""
    _instance = None
    _lock = threading.RLock()  # 使用可重入锁，避免死锁
    _appium_server = None
    _appium_server_port = 4723

    def __new__(cls):

        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(AppiumDriverPool, cls).__new__(cls)
                    cls._instance.drivers = {}
                    cls._instance.last_used = {}
                    cls._instance.driver_locks = {}
                    cls._instance.max_idle_time = 300  # 空闲300s后清理
                    cls._instance.executor = ThreadPoolExecutor(max_workers=5)  # 最大维护5个线程

                    # 启动Appium服务
                    cls._instance._start_appium_server()

                    # 启动清理线程
                    cleanup_thread = threading.Thread(target=cls._instance._cleanup_idle_drivers, daemon=True)
                    cleanup_thread.start()

                    # 添加调试日志
                    logger.info("AppiumDriverPool初始化完成")

        return cls._instance

    def _start_appium_server(self):
        """启动Appium服务器"""
        try:
            logger.info("正在启动Appium服务...")
            # 检查Appium是否已经运行
            cmd = f'netstat -ano | findstr :{self._appium_server_port}'
            result = subprocess.run(cmd, shell=True, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            if result.stdout:
                lines = result.stdout.strip().splitlines()
                logger.info("appium服务端口已经打开，直接用")
            else:
                logger.info(f"未发现端口 {self._appium_server_port} 的占用情况,打开appium服务")
                subprocess.Popen(
                    "appium",
                    shell=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,  # 不打印日志
                )

            # 等待服务启动
            time.sleep(8)

            # 验证服务是否成功启动
            try:
                result = subprocess.check_output(f'netstat -ano | findstr :{self._appium_server_port}', shell=True, text=True)
                lines = result.strip().splitlines()
                logger.info(f"已经打开appium服务：{lines}")
            except Exception as e:
                logger.error(f"检查端口的空闲情况，1是空闲：{e}")

        except Exception as e:
            logger.error(f"启动Appium服务时出错: {str(e)}")

    def stop_appium_server(self):
        """停止Appium服务器"""
        if self._appium_server:
            logger.info("正在停止Appium服务...")
            self._appium_server.terminate()
            try:
                self._appium_server.wait(timeout=10)
                logger.info("Appium服务已停止")
            except subprocess.TimeoutExpired:
                self._appium_server.kill()
                logger.warning("Appium服务被强制终止")
            self._appium_server = None

    def __del__(self):
        self.stop_appium_server()

    def _get_driver_key(self, device_id, app_package):
        """为每个驱动创建唯一的键"""
        key = f"{device_id}_{app_package}"
        logger.debug(f"生成驱动键: {key}")
        return key

    def get_driver(self, device_id, device_type, device_version, app_package, app_activity):
        """获取现有驱动或创建新驱动"""
        driver_key = self._get_driver_key(device_id, app_package)

        # 添加日志以显示当前驱动池状态
        logger.debug(f"当前驱动池状态: {list(self.drivers.keys())}")

        with self._lock:
            # 如果不存在，为这个特定驱动创建一个锁
            if driver_key not in self.driver_locks:
                self.driver_locks[driver_key] = threading.RLock()

        # 获取这个特定驱动的锁
        with self.driver_locks[driver_key]:
            # 检查是否有现有的有效驱动
            if driver_key in self.drivers and self.drivers[driver_key] is not None:
                logger.info(f"检查驱动 {driver_key} 是否有效")
                try:
                    # 检查驱动是否仍然有效的更可靠方法
                    current_package = self.drivers[driver_key].current_package
                    logger.info(f"驱动 {driver_key} 当前应用包: {current_package}")

                    # 确保驱动正在运行预期的应用
                    if current_package and (current_package == app_package or app_package in current_package):
                        logger.info(f"复用现有驱动 {driver_key}")
                        self.last_used[driver_key] = time.time()
                        return self.drivers[driver_key]
                    else:
                        logger.warning(
                            f"驱动 {driver_key} 运行的应用不匹配，当前: {current_package}，预期: {app_package}")
                        self._close_driver(driver_key)
                except Exception as e:
                    logger.warning(f"驱动 {driver_key} 不再有效: {str(e)}")
                    self._close_driver(driver_key)

            # 创建新驱动
            try:
                logger.info(f"为 {driver_key} 创建新驱动")
                driver_manager = AppiumDriverManager(
                    device_id=device_id,
                    device_type=device_type,
                    device_version=device_version,
                    app_package=app_package,
                    app_activity=app_activity
                )

                # 确保创建驱动时不会超时
                try:
                    # 使用线程池提交任务
                    future = self.executor.submit(driver_manager.create_driver)
                    driver = future.result(timeout=60)  # 增加超时时间
                except TimeoutError:
                    logger.error(f"创建驱动 {driver_key} 超时")
                    raise

                # 验证驱动是否成功初始化
                if driver:
                    try:
                        # 确保驱动已正确启动
                        actual_package = driver.current_package
                        logger.info(f"驱动 {driver_key} 成功创建，当前应用: {actual_package}")
                    except Exception as e:
                        logger.error(f"驱动 {driver_key} 创建但验证失败: {str(e)}")
                        try:
                            driver.quit()
                        except:
                            pass
                        raise

                self.drivers[driver_key] = driver
                self.last_used[driver_key] = time.time()
                return driver
            except Exception as e:
                logger.error(f"为 {driver_key} 创建驱动失败: {str(e)}")
                raise

    def release_driver(self, device_id, app_package):
        """标记驱动不再使用"""
        driver_key = self._get_driver_key(device_id, app_package)

        with self._lock:
            if driver_key in self.drivers:
                self.last_used[driver_key] = time.time()
                logger.info(f"释放驱动 {driver_key}")
            else:
                logger.warning(f"尝试释放不存在的驱动 {driver_key}")

    def close_driver(self, device_id, app_package):
        """显式关闭驱动"""
        driver_key = self._get_driver_key(device_id, app_package)
        logger.info(f"请求关闭驱动 {driver_key}")

        if driver_key in self.driver_locks:
            with self.driver_locks[driver_key]:
                self._close_driver(driver_key)
        else:
            logger.warning(f"尝试关闭不存在锁的驱动 {driver_key}")
            # 尝试直接关闭，因为没有对应的锁
            self._close_driver(driver_key)

    def _close_driver(self, driver_key):
        """内部方法，关闭驱动"""
        try:
            with self._lock:  # 获取全局锁以保护驱动字典
                if driver_key in self.drivers and self.drivers[driver_key] is not None:
                    try:
                        self.drivers[driver_key].quit()
                        logger.info(f"关闭驱动 {driver_key} 成功")
                    except Exception as e:
                        logger.warning(f"关闭驱动 {driver_key} 时出错: {str(e)}")
                    finally:
                        self.drivers[driver_key] = None
                        if driver_key in self.last_used:
                            del self.last_used[driver_key]
                else:
                    logger.debug(f"驱动 {driver_key} 已不存在，无需关闭")
        except Exception as e:
            logger.error(f"在关闭驱动 {driver_key} 过程中发生异常: {str(e)}")

    def _cleanup_idle_drivers(self):
        """后台线程清理空闲驱动"""
        logger.info("启动驱动清理后台线程")
        while True:
            try:
                time.sleep(60)  # 每分钟检查一次
                current_time = time.time()

                drivers_to_close = []

                # 收集需要关闭的驱动
                with self._lock:
                    for driver_key in list(self.last_used.keys()):
                        if current_time - self.last_used[driver_key] > self.max_idle_time:
                            drivers_to_close.append(driver_key)

                # 关闭收集到的空闲驱动
                for driver_key in drivers_to_close:
                    logger.info(f"清理空闲驱动 {driver_key}")
                    self.close_driver(driver_key.split('_')[0], driver_key.split('_', 1)[1])

                if drivers_to_close:
                    logger.info(f"清理了 {len(drivers_to_close)} 个空闲驱动")
                else:
                    logger.debug("没有空闲驱动需要清理")

            except Exception as e:
                logger.error(f"驱动清理线程出错: {str(e)}")


class AppiumDriverManager:
    """driver初始化"""

    def __init__(self, device_id, device_type, device_version, app_package, app_activity):
        self.device_id = device_id
        self.device_type = device_type
        self.device_version = device_version
        self.app_package = app_package
        self.app_activity = app_activity

        APPIUM_HOST = "192.168.69.249"
        APPIUM_PORT = 4723
        self.APPIUM_BASE_URL = f"http://{APPIUM_HOST}:{APPIUM_PORT}"

    def create_driver(self):
        """创建并返回配置好的appium driver"""
        options = UiAutomator2Options()
        options.platform_name = self.device_type
        options.platform_version = str(self.device_version)
        options.device_name = self.device_id
        options.app_package = self.app_package
        options.app_activity = self.app_activity
        options.automation_name = "UiAutomator2"
        options.no_reset = True
        options.new_command_timeout = 36000

        return webdriver.Remote(
            command_executor=self.APPIUM_BASE_URL,
            options=options
        )


class JumpAdvertise:
    """跳过彩民之家广告"""

    def __init__(self, driver, device_id=None):
        self.driver = driver
        self.device_id = device_id

    def click_element(self, text='跳过', x_proportion="0.888121546961326", y_proportion="0.06624064837905237"):
        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((AppiumBy.XPATH, f'//*[contains(@text, {text})]'))
            )
            element.click()
            print('点击元素跳过的广告')
        except Exception as e:
            print(f'广告跳过报错{e}')


class ElementOperator:
    """元素点击操作"""

    def __init__(self, driver, device_id=None):
        self.driver = driver
        self.device_id = device_id

    def click_element(self, text=None, content_desc=None, x_proportion=None, y_proportion=None):
        """
        执行点击操作
        :return: 成功返回 None，失败抛异常
        """
        try:
            if text:
                element = self.driver.find_element(AppiumBy.XPATH, f'//*[@text="{text}"]')
                element.click()
            elif content_desc:
                element = self.driver.find_element(AppiumBy.XPATH, f'//*[@content-desc="{content_desc}"]')
                element.click()
            else:
                raise ValueError("点击元素失败")
        except Exception:
            # 如果根据text或content-desc找不到元素，则使用坐标点击
            if x_proportion is not None and y_proportion is not None:
                device = Devices.objects.filter(unique_id=self.device_id).first()
                if not device:
                    raise ValueError("没找到对应设备尺寸")

                width = float(device.device_width)
                height = float(device.device_high)
                x = int(width * float(x_proportion))
                y = int(height * float(y_proportion))
                self.driver.tap([(x, y)], 100)
                print('使用了坐标点击')
            else:
                raise ValueError("点击元素失败")


class ElementLongPressOperator:
    """元素长按操作"""

    def __init__(self, driver, device_id=None):
        self.driver = driver
        self.device_id = device_id

    def long_press_element(self, text=None, content_desc=None, x_proportion=None, y_proportion=None, duration=None):
        """
        执行长按操作
        :return: 成功返回 None，失败抛异常
        """
        try:
            if text:
                element = self.driver.find_element(AppiumBy.XPATH, f'//*[@text="{text}"]')

                # 创建 ActionChains 对象
                actions = ActionChains(self.driver)

                # 长按操作
                actions.click_and_hold(element).pause(duration / 1000).release().perform()


            elif content_desc:
                element = self.driver.find_element(AppiumBy.XPATH, f'//*[@content-desc="{content_desc}"]')

                # 创建 ActionChains 对象
                actions = ActionChains(self.driver)

                # 长按操作
                actions.click_and_hold(element).pause(duration / 1000).release().perform()
            else:
                raise ValueError("长按元素失败")

        except Exception:
            # 如果根据text或content-desc找不到元素，则使用坐标点击
            if x_proportion is not None and y_proportion is not None:
                device = Devices.objects.filter(unique_id=self.device_id).first()
                if not device:
                    raise ValueError("没找到对应设备尺寸")

                width = float(device.device_width)
                height = float(device.device_high)
                x = int(width * float(x_proportion))
                y = int(height * float(y_proportion))
                self.driver.tap([(x, y)], duration)
            else:
                raise ValueError("长按元素失败")


class ElementSwipeOperator:
    """元素滑动操作"""

    def __init__(self, driver, device_id=None):
        self.driver = driver
        self.device_id = device_id

    def swipe_element(self, start_x_start_y_end_x_end_y=None, duration=None):
        """
        执行滑动操作
        :return: 成功返回 None，失败抛异常
        """
        try:
            device = Devices.objects.filter(unique_id=self.device_id).first()
            if not device:
                raise ValueError("没找到对应设备尺寸")

            width = float(device.device_width)
            height = float(device.device_high)
            if start_x_start_y_end_x_end_y and duration:
                start_x, start_y, end_x, end_y = [float(x) for x in start_x_start_y_end_x_end_y.split(',')[:]]
                s_x = int(start_x * width)
                s_y = int(start_y * height)
                e_x = int(end_x * width)
                e_y = int(end_y * height)
                self.driver.swipe(s_x, s_y, e_x, e_y, duration=1000)

            else:
                raise ValueError("滑动失败")



        except Exception:
            raise ValueError("滑动失败")


class ElementClickAfterSwipingOperator:
    """元素先滑动再点击操作"""

    def __init__(self, driver, device_id=None):
        self.driver = driver
        self.device_id = device_id

    def click_after_swipe_element(self, text=None, content_desc=None, x_proportion=None, y_proportion=None,
                                  start_x_start_y_end_x_end_y=None, duration=None):
        """
        执行滑动操作
        :return: 成功返回 None，失败抛异常
        """
        device = Devices.objects.filter(unique_id=self.device_id).first()
        if not device:
            raise ValueError("没找到对应设备尺寸")

        width = float(device.device_width)
        height = float(device.device_high)

        try:
            if start_x_start_y_end_x_end_y and duration:
                start_x, start_y, end_x, end_y = [float(x) for x in start_x_start_y_end_x_end_y.split(',')[:]]
                s_x = int(start_x * width)
                s_y = int(start_y * height)
                e_x = int(end_x * width)
                e_y = int(end_y * height)
                self.driver.swipe(s_x, s_y, e_x, e_y, duration=1000)

            else:
                raise ValueError("滑动失败")

        except Exception:
            raise ValueError("滑动失败")
        """
        执行点击操作
        """
        try:
            if text:
                element = self.driver.find_element(AppiumBy.XPATH, f'//*[@text="{text}"]')
                element.click()
            elif content_desc:
                element = self.driver.find_element(AppiumBy.XPATH, f'//*[@content-desc="{content_desc}"]')
                element.click()
            else:
                raise ValueError("点击元素失败")
        except Exception:
            # 如果根据text或content-desc找不到元素，则使用坐标点击
            if x_proportion is not None and y_proportion is not None:

                x = int(width * float(x_proportion))
                y = int(height * float(y_proportion))
                self.driver.tap([(x, y)], 100)
            else:
                raise ValueError("点击元素失败")


class ElementEnterTextOperator:
    """输入文字操作"""

    def __init__(self, driver, device_id=None):
        self.driver = driver
        self.device_id = device_id

    def enter_text(self, position_text=None, enter=None):
        """
        执行输入文字操作
        :return: 成功返回 None，失败抛异常
        """
        try:
            if position_text:
                screenshot_png = self.driver.get_screenshot_as_png()

                # 将 PNG 转换为 NumPy 数组
                image_array = np.frombuffer(screenshot_png, dtype=np.uint8)
                image = cv2.imdecode(image_array, cv2.IMREAD_COLOR)

                reader = easyocr.Reader(["ch_sim", "en"])
                result = reader.readtext(image)

                # 查找目标文本的位置
                target_coords = None

                for bbox, text, prob in result:
                    if position_text in text:
                        target_coords = bbox
                        break

                if target_coords:
                    coordinate = [[int(point[0]), int(point[1])] for point in target_coords]
                    mid_x = (coordinate[0][0] + coordinate[1][0]) // 2
                    mid_y = (coordinate[1][1] + coordinate[2][1]) // 2
                    self.driver.tap([(mid_x, mid_y)], 100)

                # 光标进入输入框，开始输入内容
                self.driver.switch_to.active_element.send_keys(enter)
                self.driver.hide_keyboard()



            else:
                raise ValueError("输入文字失败")
        except Exception as e:
            print(e)
