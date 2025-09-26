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
options.platform_version = "11"
options.device_name = "pr4pvgjjeynzojm7"
options.app_package = "com.android.calendar"
options.app_activity = ".homepage.AllInOneActivity"
options.automation_name = "UiAutomator2"
options.no_reset = True
options.new_command_timeout = 60


class CalendarTest:
    def __init__(self):
        try:
            # 初始化 driver，使用更新的配置
            self.driver = webdriver.Remote(
                command_executor=APPIUM_BASE_URL,
                options=options
            )
            self.driver.implicitly_wait(10)
            # 确保应用处于正确的初始状态
            self.reset_app_state()
        except Exception as e:
            print(f"连接 Appium 服务器失败: {str(e)}")
            raise e

    def reset_app_state(self):
        """重置应用状态"""
        try:
            # 终止并重启应用
            self.driver.terminate_app(options.app_package)
            time.sleep(1)  # 等待应用完全关闭
            self.driver.activate_app(options.app_package)
            time.sleep(2)  # 等待应用启动完成
        except Exception as e:
            print(f"重置应用状态时出错: {str(e)}")

    def wait_for_element(self, locator, timeout=10, retries=2):
        """等待元素可见，支持重试机制"""
        for attempt in range(retries):
            try:
                return WebDriverWait(self.driver, timeout).until(
                    EC.presence_of_element_located(locator)
                )
            except Exception as e:
                if attempt == retries - 1:  # 最后一次尝试
                    raise e
                print(f"尝试第 {attempt + 1} 次查找元素失败，正在重试...")
                self.reset_app_state()  # 重试前重置应用状态

    def test_weather(self):
        """测试天气功能"""
        try:
            # 等待并点击天气元素
            weather_element = self.wait_for_element(
                (AppiumBy.XPATH, "//*[@text='朝阳区']"),
                timeout=10,
                retries=2
            )

            if weather_element.is_displayed():
                time.sleep(1)  # 短暂等待确保元素完全可交互
                weather_element.click()
                print('成功点击了朝阳区的天气')
                time.sleep(1)  # 等待动画完成
                self.driver.back()
            else:
                print("天气元素存在但不可见")

        except Exception as e:
            print(f"测试过程中出现错误: {str(e)}")
            # 出错时尝试重置应用状态
            self.reset_app_state()

    def teardown(self):
        """清理资源"""
        try:
            if self.driver:
                # 确保应用被完全关闭
                self.driver.terminate_app(options.app_package)
                time.sleep(1)
                self.driver.quit()
        except Exception as e:
            print(f"清理资源时出错: {str(e)}")


def main():
    test = None
    try:
        test = CalendarTest()
        print("开始测试日历应用...")
        test.test_weather()

    except Exception as e:
        print(f"测试过程中出现未处理的错误: {str(e)}")

    finally:
        if test:
            print("\n测试完成，清理资源...")
            test.teardown()


# if __name__ == "__main__":
#     main()

