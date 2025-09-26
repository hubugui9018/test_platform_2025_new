import easyocr
from PIL import Image

# 使用简体中文 ('zh') 和英文 ('en')
reader = easyocr.Reader(["ch_sim", "en"])
result = reader.readtext('20250313172133.jpg')

# 查找 "请输入密码" 的位置
target_text = "请输入密码"
target_coords = None

for bbox, text, prob in result:
    if target_text in text:
        target_coords = bbox
        break

# 输出结果
if target_coords:
    coordinate = [[int(point[0]), int(point[1])] for point in target_coords]
    mid_x = (coordinate[0][0] + coordinate[1][0]) // 2
    mid_y = (coordinate[1][1] + coordinate[2][1]) // 2
    print(mid_x, mid_y)
    print(coordinate)

# [[105, 1019], [374, 1019], [374, 1087], [105, 1087]]


# img = Image.open('20250313172133.jpg')
# img.show()
