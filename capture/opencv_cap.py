import cv2
import numpy as np
##from dora import Node
import pyarrow as pa
import sys
import os
from dora import Node

def main():
    node = Node()
    IMGW=640  #摄像头捕获图片长度
    IMGH=480  #摄像头捕获图片高度

    # 打开默认摄像头（通常是设备上的第一个摄像头）
    cap = cv2.VideoCapture(1)
    # 图片形状 640*480
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print("无法打开摄像头")
        exit()
    ret, frame = cap.read()
    if not ret:
        node.send_output("image", frame, event["metadata"]) 
    
    # 释放摄像头资源
    cap.release()
    # 关闭所有 OpenCV 窗口
    cv2.destroyAllWindows()


# 使用示例
if __name__ == "__main__":
    main()
