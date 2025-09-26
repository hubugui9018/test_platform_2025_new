from appium import webdriver
from appium.webdriver.common.appiumby import AppiumBy
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from appium.options.android import UiAutomator2Options

import time

# Appium 2.0+ 服务器地址
APPIUM_HOST = "192.168.69.242"
APPIUM_PORT = 4723
APPIUM_BASE_URL = f"http://{APPIUM_HOST}:{APPIUM_PORT}"

# 创建 UiAutomator2Options 对象
options = UiAutomator2Options()
options.platform_name = "Android"
options.platform_version = "12"
options.device_name = "NAB0220728034708"
options.app_package = "com.zhcw.cp"
options.app_activity = "com.zhcw.cmzjapp.MainActivity"
options.automation_name = "UiAutomator2"
options.no_reset = True
options.new_command_timeout = 60

driver = webdriver.Remote(
    command_executor=APPIUM_BASE_URL,
    options=options
)
# 通过文本内容定位元素
element = driver.find_element(AppiumBy.XPATH, '//*[@content_desc="我的Tab 5 of 5"]')

# 点击元素
element.click()

# 获取屏幕尺寸
screen_size = driver.get_window_size()
width = screen_size['width']
height = screen_size['height']

# 定义滑动起点和终点
start_x = width * 0.5     # 起点x坐标（屏幕中间）
start_y = height * 0.2    # 起点y坐标（屏幕底部）
end_x = width * 0.1       # 终点x坐标（与起点相同）
end_y = height * 0.2      # 终点y坐标（屏幕顶部）

# 执行滑动操作
driver.swipe(start_x, start_y, end_x, end_y, duration=1000)  # duration为滑动持续时间（毫秒）


time.sleep(2)

# 关闭驱动
driver.quit()
