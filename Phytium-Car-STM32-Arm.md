# `Phytium-Car-STM32-Arm`

## :hammer_and_wrench:项目部署

---

项目使用了`dora-rs`作为启动以及机器人各节点的管理，配置项目需要先安装`dora-rs`，而`dora-rs`是基于`Rust`语言的，因此还需要先安装`Rust`。具体安装方式可以参考：

1. [安装 - Rust程序设计语言 简体中文版](https://kaisery.github.io/trpl-zh-cn/ch01-01-installation.html)

2. [DORA机器人中间件学习教程（1）--Dora-rs安装](https://blog.csdn.net/crp997576280/article/details/135368894)

> [!NOTE]
>
> 如果是Windows电脑，在参考第2篇文章安装`dora-rs`时可以参考文章中的2.2从源码编译安装

## :zap: `dora-rs`使用​

---

- ## **数据流文件介绍**

  **`dora`** 使用数据流**`yaml`**文件来指定项目运行过程中数据应该怎么传递，项目的启动也是通过**`yaml`**文件。下面是关于数据流**`yaml`**文件的一些介绍，这里只介绍跟项目有关的部分，详细介绍可参考 **[`指南 | dora-rs`](https://dora-rs.ai/zh-CN/docs/guides/)**。

  ```yaml
  nodes:                           # 节点数组
    - id: opencv-video-capture     # 表示一个节点的id，用于在其他节点输入时标识数据来源
      build: pip install opencv-video-capture # 节点构建方式，用到的比较少，只有dora build指令会用到
      path: opencv-video-capture   # 节点的运行路径或指令，如果用python控制一个节点，则写明.py文件路径
      inputs:                      # 表示节点需要什么输入数据
        tick: dora/timer/millis/50 # 这是一种特殊输入，是一种定时启动，这里表示50ms启动一次
      env:                         # 特殊参数，一般用不到
        PATH: 0 # optional, default is 0
      outputs:                     # 表示节点输出数据
        - image                    # 节点输出的数据名称，需要和代码中设置的输出数据名称一致
    - id: color
      path: mycv/color.py
      inputs: 
        image: cap/image           # 输入的参数[自定义参数名]: [参数来源节点id]/[数据名称]，可以设置多个
      outputs: 
        - image
        - data
        - mask
  ```

  

- ## **指令介绍**

  详细的指令使用可以参考 **[`cli | dora-rs`](https://dora-rs.ai/zh-CN/docs/api/cli/)**，这里只介绍几个跟项目有关的指令，且是比较精简的格式。

   1. ### 在本地模式（默认配置）生成协调器和守护进程

      ```cmd
      dora up
      ```

   2. ### 从给定数据流路径启动

      ```cmd
      dora start <PATH>
      ```

      <PATH>  数据流描述符文件的路径如`./car_cv.yaml`

   3. ### 销毁运行中的协调器和守护进程

      ```cmd
      dora destroy
      ```

      如果一些数据流还在运行，他们将首先被停止。

   4. ### 对给定数据流生成可视化流程图

      ```cmd
      dora graph <PATH> --open
      ```

      <PATH>  数据流描述符文件的路径如`./car_cv.yaml`

      `--open`生成后直接在浏览器打开

      这条指令用于生成给定数据流文件数据流向图，即把数据流可视化。

      可用于检测数据流文件是否正确编写。

      生成的是一个`html`文件，也可以不使用`--open`，直接在数据流`yaml`文件的目录下找到生成的`html`文件

- ## **运行过程**

  1. ### 先运行第1条指令`dora up`，开启生成协调器和守护进程。

     这条指令是后台运行，在显示`started dora coordinator`和`started dora daemon`后控制台就会结束运行，这时协调器和守护进程已经成功在后台运行，因此这条指令运行后如果没有运行摧毁指令的话，只需要运行这一次，不需要重复运行。

  2. ### 运行第2条指令`dora start <PATH>`，从数据流文件启动项目。

     启动后控制台会输出调试信息，Python的报错也会在调试信息中显示，如果需要结束运行，按`Ctrl+c`即可。

     如果没有主动结束指令的运行，且数据流中使用的是**`tick: dora/timer/millis/*`**作为定时触发，则指令会一直运行；如果停止运行，则需要阅读调试输出看是否有错误。

  3. ### 结束项目运行

     用`Ctrl+c`结束当前运行的数据流，如果不再需要运行项目，则需要通过第3条指令`dora destroy`销毁运行中的***协调器和守护进程***，直接关闭控制台窗口是无法关闭这两个后台的。当然，如果关闭了当前的控制台但是未摧毁***协调器和守护进程***，也可以打开一个新的控制台，并运行第3条指令来摧毁。

## 📚项目结构

---

```shell
├─capture # 存放控制摄像头节点的代码
│  │  opencv_cap.py # 摄像头控制节点，在数据流中传入拍摄的图片
│
├─common
│  │  __init__.py  # 模块初始化
│  │  calculate.py # 用于存储和处理目标检测结果的数据类
│  │  move_data.py # 规范移动数据
│  │  test_move_data.py # MoveData的单元测试类
│  │  view.py      # 输出数据给前端，目前数据和MoveData一致
│
├─motor
│  │  main.py   # dora控制电机节点的文件，有多个电机控制类，因此统一电机节点代码在main中
│  │  Motor.py  # 电机控制类，ModbusMotor是控制大车底盘，PCA9685是控制桌面小车底盘
│  │  pyproject.toml
│  │  test.py   # 测试用
│
```

