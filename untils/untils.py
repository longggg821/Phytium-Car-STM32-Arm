import cv2
import numpy as np
import pyarrow as pa


def translate_image(data, metadata):
    """处理图像数据，支持不同编码格式"""
    # 转换为 NumPy 数组
    np_array = data.to_numpy()
    # 根据编码处理数据
    encoding = metadata["encoding"]
    if encoding in ["bgr8", "rgb8"]:
        # 原始像素格式
        height = metadata["height"]
        width = metadata["width"]
        image = np_array.reshape((height, width, 3))
        if encoding == "rgb8":
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
    elif encoding in ["jpeg", "png"]:
        # 压缩格式，需要解码
        byte_data = np_array.tobytes()
        image = cv2.imdecode(np.frombuffer(byte_data, np.uint8), cv2.IMREAD_COLOR)
    elif encoding in ["uint8"]:
        height = metadata["height"]
        width = metadata["width"]
        image = np_array.reshape((height, width))
    else:
        return None
    return image


class Calculate:
    """
    用于存储和处理目标检测结果的数据类
    
    属性:
        x (int): 目标在图像中的 x 坐标
        y (int): 目标在图像中的 y 坐标
        ratio (float): 目标在图像中所占的比例
    """
    def __init__(self, x, y, ratio):
        """
        初始化 Calculate 对象
        
        参数:
            x (int): 目标在图像中的 x 坐标
            y (int): 目标在图像中的 y 坐标
            ratio (float): 目标在图像中所占的比例
        """
        self.x = x
        self.y = y
        self.ratio = ratio

    @staticmethod
    def to_pa_array(calc_list):
        """将 Calculate 对象列表转换为 pyarrow 数组"""
        data = [(c.x, c.y, c.ratio) for c in calc_list]
        return pa.array(
            data,
            type=pa.struct(
                [
                    pa.field("x", pa.int64()),
                    pa.field("y", pa.int64()),
                    pa.field("ratio", pa.float64()),
                ]
            ),
        )

    @staticmethod
    def from_pa_array(pa_array):
        """将 pyarrow 数组转换回 Calculate 对象列表"""
        return [
            Calculate(item["x"].as_py(), item["y"].as_py(), item["ratio"].as_py())
            for item in pa_array
        ]


# 方向转换
def translate_direction(direction: int):
    directions = {
        0: "Stop",
        1: "Advance",
        2: "Back",
        5: "Trun_Left",
        6: "Trun_Right",
    }
    return directions.get(direction)
