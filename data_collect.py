import cv2
import numpy as np
##from dora import Node
import pyarrow as pa
import sys
import os

import time

# 添加项目根目录到 Python 路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 现在可以正常导入
from untils.untils import Calculate

def test():
    num = 0
    cap = cv2.VideoCapture(1)
    # 图片形状 640*480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    if not cap.isOpened():
        print("无法打开摄像头")
        exit()

    while True:
        # 逐帧捕获
        ret, frame = cap.read()
        # 如果正确读取帧，ret 为 True
        if not ret:
            print("无法读取摄像头画面")
            break

        # 显示当前帧
        cv2.imshow("Camera Feed", frame)
        # 按下键盘上的 'q' 键退出循环
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord('p'):
            cv2.imwrite('./imgs/2全/'+str(int(time.time()*1000))+'.jpg',frame)
            num += 1
            print('img saved ',num)

    # 释放摄像头资源
    cap.release()
    # 关闭所有 OpenCV 窗口
    cv2.destroyAllWindows()


# 使用示例
if __name__ == "__main__":
##    main()
    test()
