import pyarrow as pa
from typing import List


class DetectData:

    """
    用于存储和处理目标检测结果的数据类
    
    属性:
        x (int): 目标在图像中的 x 坐标
        y (int): 目标在图像中的 y 坐标
        w (int): 目标的 x 坐标上的长
        h (int): 目标的 y 坐标上的高
    """
    def __init__(self, x, y, w, h):
        """
        初始化 Calculate 对象
        
        参数:
            x (int): 目标在图像中的 x 坐标
            y (int): 目标在图像中的 y 坐标
            w (int): 目标的 x 坐标上的长
            h (int): 目标的 y 坐标上的高
        """
        self.x = x
        self.y = y
        self.w = w
        self.h = h

    @staticmethod
    def to_pa_array(calc_list):
        """将 Calculate 对象列表转换为 pyarrow 数组"""
        data = [(c.x, c.y, c.w, c.h) for c in calc_list]
        return pa.array(
            data,
            type=pa.struct(
                [
                    pa.field("x", pa.int64()),
                    pa.field("y", pa.int64()),
                    pa.field("w", pa.int64()),
                    pa.field("h", pa.int64()),
                ]
            ),
        )

    @staticmethod
    def from_pa_array(pa_array):
        """将 pyarrow 数组转换回 Calculate 对象列表"""
        return [
            Calculate(item["x"].as_py(), item["y"].as_py(), item["w"].as_py(), item["h"].as_py())
            for item in pa_array
        ]
