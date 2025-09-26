from lxml import etree

def find_xpath_by_text(xml_file, text):
    # 以二进制模式打开文件，读取为字节流
    with open(xml_file, 'rb') as f:
        xml_data = f.read()

    # 解析XML
    tree = etree.fromstring(xml_data)

    # 递归查找指定文本的元素
    def get_xpath(element, path=""):
        # 获取当前元素的标签
        tag = element.tag

        # 处理属性
        if element.attrib:
            attrs = ''.join([f"[@{k}='{v}']" for k, v in element.attrib.items()])
            tag += attrs

        current_path = f"{path}/{tag}" if path else tag

        # 解码元素的文本为UTF-8
        if 'text' in element.attrib.keys():
            element_text = element.attrib['text']
            if isinstance(element_text, bytes):
                element_text = element_text.decode('utf-8')

            # 打印调试信息
            # print(f"Current Path: {current_path}")
            # print(f"Element Text: {element_text}")

            # 如果元素包含文本且目标文本在其中，返回当前路径
            if element_text and text in element_text:
                return current_path

        # 遍历子元素F
        for child in element:
            result = get_xpath(child, current_path)
            if result:
                return result

        return None

    return get_xpath(tree)

# 调用函数
xml_file = 'example.xml'  # XML文件路径
text_to_find = "包月订阅（15期） 5折 210 彩贝"  # 目标文本
xpath = find_xpath_by_text(xml_file, text_to_find)

if xpath:
    print(f"找到的XPath: {xpath}")
else:
    print("没有找到匹配的元素")

def print_xml_tree(xml_file):
    # 以二进制模式打开文件，读取为字节流
    with open(xml_file, 'rb') as f:
        xml_data = f.read()

    # 解析XML
    tree = etree.fromstring(xml_data)


    # 打印解析后的XML内容（作为字符串）
    xml_str = etree.tostring(tree, pretty_print=True, encoding='utf-8').decode('utf-8')
    # print(xml_str)

# 调用函数

print_xml_tree(xml_file)

