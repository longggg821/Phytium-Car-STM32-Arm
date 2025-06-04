from dora import Node
from tennis_cv import TennisColorDetector

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

# 接受传入的图像，发送处理后的图像，轮廓，中心点，掩膜
def main():
    node = Node()
    dector = TennisColorDetector([20,105,29],[70,255,255], min_area=50)
    for event in node:
        if event["type"] == "INPUT":
            event_id = event["id"]
            # 处理普通图像或 mask 图像
            if event_id == "image":
                image = process_image(event["value"], event["metadata"])
                if image is not None:
                    # image = cv2.flip(image, 0)
                    processed_frame, mask, data = dector.process(image)
                    node.send_output(
                        "image", pa.array(processed_frame.ravel()), event["metadata"]
                    )
                    event["metadata"]["encoding"] = "uint8"
                    node.send_output("mask", pa.array(mask.ravel()), event["metadata"])
                    node.send_output("data", Calculate.to_pa_array(data))
        # elif  event["type"] == "STOP":
        #     cv2.VideoCapture.release()

if __name__ == "__main__":
    main()
