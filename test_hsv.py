import cv2
import numpy as np
import pyarrow as pa
import sys
import os
from flask import Flask, request, jsonify, send_from_directory, render_template, url_for, redirect
from waitress import serve

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 现在可以正常导入
from untils.untils import Calculate
import base64

app = Flask(__name__)


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
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=2)
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
                area > self.min_area and area < self.max_area and circularity > 0.80
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

@app.route("/")
def index():
    return render_template("index-test.html")

@app.route("/api/process-image", methods=['POST'])
def api_process():
    data=request.get_json()
    print(data)
    dector = ColorDetector([data['h_min'], data['s_min'], data['v_min']], [data['h_max'], data['s_max'], data['v_max']], min_area=300,max_area=40000)
    frame = cv2.imread('./frame/1747468303.jpg')#1747468211.jpg
    processed_frame, mask, data = dector.process(frame)
    ret, jpeg = cv2.imencode(".jpg", mask)
    if ret:
        # 将 JPEG 转换为 Base64 字符串
        jpeg_base64 = base64.b64encode(jpeg.tobytes()).decode("utf-8")
        # 发送到前端
        return {"imageData": jpeg_base64}
    return {}

def test_server():
    global app
    serve(app, host='0.0.0.0', port=80)


def test_hsv():
    IMGW=640  #摄像头捕获图片长度
    IMGH=480  #摄像头捕获图片高度
    WIDTH_THRESHOLD=200    #标记区域的长度临界值，达到这个长度表示距离已经到达标记附近
    EDGE_THRESHOLD=(IMGW-WIDTH_THRESHOLD)/2   #标记区域左右边界临界值，用于判断标记区域偏左还是偏右
    EDGE_DEVIATION=20   #左右边界差距的误差范围，差距小于这个值就认为是在中间
    WIDTH_DEVIATION=20  #长度的误差范围，标记长度处在长度临界值加减误差的范围内，就认为是到达了捡球合适位置

    #[30, 70, 80], [50, 255, 255]
    #[22, 147, 29], [70, 255, 255]
    hsvs=[[20,105,29],[70,255,255]]
    dirname=str(hsvs)
    dector = ColorDetector(hsvs[0],hsvs[1], min_area=300,max_area=40000)

    if not os.path.exists('./test/'+dirname):
        os.makedirs('./test/'+dirname+'/process', exist_ok=True)
        os.makedirs('./test/'+dirname+'/mask', exist_ok=True)

    imgs=os.listdir('./frame')
    for img in imgs:
        # 逐帧捕获
        frame = cv2.imread('./frame/'+img)
        processed_frame, mask, data = dector.process(frame)

        cv2.imshow("processed_frame", processed_frame)
        cv2.imshow("mask", mask)
        cv2.imwrite('./test/'+dirname+'/process/'+img,processed_frame)
        cv2.imwrite('./test/'+dirname+'/mask/'+img,mask)
    cv2.destroyAllWindows()

        # for xywh in data[:1]:
        #     #图片从左上角开始为0，0，横向为x，纵向为y
            
        #     leftEdge=int(xywh[0])
        #     rightEdge=IMGW-int(xywh[2])-int(xywh[0])
        #     width=int(xywh[2])

        #     difference=leftEdge-rightEdge
        #     cmd=None
        #     if difference<-1*EDGE_DEVIATION:#左边距距离更小，应左转
        #         cmd="左转"
        #         # motors.Rotate_Left()
        #     elif difference>EDGE_DEVIATION:#右边距距离更小，应右转
        #         cmd="右转"
        #         # motors.Rotate_Right()
        #     elif width<WIDTH_THRESHOLD-WIDTH_DEVIATION:#长度较小，说明离标记较远，应前进
        #         cmd="前进"
        #         # motors.Advance()
        #     elif width>WIDTH_THRESHOLD+WIDTH_DEVIATION:#长度较大，说明离标记较近，应后退
        #         cmd="后退"
        #         # motors.Back()
        #     else:#所有距离都符合，表示来到了标记合适位置，可以抓取
        #         cmd="抓取"
        #     print('dif: ',difference)
        #     print('wid: ',width)
        #     print(cmd)

        # # 按下键盘上的 'q' 键退出循环
        # if cv2.waitKey(1) & 0xFF == ord("q"):
        #     break

# 使用示例
if __name__ == "__main__":
##    main()
    # test_hsv()
    test_hsv()
