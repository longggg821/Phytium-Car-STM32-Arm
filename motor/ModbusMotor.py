import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from common.move_data import MoveData

import struct
import serial
import time
from simple_pid import PID

# 定义 Modbus 电机驱动类
# 在 ModbusMotor 类中添加 PID 控制相关方法
# 需要安装：pip install simple-pid
class ModbusMotor(MotorBase):
    def __init__(self, port):
        super().__init__()
        self.port = port
        self.running = True
        self.last_time = time.time()  # 用来储存上次一执行运动指令的时间
        self.interval = 0.05   # 给前后两个运动指令的最短间隔，小于这个间隔则新的运动指令不会执行，停止指令不检测间隔
        # 添加速度相关的属性初始化
        self.left_speed = 0
        self.right_speed = 0
        self.max_speed = 255  # 最大速度限制
        self.enable_motor()

    def set_motor_speed(self, left_speed, right_speed):
        """设置电机速度

        Args:
            left_speed: 左轮速度 (-255 到 255)
            right_speed: 右轮速度 (-255 到 255)
        """
        # 限制速度范围
        self.left_speed = max(-self.max_speed, min(self.max_speed, left_speed))
        self.right_speed = max(-self.max_speed, min(self.max_speed, right_speed))

    def Control(self, data: MoveData):
        # TODO 目前只前进后悔控制速度，左转右转时速度影响转弯半径
        actions = {
            0: self.Stop,
            1: self.Advance,
            2: self.Back,
            5: self.Trun_Left,
            6: self.Trun_Right,
        }

        # self.left_speed = data.speed
        # self.right_speed = data.speed
        self.set_motor_speed(data.speed, data.speed)
        if data.direction == 0:
            actions[data.direction]()
        current_time = time.time()
        if current_time - self.last_time > self.interval:
            print("Car_run_Task called with value:", data.direction)  # 调试打印
            self.last_time = current_time
            actions[data.direction]()

    def send_modbus_command(self, command):
        try:
            with serial.Serial(self.port, baudrate=57600, timeout=0.1) as ser:
                request = bytes.fromhex(command)
                ser.write(request)
        except (serial.SerialException, OSError) as e:
            print(f"Unable to open serial port {self.port}: {e}")

    # 添加一个装饰器函数来检查电机状态
    def check_motor_state(func):
        def wrapper(self, *args, **kwargs):
            if not self.running:
                self.enable_motor()
            return func(self, *args, **kwargs)

        return wrapper

    # 计算 CRC 函数
    def calculate_crc(self, data):
        crc = 0xFFFF
        for byte in data:
            crc ^= byte
            for _ in range(8):
                if crc & 0x0001:
                    crc = (crc >> 1) ^ 0xA001
                else:
                    crc = crc >> 1
        return crc

    def enable_motor(self):
        self.running = True
        self.send_modbus_command(self.get_modbus_command("enable"))

    def disable_motor(self):
        self.running = False
        self.send_modbus_command(self.get_modbus_command("disable"))

    def Stop(self):
        self.send_modbus_command(self.get_modbus_command("stop"))

    def Advance(self):
        self.send_modbus_command(self.get_modbus_command("advance"))

    def Back(self):

        self.send_modbus_command(self.get_modbus_command("back"))

    def Trun_Left(self):
        self.right_speed=-self.left_speed
        self.send_modbus_command(self.get_modbus_command("turn_left"))

    def Trun_Right(self):
        self.left_speed=-self.right_speed
        self.send_modbus_command(self.get_modbus_command("turn_right"))

    # 获取 Modbus 命令映射
    def set_motor_speed(self, left_speed, right_speed):
        """设置电机速度

        Args:
            left_speed: 左轮速度 (-255 到 255)
            right_speed: 右轮速度 (-255 到 255)
        """
        # 限制速度范围
        self.left_speed = left_speed
        self.right_speed = right_speed

    def get_modbus_command(self, action):
        """获取 Modbus 命令"""

        # 转换速度为十六进制格式
        def speed_to_hex(speed):
            if speed < 0:
                data = (0xFFFF - abs(speed) + 1) & 0xFFFF
            else:
                data = speed
        
            # 转换为大端序字节
            return f"{(data >> 8) & 0xFF:02X} {data & 0xFF:02X}"



        # 基础命令模板
        base_commands = {
            "enable":  "05 44 21 00 31 00 00 01 00 01",
            "disable": "05 44 21 00 31 00 00 00 00 00",
            "stop":    "05 44 23 18 33 18 00 00 00 00 00",
        }

        # 运动命令需要动态生成
        movement_commands = {
            "advance":    f"05 44 23 18 33 18 {speed_to_hex(self.right_speed)} {speed_to_hex(self.left_speed)}",
            "back":       f"05 44 23 18 33 18 {speed_to_hex(-self.right_speed)} {speed_to_hex(-self.left_speed)}",
            "turn_left":  f"05 44 23 18 33 18 {speed_to_hex(self.right_speed)} {speed_to_hex(self.left_speed)}",
            "turn_right": f"05 44 23 18 33 18 {speed_to_hex(self.right_speed)} {speed_to_hex(self.left_speed)}",
        }

        # 合并命令字典
        commands = {**base_commands, **movement_commands}
        command = commands.get(action, "")
       
        # 如果命令非空，计算并添加 CRC
        if command:
            data = bytes.fromhex(command)
            crc = self.calculate_crc(data)
            crc_bytes = struct.pack("<H", crc)
            command = f"{command} {crc_bytes[0]:02X} {crc_bytes[1]:02X}"
        print(command)
        return command