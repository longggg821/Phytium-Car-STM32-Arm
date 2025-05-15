import cv2
import numpy as np
##from dora import Node
import pyarrow as pa
import sys
import os
import serial
import time

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 现在可以正常导入
from untils.untils import Calculate

from motor.Motor import PCA9685Motor



def process_image(data, metadata):
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
    else:
        return None

    return image


class ColorDetector:
    def __init__(
        self,
        lower_hsv,
        upper_hsv,
        ratio_value=0.0322265625,
        min_area=300,
        max_area=10000,
    ):
        """
        颜色识别器构造函数
        :param lower_hsv: HSV 颜色空间下限阈值 (list/tuple)
        :param upper_hsv: HSV 颜色空间上限阈值 (list/tuple)
        :param min_area: 最小识别区域面积（过滤噪声）
        """
        self.lower = np.array(lower_hsv)
        self.upper = np.array(upper_hsv)
        self.min_area = min_area
        self.max_area = max_area
        self.kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        # 锁眼位置
        self.recet_pos = (210, 354, 100, 100)
        self.center = (278, 298)
        #  图片的高和宽
        self.h = 480
        self.w = 640
        self.ratio_value = ratio_value

    def set_threshold(self, lower_hsv, upper_hsv):
        """动态设置颜色阈值范围"""
        self.lower = np.array(lower_hsv)
        self.upper = np.array(upper_hsv)

    def ratio(self, h, w):
        """
        计算轮廓的长宽比
        :param height:
        :param width:
        :return: 长宽比列表
        """
        return (h / self.h) * w / self.w

    def process(self, frame):
        """处理图像帧以识别单个网球。

        该方法对输入图像进行预处理、颜色阈值分割和轮廓检测，以识别单个网球。
        当检测到多个符合条件的轮廓时，会选择面积最大的一个作为网球。

        Args:
            frame: 输入的图像帧，BGR 格式的 numpy 数组。

        Returns:
            tuple: 包含三个元素:
                - processed_frame: 处理后的图像，带有标记的网球位置。
                - centers: 网球中心点坐标列表，格式为 [(x, y)]。
                - mask: 二值化掩膜图像。

        Raises:
            None
        """
        # 预处理 - 高斯模糊减少噪声
        blurred_img = cv2.GaussianBlur(frame, (5, 5), 0)

        # 中值滤波进一步减少噪声
        median_blur = cv2.medianBlur(blurred_img, 5)

        # 转换为 HSV 颜色空间
        hsv = cv2.cvtColor(median_blur, cv2.COLOR_BGR2HSV)

        # 创建颜色掩膜
        mask = cv2.inRange(hsv, self.lower, self.upper)
        # 形态学操作（消除噪声）
        # 定义结构元素（核），例如 5x5 的矩形
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        # 开运算，先腐蚀再膨胀，用于去除小的噪点
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
        ma=mask
        # 闭运算，先膨胀再腐蚀，用于填充孔洞
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=3)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
        mask = cv2.GaussianBlur(mask, (5, 5), 0)

        # 查找轮廓
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        data = []
        processed_frame = frame.copy()
        # 轮询处理每个轮廓
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            # 计算轮廓的圆形度
            perimeter = cv2.arcLength(cnt, True)
            if perimeter == 0:
                continue
            circularity = 4 * np.pi * area / (perimeter * perimeter)

            # 只处理面积小于某个值且轮廓接近圆形的轮廓
            if (
                area > self.min_area and area < self.max_area and circularity > 0.8
            ):  # 圆形度阈值可以调整
                center_x = x + w // 2
                center_y = y + h // 2

                cv2.rectangle(processed_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                cv2.circle(processed_frame, (center_x, center_y), 5, (0, 0, 255), -1)

                cv2.putText(
                    processed_frame,
                    f"Ball:({center_x}, {center_y})",
                    (center_x - 60, center_y - 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2,
                )

                cv2.putText(
                    processed_frame,
                    f"Square :{int(area)}",
                    (center_x - 60, center_y + 20),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    2,
                )
                # data.append(Calculate(center_x, center_y, self.ratio(h, w)))
                data.append([x,y,w,h])
        return processed_frame, ma, data


# 接受传入的图像，发送处理后的图像，轮廓，中心点，掩膜
##def main():
##    node = Node()
##    dector = ColorDetector([30, 70, 80], [50, 255, 255], min_area=50)
##    for event in node:
##        if event["type"] == "INPUT":
##            event_id = event["id"]
##            # 处理普通图像或 mask 图像
##            if event_id == "image":
##                image = process_image(event["value"], event["metadata"])
##                if image is not None:
##                    image = cv2.flip(image, 0)
##                    processed_frame, mask, data = dector.process(image)
##                    node.send_output(
##                        "image", pa.array(processed_frame.ravel()), event["metadata"]
##                    )
##                    event["metadata"]["encoding"] = "uint8"
##                    node.send_output("mask", pa.array(mask.ravel()), event["metadata"])
##                    node.send_output("data", Calculate.to_pa_array(data))
##        # elif  event["type"] == "STOP":
##        #     cv2.VideoCapture.release()

cap=None
motors=None
ser=None

CMD_DIR={
    'find':'',
    'advance':'',
    'back':'',
    'turn left':'',
    'turn right':'',
}
def execute_cmd(cmd):
    global motors
    MOVE_SPEED=2500
    TURN_SPEED=1500
    if cmd=='turn_right':
        motors.Rotate_Right()
        motors.set_pwm(TURN_SPEED,TURN_SPEED,TURN_SPEED,TURN_SPEED)
    elif cmd=='turn_left':
        motors.Rotate_Left()
        motors.set_pwm(TURN_SPEED,TURN_SPEED,TURN_SPEED,TURN_SPEED)
    elif cmd=='advance':
        motors.Advance()
        motors.set_pwm(MOVE_SPEED,MOVE_SPEED,MOVE_SPEED,MOVE_SPEED)
    elif cmd=='back':
        motors.Back()
        motors.set_pwm(MOVE_SPEED,MOVE_SPEED,MOVE_SPEED,MOVE_SPEED)
    elif cmd=='stop':
        motors.Stop()
    elif cmd=='catch':
        global ser
        global cap
        motors.Stop()
        cap.release()
        ser.write(b'@u \n')
        time.sleep(6)
        ser.write(b'@d \n')
        time.sleep(8)
        cap = cv2.VideoCapture(0)
        
    

def test():
    IMGW=640  #摄像头捕获图片长度
    IMGH=480  #摄像头捕获图片高度
    WIDTH_THRESHOLD=150    #标记区域的长度临界值，达到这个长度表示距离已经到达标记附近
    EDGE_THRESHOLD=(IMGW-WIDTH_THRESHOLD)/2   #标记区域左右边界临界值，用于判断标记区域偏左还是偏右
    EDGE_DEVIATION=40   #左右边界差距的误差范围，差距小于这个值就认为是在中间
    WIDTH_DEVIATION=10  #长度的误差范围，标记长度处在长度临界值加减误差的范围内，就认为是到达了捡球合适位置
    
    BALL_COUNT_TIMES=100
    BALL_COUNT_THRESHOLD=70

    dector = ColorDetector([30, 70, 80], [50, 255, 255], min_area=300,max_area=40000)

    # 打开默认摄像头（通常是设备上的第一个摄像头）
    global cap
    cap = cv2.VideoCapture(0)
    # 图片形状 640*480
    if not cap.isOpened():
        print("无法打开摄像头")
        exit()
    
    global motors
    motors = PCA9685Motor(1500,1500,1500,1500)
    global ser
    ser=serial.Serial('/dev/ttyAMA2',9600)
    
    ball_count=0
    times_count=0
    
    find_status=0 # 0:not find, 1:turn and find, 2:stop turn and find
    NOT_FIND=0
    TURN_FIND=1
    STOP_TURN_FIND=2
    
    TURN_FIND_TIME_THRESHOLD = 60*1
    STOP_TURN_FIND_TIME_THRESHOLD = 60*5
    
    last_time=int(time.time()) # second
    now_time =int(time.time())

    while True:
        # 逐帧捕获
        ret, frame = cap.read()
        image = cv2.flip(frame, 0)
        processed_frame, mask, data = dector.process(image)
        # 如果正确读取帧，ret 为 True
        if not ret:
            print("无法读取摄像头画面")
            break

        # 显示当前帧
        # cv2.imshow("Camera Feed", frame)
        # cv2.imshow("processed_frame", processed_frame)
        # cv2.imshow("mask", mask)
        
        cmd=None
        
        if len(data)<=0:
            # motors.Stop()
            cmd='turn_left'
            if find_status==NOT_FIND:
                find_status=TURN_FIND
            elif find_status==TURN_FIND:
                now_time=int(time.time())
                if now_time-last_time>=TURN_FIND_TIME_THRESHOLD:
                    find_status=STOP_TURN_FIND
                    cmd='stop'
            elif find_status==STOP_TURN_FIND:
                now_time=int(time.time())
                if now_time-last_time>=STOP_TURN_FIND_TIME_THRESHOLD:
                    find_status=TURN_FIND
                

        for xywh in data[:1]:
            find_status=NOT_FIND
            #图片从左上角开始为0，0，横向为x，纵向为y
            
            leftEdge=int(xywh[0])
            rightEdge=IMGW-int(xywh[2])-int(xywh[0])
            width=int(xywh[2])

            difference=leftEdge-rightEdge
            print('dif: ',difference)
            print('wid: ',width)
            
            if difference<-1*EDGE_DEVIATION:#右边距距离更小，应右转
                cmd='turn_right'# "右转"
            elif difference>EDGE_DEVIATION:#左边距距离更小，应左转
                cmd='turn_left' # "左转"
            elif width<WIDTH_THRESHOLD-WIDTH_DEVIATION:#长度较小，说明离标记较远，应前进
                cmd='advance'   # "前进"
            elif width>WIDTH_THRESHOLD+WIDTH_DEVIATION:#长度较大，说明离标记较近，应后退
                cmd='back'      # "后退"
            else:#所有距离都符合，表示来到了标记合适位置，可以抓取
                cmd='stop'
                ball_count+=1
                if times_count==0:
                    times_count=1
        
        if times_count>0:
            times_count+=1
            if times_count>=BALL_COUNT_TIMES:
                if ball_count>=BALL_COUNT_THRESHOLD:
                    cmd='catch'# '抓取'
                ball_count=0
                times_count=0
        print(cmd)
        execute_cmd(cmd)

        # 按下键盘上的 'q' 键退出循环
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    motors.Stop()
    ser.close()
    # 释放摄像头资源
    cap.release()
    # 关闭所有 OpenCV 窗口
    cv2.destroyAllWindows()


# 使用示例
if __name__ == "__main__":
##    main()
    test()
