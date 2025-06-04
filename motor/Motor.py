import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from common.move_data import MoveData

# import struct
from typing import Protocol

from PCA9685Motor import PCA9685Motor
from ModbusMotor import ModbusMotor


# 定义电机驱动基类
class MotorBase(Protocol):

    def Control(self, data: MoveData) -> None:
        pass







# 统一的电机控制类，可以选择使用哪种驱动方式
class Motor:
    def __init__(self, driver_type="pca9685", **kwargs):
        """
        初始化电机控制器

        参数:
            driver_type: 驱动类型，可选 "pca9685" 或 "modbus"
            **kwargs: 根据驱动类型传递不同的参数
                对于 pca9685: d1, d2, d3, d4
                对于 modbus: port
        """
        if driver_type == "pca9685":
            d1 = kwargs.get("d1", 1500)
            d2 = kwargs.get("d2", 1500)
            d3 = kwargs.get("d3", 1500)
            d4 = kwargs.get("d4", 1500)
            self.driver = PCA9685Motor(d1, d2, d3, d4)
        elif driver_type == "modbus":
            port = kwargs.get("port", "COM1")
            self.driver = ModbusMotor(port)
        else:
            raise ValueError(f"不支持的驱动类型：{driver_type}")

        self.driver_type = driver_type

    def __getattr__(self, name):
        """转发方法调用到具体的驱动实现"""
        return getattr(self.driver, name)


def calculate_crc(data):
    crc = 0xFFFF
    for byte in data:
        crc ^= byte
        for _ in range(8):
            if crc & 0x0001:
                crc = (crc >> 1) ^ 0xA001
            else:
                crc = crc >> 1
    return crc


def send_modbus_command(command):

    data_without_crc = command[:-5]
    crc = calculate_crc(bytes.fromhex(data_without_crc))
    crc_bytes = struct.pack("<H", crc)
    command_with_crc = data_without_crc + f" {crc_bytes[0]:02X} {crc_bytes[1]:02X}"
    print(command_with_crc)


if __name__ == "__main__":
    # 使用 Modbus 驱动
    # car_controller:MotorBase = ModbusMotor(port="COM1")
    # car_controller.Control(1,100)
    send_modbus_command("05 44 23 18 33 18 FF 64 FF 64 AD 09")
