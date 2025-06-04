import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)) + "/../")
from common.move_data import MoveData

import smbus
import traitlets
import time

# 定义 PCA9685 电机驱动类
class PCA9685Motor(traitlets.HasTraits):
    def __init__(self, d1, d2, d3, d4):
        super().__init__()
        self.interval = 0.05
        self.last_time = time.time()
        # 设置 PCA9685 I2C 地址
        self.PCA9685_ADDRESS = 0x60#0x60

        # 寄存器地址
        self.MODE1 = 0x00
        self.PRE_SCALE = 0xFE
        self.LED0_ON_L = 0x06


        # 初始化 I2C 总线
        self.bus = smbus.SMBus(2)
        self.write(self.MODE1, 0x00)
        self.set_pwm_frequency(50)
        self.set_pwm(d1, d2, d3, d4)
        self.Stop()

        self.release_angle1 = 90
        self.release_angle2 = 87

        self.traffic_light_release()
    def write(self, reg, value):
        self.bus.write_byte_data(self.PCA9685_ADDRESS, reg, value)

    Car_run = traitlets.Integer(default_value=0)

    def Control(self, data: MoveData):
        actions = {
            0: self.Stop,
            1: self.Advance,
            2: self.Back,
            5: self.Turn_Left,
            6: self.Turn_Right,
        }

        speed_pwm=int(data.speed*2048/100)
        self.set_pwm(speed_pwm,speed_pwm,speed_pwm,speed_pwm)

        if data.direction == 0:
            actions[data.direction]()
        current_time = time.time()
        if current_time - self.last_time > self.interval:
            print("Car_run_Task called with value:", data.direction)  # 调试打印
            self.last_time = current_time
            actions[data.direction]()

    # 绑定 Car_run 属性的观察者函数
    @traitlets.validate("Car_run")
    def _Car_run_Task(self, proposal):
        actions = {
            0: self.Stop,
            1: self.Advance,
            2: self.Back,
            3: self.Move_Left,
            4: self.Move_Right,
            5: self.Trun_Left,
            6: self.Trun_Right,
            7: self.Advance_Left,
            8: self.Advance_Right,
            9: self.Back_Left,
            10: self.Back_Right,
            11: self.Rotate_Left,
            12: self.Rotate_Right,
        }

        value = proposal["value"]
        if value in actions:
            actions[value]()

        return value

    def Stop(self):  # 停止
        self.Status_control(0, 0, 0, 0)

    def Advance(self):  # 前进
        self.Status_control(1, 1, 1, 1)

    def Back(self):  # 后退
        self.Status_control(-1, -1, -1, -1)

    def Move_Left(self):  # 平移向左
        self.Status_control(-1, 1, 1, -1)

    def Move_Right(self):  # 平移向右
        self.Status_control(1, -1, -1, 1)

    def Turn_Left(self):  # 左转
        self.Status_control(0, 1, 1, 1)

    def Turn_Right(self):  # 右转
        self.Status_control(1, 0, 1, 1)

    def Advance_Left(self):  # 左前
        self.Status_control(0, 1, 1, 0)

    def Advance_Right(self):  # 右前
        self.Status_control(1, 0, 0, 1)

    def Back_Left(self):  # 左后
        self.Status_control(-1, 0, 0, -1)

    def Back_Right(self):  # 右后
        self.Status_control(0, -1, -1, 0)

    def Rotate_Right(self):  # 左旋转
        self.Status_control(1, -1, 1, -1)

    def Rotate_Left(self):  # 右旋转
        self.Status_control(-1, 1, -1, 1)

    def LX_90D(self, t_ms):  # 左旋转 90 度
        self.Rotate_Left()
        time.sleep(t_ms / 1000.0)
        self.Stop()

    def RX_90D(self, t_ms):  # 右旋转 90 度
        self.Rotate_Right()
        time.sleep(t_ms / 1000.0)
        self.Stop()

    def GS_run(self, L_speed, R_speed):
        self.set_pwm(L_speed, R_speed, L_speed, R_speed)

    def set_pwm_frequency(self, freq):
        # 计算预分频值
        prescale_val = int((25000000.0 / (4096 * freq)*0.98 - 1) + 0.5) # 0.98为设置频率与实际频率存在的误差，为多次实验总结出的；0.5为实现四舍五入

        # 读取当前 MODE1 寄存器的值
        old_mode = self.bus.read_byte_data(self.PCA9685_ADDRESS, self.MODE1)

        # 设置 SLEEP 位（MODE1 寄存器的第 4 位）为 1，进入睡眠模式
        new_mode = (old_mode & 0x7F) | 0x10
        self.bus.write_byte_data(self.PCA9685_ADDRESS, self.MODE1, new_mode)

        # 设置预分频寄存器的值
        self.bus.write_byte_data(self.PCA9685_ADDRESS, self.PRE_SCALE, prescale_val)

        # 将 SLEEP 位设置为 0，退出睡眠模式
        self.bus.write_byte_data(self.PCA9685_ADDRESS, self.MODE1, old_mode)

        # 等待至少 500us，以确保 OSC 稳定
        time.sleep(0.001) # 1ms

        # 将 RESTART 位（MODE1 寄存器的第 7 位）设置为 1，重启设备
        self.bus.write_byte_data(self.PCA9685_ADDRESS, self.MODE1, old_mode | 0x80)
        # 无需置0，PCA9865会在自动将RESTART位置0
        # self.bus.write_byte_data(self.PCA9685_ADDRESS, self.MODE1, 0x00)

    def set_pwm(self, Duty_channel1, Duty_channel2, Duty_channel3, Duty_channel4):
        # 设置 PWM 通道的占空比
        Duty_channel1 = max(0, min(Duty_channel1, 4095))  # 限制 off_time 在 0-4095 之间
        Duty_channel2 = max(0, min(Duty_channel2, 4095))  # 限制 off_time 在 0-4095 之间
        Duty_channel3 = max(0, min(Duty_channel3, 4095))  # 限制 off_time 在 0-4095 之间
        Duty_channel4 = max(0, min(Duty_channel4, 4095))  # 限制 off_time 在 0-4095 之间

        # 简化后的 PWM 设置函数
        def set_channel_pwm(channel, duty):
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel, 0 & 0xFF
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 1, 0 >> 8
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 2, duty & 0xFF
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 3, duty >> 8
            )

        set_channel_pwm(0, Duty_channel1)
        set_channel_pwm(5, Duty_channel2)
        set_channel_pwm(6, Duty_channel3)
        set_channel_pwm(11, Duty_channel4)

    def Status_control(self, m4, m3, m2, m1):
        # 简化后的电机控制函数
        def set_motor_pwm(channel_pair, direction):
            channel1, channel2 = channel_pair

            if direction == -1:  # 反向
                set_channel_pwm(channel1, 4095)
                set_channel_pwm(channel2, 0)
            elif direction == 0:  # 停止
                set_channel_pwm(channel1, 0)
                set_channel_pwm(channel2, 0)
            elif direction == 1:  # 正向
                set_channel_pwm(channel1, 0)
                set_channel_pwm(channel2, 4095)

        def set_channel_pwm(channel, duty):
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel, 0 & 0xFF
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 1, 0 >> 8
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 2, duty & 0xFF
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 3, duty >> 8
            )

        # 控制四个电机
        set_motor_pwm((1, 2), m1)
        set_motor_pwm((3, 4), m2)
        set_motor_pwm((7, 8), m3)
        set_motor_pwm((9, 10), m4)

    def set_servo_angle(self, angle):
        min_pulse = 150
        max_pulse = 2500
        angle = max(0, min(180, angle))  # 限制角度在 0 到 180 度之间
        pulse_width = int((angle / 180.0) * (max_pulse - min_pulse) + min_pulse)
        duty_cycle = (pulse_width / 20000) * 4096  # 将脉冲宽度转换为占空比
        return int(duty_cycle)

    def set_servo(self, channel, angle1):
        # 设置 PWM 通道的占空比
        Duty_channel1 = self.set_servo_angle(angle1)

        def set_channel_pwm(channel, on_value, off_value):
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel, on_value & 0xFF
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 1, on_value >> 8
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 2, off_value & 0xFF
            )
            self.bus.write_byte_data(
                self.PCA9685_ADDRESS, self.LED0_ON_L + 4 * channel + 3, off_value >> 8
            )

        set_channel_pwm(channel, 0, Duty_channel1)

    def release(self):
        self.bus.write_byte_data(self.PCA9685_ADDRESS, self.MODE1, 0x00)

    def traffic_light_change(self):
        self.set_servo(12, 120)
        self.set_servo(13, 90)

    def traffic_light_release(self):
        self.set_servo(12, self.release_angle1)
        self.set_servo(13, self.release_angle2)

    def servo_follow(self):
        self.set_servo(12, 100)

    def servo_poss(self):
        self.set_servo(12, 40)

    def servo_map(self):
        self.set_servo(12, 105)

    def FT_Turn(self, L, R):
        self.Status_control(1, -1, 1, -1)
        self.set_pwm(L, R, L, R)
