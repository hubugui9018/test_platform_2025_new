import asyncio
import json

import cv2
import subprocess
import numpy as np
from channels.generic.websocket import AsyncWebsocketConsumer
import logging
import traceback
from concurrent.futures import ThreadPoolExecutor
from lxml import etree
from urllib.parse import parse_qs

logger = logging.getLogger(__name__)


class VideoStreamConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.screen_size = None
        self.cached_dom_tree = None
        self.device_id = None

    async def connect(self):
        # 从查询参数中获取设备ID
        query_params = parse_qs(self.scope["query_string"].decode())
        self.device_id = query_params.get("unique_id", [None])[0]

        if not self.device_id:
            await self.close(code=4003)
            return

        logger.info(f"WebSocket 连接建立，设备ID: {self.device_id}")
        await self.accept()
        self.is_streaming = False
        self.streaming_task = None

    async def disconnect(self, close_code):
        logger.info(f"WebSocket 连接断开，关闭代码：{close_code}")
        await self.stop_streaming()
        self.executor.shutdown(wait=False)

    async def receive(self, text_data=None, bytes_data=None):
        logger.info(f"收到消息：{text_data}")
        try:
            if text_data:
                data = json.loads(text_data) if text_data.startswith('{') else {'action': text_data}
                action = data.get('action')

                if action == "start":
                    if not self.is_streaming:
                        self.is_streaming = True
                        self.streaming_task = asyncio.create_task(self.start_stream())
                elif action == "stop":
                    await self.stop_streaming()

                elif action == "touch":
                    await self.handle_touch_event(data)

                elif action == "swipe":
                    await self.handle_swipe_event(data)

                elif action == "get_dom_at":
                    await self.get_dom_at_position(data)


        except json.JSONDecodeError:
            logger.error(f"json解析出错：{text_data}")
        except Exception as e:
            logger.error(f"接收消息出错：{str(e)}")

    async def get_device_screen_size(self):
        """获取设备屏幕尺寸"""
        try:
            result = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: subprocess.check_output(['adb', '-s', self.device_id, 'shell', 'wm', 'size'])
            )
            size_str = result.decode().strip()
            if 'size' in size_str:
                width, height = map(int, size_str.split(':')[-1].split('x'))
                self.screen_size = (width, height)
                logger.info(f"设备屏幕尺寸：{self.screen_size}")
        except Exception as e:
            logger.error(f'获取屏幕尺寸失败{str(e)}')

    async def handle_swipe_event(self, data):
        """处理滑动事件"""
        try:
            if not self.screen_size:
                await self.get_device_screen_size()

            # 获取活动的起点和终点坐标
            start_x = int(data.get('startX', 0) * self.screen_size[0])
            start_y = int(data.get('startY', 0) * self.screen_size[1])
            end_x = int(data.get('endX', 0) * self.screen_size[0])
            end_y = int(data.get('endY', 0) * self.screen_size[1])
            duration = data.get('duration', 300)  # 滑动持续事件，默认300

            logger.info(f"执行滑动事件{start_x}, {start_y}) -> ({end_x}, {end_y}")

            # 执行滑动命令
            cmd = f'input swipe {start_x} {start_y} {end_x} {end_y} {duration}'
            await self.execute_adb_command(cmd)


        except Exception as e:
            logger.error(f'滑动事件处理失败{e}')

    async def handle_touch_event(self, data):
        """处理触控事件"""
        try:
            if not self.screen_size:
                await self.get_device_screen_size()

            # 获取点击坐标和类型
            x = data.get('x', 0)
            y = data.get('y', 0)
            touch_type = data.get('type', 'tap')
            is_dom_mode = data.get('dom_mode', False)  # 是否为 DOM 模式

            # 转换为实际设备坐标
            device_x = int(x * self.screen_size[0])
            device_y = int(y * self.screen_size[1])

            if is_dom_mode:
                # **DOM 模式下，更新 DOM 树**
                self.cached_dom_tree = await self.get_dom_tree()
                if self.cached_dom_tree:
                    await self.send(text_data=json.dumps({
                        "action": "update_dom_tree",
                        "dom_tree": self.cached_dom_tree
                    }))
                    logger.info("DOM 模式：获取最新 DOM 树")
                else:
                    logger.warning("DOM 模式：获取 DOM 树失败，无法更新 DOM 树")

            else:
                # **控制模式下，执行点击事件**
                if touch_type == 'tap':
                    cmd = f'input tap {device_x} {device_y}'
                    await self.execute_adb_command(cmd)
                elif touch_type == 'longpress':
                    cmd = f'input swipe {device_x} {device_y} {device_x} {device_y} 500'
                    await self.execute_adb_command(cmd)

                # **控制模式仍然缓存 DOM 树**
                self.cached_dom_tree = await self.get_dom_tree()
                if self.cached_dom_tree:
                    await self.send(text_data=json.dumps({
                        "action": "update_dom_tree",
                        "dom_tree": self.cached_dom_tree
                    }))
                    logger.info(f'执行 {touch_type} 事件, 坐标 ({device_x}, {device_y})')
                else:
                    logger.warning("控制模式：获取 DOM 树失败，无法更新 DOM 树")

        except Exception as e:
            logger.error(f'处理触控事件失败{e}')

    async def get_dom_tree(self):
        """从设备获取dom树"""

        try:
            process = subprocess.Popen(
                ['adb', '-s', self.device_id, 'exec-out', 'uiautomator', 'dump', '/dev/tty'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            dom_data, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"获取DOM树失败：{stderr.decode()}")

            # 检查是否有有效的 XML 数据
            if b'<?xml' not in dom_data:
                logger.error("未找到有效的 XML 数据")
                return None

            result = b'<?xml' + dom_data.split(b'<?xml')[1].split(b'UI hierchary')[0]
            tree = etree.fromstring(result)
            xml_str = etree.tostring(tree, pretty_print=True, encoding='utf-8').decode('utf-8')
            return xml_str

        except Exception as e:
            logger.error(f"获取DOM树失败: {str(e)}")
            return None

    async def get_dom_at_position(self, data):
        """获取指定位置的DOM信息并发送给前端"""
        try:
            if not self.screen_size:
                await self.get_device_screen_size()

            # 计算实际设备坐标
            device_x = int(data.get('x', 0) * self.screen_size[0])
            device_y = int(data.get('y', 0) * self.screen_size[1])

            # 检查是否有缓存的 DOM 树
            if not self.cached_dom_tree:
                logger.warning("没有缓存的 DOM 树，无法解析元素信息")
                element_info = {
                    'original_x_proportion': data.get('x'),
                    'original_y_proportion': data.get('y')
                }
                await self.send(text_data=json.dumps({
                    "action": "highlight_dom",
                    "element": element_info
                }))
                return

            # 使用 UIElementFinder 获取元素信息
            finder = UIElementFinder(self.cached_dom_tree)  # 传入缓存的dom
            try:
                element_info = finder.get_element_info(device_x, device_y)
            except Exception as e:
                logger.warning(f"UIElementFinder 解析失败: {str(e)}")
                element_info = None

            logger.info(f'device_x:{device_x},device_y:{device_y}')
            logger.info(f'element_info111:{element_info}')

            if element_info:
                element_info = {k: str(v) for k, v in element_info.items()}
                element_info['original_x_proportion'] = data.get('x')
                element_info['original_y_proportion'] = data.get('y')

                # 发送 DOM 元素信息到前端
                await self.send(text_data=json.dumps({
                    "action": "highlight_dom",
                    "element": element_info
                }))
            else:
                element_info = {
                    'original_x_proportion': data.get('x'),
                    'original_y_proportion': data.get('y')
                }
                logger.info(f'else里的element_info：{element_info}')
                await self.send(text_data=json.dumps({
                    "action": "highlight_dom",
                    "element": element_info
                }))

        except Exception as e:
            logger.error(f"获取DOM元素失败: {str(e)}")

    async def execute_adb_command(self, cmd):
        """执行adb shell命令"""
        try:
            await asyncio.get_event_loop().run_in_executor(
                self.executor,
                lambda: subprocess.run(['adb', '-s', self.device_id, 'shell', cmd],
                                       check=True,
                                       capture_output=True)
            )
        except subprocess.CalledProcessError as e:
            logger.error(f"ADB命令执行失败: {cmd}")
            logger.error(f"错误输出: {e.stderr.decode() if e.stderr else ''}")
            raise
        except Exception as e:
            logger.error(f"执行ADB命令时出错: {str(e)}")
            raise

    async def stop_streaming(self):
        logger.info("停止流媒体传输")
        self.is_streaming = False
        if self.streaming_task:
            self.streaming_task.cancel()
            try:
                await self.streaming_task
            except asyncio.CancelledError:
                pass
            self.streaming_task = None

    def capture_screen(self):
        """在线程池中执行 adb 截图命令"""
        try:
            process = subprocess.Popen(
                ['adb', '-s', self.device_id, 'exec-out', 'screencap', '-p'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            screenshot_data, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"截图失败: {stderr.decode()}")

            return screenshot_data

        except Exception as e:
            logger.error(f"截图过程出错: {str(e)}")
            raise

    def process_frame(self, screenshot_data):
        """处理图像帧"""
        try:
            # 转换为numpy数组
            nparr = np.frombuffer(screenshot_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is None:
                raise Exception("图像解码失败")

            # 调整图像大小（如果需要）
            if frame.shape[:2] != (2400, 1080):
                frame = cv2.resize(frame, (1080, 2400))

            # 编码为JPEG
            _, jpeg = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            return jpeg.tobytes()

        except Exception as e:
            logger.error(f"图像处理出错: {str(e)}")
            raise

    def check_adb_devices(self):
        """检查 ADB 设备"""
        try:
            result = subprocess.run(['adb', '-s', self.device_id, 'devices'],
                                    capture_output=True,
                                    text=True)
            return result.stdout
        except Exception as e:
            logger.error(f"检查 ADB 设备时出错: {str(e)}")
            raise

    async def start_stream(self):
        logger.info("开始流媒体传输")
        retry_count = 0
        max_retries = 3
        error_delay = 1  # 错误重试延迟（秒）

        try:
            # 检查设备连接
            devices_output = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.check_adb_devices
            )
            logger.info(f"ADB 设备列表：\n{devices_output}")

            # 主循环
            while self.is_streaming:
                try:
                    # 在线程池中执行截图
                    screenshot_data = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self.capture_screen
                    )

                    # 在线程池中处理图像
                    jpeg_data = await asyncio.get_event_loop().run_in_executor(
                        self.executor,
                        self.process_frame,
                        screenshot_data
                    )

                    # 发送到前端
                    if self.is_streaming:
                        await self.send(bytes_data=jpeg_data)

                    # 重置重试计数
                    retry_count = 0

                    # 控制帧率
                    await asyncio.sleep(0.05)  # 约20fps

                except Exception as e:
                    retry_count += 1
                    error_msg = f"处理帧时出错 (重试 {retry_count}/{max_retries}): {str(e)}"
                    logger.error(error_msg)
                    logger.error(traceback.format_exc())

                    if retry_count >= max_retries:
                        logger.error("达到最大重试次数，停止流媒体")
                        break

                    await asyncio.sleep(error_delay)

        except Exception as e:
            logger.error(f"流媒体错误: {str(e)}")
            logger.error(traceback.format_exc())

        finally:
            logger.info("流媒体传输结束")
            await self.stop_streaming()


class DomTreeConsumer(AsyncWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 初始化线程池
        self.executor = ThreadPoolExecutor(max_workers=5)
        self.device_id = None

    async def connect(self):
        query_params = parse_qs(self.scope["query_string"].decode())
        self.device_id = query_params.get("unique_id", [None])[0]

        if not self.device_id:
            await self.close(code=4003)
            return

        logger.info(f"DOM连接建立，设备ID: {self.device_id}")
        await self.accept()

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data=None, bytes_data=None):
        # 收到请求的DOM树消息
        if text_data == 'get_dom_tree':
            await self.send_dom_tree()

    async def send_dom_tree(self):
        # 抓取手机dom树并发送到前端
        try:
            dom_data = await asyncio.get_event_loop().run_in_executor(
                self.executor,
                self.capture_dom_tree,
            )
            await self.send(text_data=dom_data)
        except Exception as e:
            logger.error(f"抓取 DOM 树失败: {str(e)}")

    def capture_dom_tree(self):
        # 使用adb获取dom树
        try:
            process = subprocess.Popen(
                ['adb', '-s', self.device_id, 'exec-out', 'uiautomator', 'dump', '/dev/tty'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            dom_data, stderr = process.communicate()

            if process.returncode != 0:
                raise Exception(f"获取DOM树失败：{stderr.decode()}")

            result = b'<?xml' + dom_data.split(b'<?xml')[1].split(b'UI hierchary')[0]
            # logger.info(f'dom_data:{dom_data}')
            tree = etree.fromstring(result)
            xml_str = etree.tostring(tree, pretty_print=True, encoding='utf-8').decode('utf-8')
            return xml_str

            # return dom_data.decode('utf-8').split('<?xml')[1].split('UI hierchary')[0]
            # return dom_data

        except Exception as e:
            logger.error(f"获取Dom树出现错误：{str(e)}")
            raise


class UIElementFinder:
    def __init__(self, xml_content):
        self.xml_content = xml_content
        self.tree = etree.fromstring(xml_content.encode('utf-8'))

    def parse_bounds(self, bounds_str):
        """解析bounds字符串为坐标值"""
        try:
            # 移除方括号并分割坐标q
            coords = bounds_str.replace('][', ',').replace('[', '').replace(']', '')
            x1, y1, x2, y2 = map(int, coords.split(','))
            return x1, y1, x2, y2
        except:
            return None

    def get_element_info(self, x, y):
        """获取指定坐标的元素信息"""

        target_element = None
        min_area = float('inf')

        for element in self.tree.xpath("//node"):
            bounds = element.get("bounds")

            if not bounds:
                continue

            coords = self.parse_bounds(bounds)

            if not coords:
                continue

            x1, y1, x2, y2 = coords
            # 检查坐标是否在元素范围内
            if x1 <= x <= x2 and y1 <= y <= y2:

                # 计算面积并更新最小面积的元素
                area = (x2 - x1) * (y2 - y1)

                if area < min_area:
                    min_area = area
                    target_element = element.attrib

        return target_element
