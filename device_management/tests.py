class UIElementFinder:
    def __init__(self):
        import subprocess
        self.subprocess = subprocess

    def get_ui_dump(self):
        """获取UI层级数据"""
        try:
            result = self.subprocess.run(
                ['adb', 'exec-out', 'uiautomator', 'dump', '/dev/tty'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='ignore'
            )
            return result.stdout
        except Exception as e:
            print(f"获取UI层级失败: {e}")
            return None

    def parse_bounds(self, bounds_str):
        """解析bounds字符串为坐标值"""
        try:
            # 移除方括号并分割坐标
            coords = bounds_str.replace('][', ',').replace('[', '').replace(']', '')
            x1, y1, x2, y2 = map(int, coords.split(','))
            return x1, y1, x2, y2
        except:
            return None

    def parse_node_attributes(self, node_str):
        """解析节点字符串中的所有属性"""
        attributes = {}
        # 分割所有的属性对
        parts = node_str.split('" ')

        for part in parts:
            if '="' in part:
                key, value = part.split('="', 1)
                key = key.strip()
                value = value.replace('"', '').strip()
                attributes[key] = value

        return attributes

    def get_element_info(self, x, y):
        """获取指定坐标的元素信息"""
        xml_content = self.get_ui_dump()
        if not xml_content:
            print(f'xml_content:{xml_content}')
            return None

        # 分割所有node节点
        nodes = xml_content.split('<node ')
        print(f'nodes:{nodes}')

        target_element = None
        min_area = float('inf')
        print(f'len_node:{len(nodes)}')
        for node in nodes[1:]:  # 跳过第一个空字符串
            try:
                # 解析节点的所有属性
                attributes = self.parse_node_attributes(node)

                # 如果找到bounds属性
                if 'bounds' in attributes:
                    coords = self.parse_bounds(attributes['bounds'])
                    print(f'1coords:{coords}')
                    if coords:
                        print(f'2coords:{coords}')
                        x1, y1, x2, y2 = coords
                        # 检查坐标是否在元素范围内
                        if x1 <= x <= x2 and y1 <= y <= y2:
                            print('11111')
                            # 计算面积并更新最小面积的元素
                            area = (x2 - x1) * (y2 - y1)

                            if area < min_area:
                                print('22222')
                                min_area = area
                                target_element = attributes


            except Exception as e:
                continue

        return target_element


def get_element_attributes(x, y):
    finder = UIElementFinder()
    element_info = finder.get_element_info(x, y)

    if element_info:
        print("\n找到元素:")
        # 按照重要性排序显示属性
        important_attrs = ['text', 'class', 'resource-id', 'package', 'content-desc',
                           'clickable', 'bounds', 'checked', 'enabled']
        for attr in important_attrs:
            if attr in element_info and element_info[attr]:
                print(f"{attr}: {element_info[attr]}")
        return element_info
    else:
        print(f"\n在坐标 ({x}, {y}) 未找到元素")
        return None


# get_element_attributes(538, 197)
# get_element_attributes(258, 1439)


