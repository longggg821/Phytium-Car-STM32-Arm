from dora import Node
import pyarrow as pa
import functools
from common.move_data import MoveData


class Move:
    def __init__(self, node, debug=True):
        self.node = node
        self.debug = debug

    def debug_log(func):
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if self.debug:
                print(f"move:{func.__name__}")
            return func(self, *args, **kwargs)

        return wrapper

    def send(self, direction, speed):
        """
        发送运动数据给其他节点
        Args:
            direction (int): 运动的方向。

        Returns:
            bool: 是否发送成功。

        Raises:
            ZeroDivisionError: 如果除数为零，则抛出异常。
        """
        data = MoveData(direction, speed).to_arrow_array()
        self.node.send_output("move", data)

    @debug_log
    def stop(self):
        return self.send(0, 0)

    @debug_log
    def advance(self, speed=2):
        return self.send(1, speed)

    @debug_log
    def Back(self, speed=2):
        return self.send(2, speed)

    @debug_log
    def turn_left(self, speed=2):
        return self.send(5, speed)

    @debug_log
    def turn_right(self, speed=2):
        return self.send(6, speed)
