# RoboMasterPy

[English](https://github.com/nanmu42/robomasterpy/blob/master/README.md) | **中文**

[![文档编译状态](https://readthedocs.org/projects/robomasterpy/badge/?version=latest)](https://robomasterpy.nanmu.me/zh_CN/latest/)
[![](https://img.shields.io/pypi/l/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/wheel/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/pyversions/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)

**RoboMasterPy** 是大疆机甲大师的Python SDK和编程框架：

* Python SDK：遥测和控制机甲大师；
* 编程框架：提供和规范控制流和数据流，解决视频流拉取解析、事件和推送拉取解析等常见需求，解耦控制循环、日志打印、安全退出等模板代码，降低心智负担和劳动强度，让开发者可以专注于业务逻辑的实现。

SDK（客户端）的使用方式比较直观：

```python
>>> import robomasterpy as rm

# 路由器模式下，可自动获取机甲大师的IP
>>> cmd = rm.Commander()

# 查询机甲大师的固件的API版本
>>> cmd.version()
'version 00.00.00.60'

>>> cmd.get_robot_mode()
'chassis_lead'

# 执行前请确保你的机甲大师有足够的行动空间
>>> cmd.chassis_move(x=-1, z=30)
'ok'

# 开启视频推流，
# 视频流可以使用RoboMasterPy编程框架进行获取和处理。
>>> cmd.stream(rm.SWITCH_ON)
'ok'

# 开启云台姿态推送，设定频率为5Hz，
# 推送可以使用RoboMasterPy编程框架进行获取和处理。
>>> cmd.gimbal_push_on(attitude_freq=5)
'ok'

# 当心飞弹！
>>> cmd.blaster_fire()
'ok'
```

框架让你能够更容易地创建复杂应用，例如：

* [使用键盘控制你的机甲大师](https://github.com/nanmu42/robo-playground/blob/master/README.Chinese.md#%E4%BD%BF%E7%94%A8%E9%94%AE%E7%9B%98%E6%8E%A7%E5%88%B6%E4%BD%A0%E7%9A%84%E6%9C%BA%E7%94%B2%E5%A4%A7%E5%B8%88ep)；
* [让你的机甲大师变身为守门员](https://github.com/nanmu42/robo-playground/blob/master/README.Chinese.md#%E8%AE%A9%E4%BD%A0%E7%9A%84%E6%9C%BA%E7%94%B2%E5%A4%A7%E5%B8%88ep%E5%8F%98%E8%BA%AB%E4%B8%BA%E5%AE%88%E9%97%A8%E5%91%98)。
* [更多示例](https://github.com/nanmu42/robo-playground)

![RoboMasterPy 守门员](https://user-images.githubusercontent.com/8143068/82755582-186d5700-9e07-11ea-9c08-1ff1d82e7a7e.jpg)

## 安装

RoboMasterPy 需要Python 3.6或更高版本。

### 安装依赖

如果你正使用Python 3.6.x，你需要额外安装`dataclasses`（已预置在Python 3.7及以上版本）：

```bash
pip install dataclasses
```

安装你熟悉的OpenCV发行版，推荐：

```bash
# 如果你偏爱conda环境
conda install -c conda-forge opencv

# 如果你只使用pip
pip install opencv-contrib-python
```

### 安装RoboMasterPy

```bash
pip install robomasterpy
```

大功告成！

## 用户指南

https://robomasterpy.nanmu.me/zh_CN/latest/

文档提供中英双语。

Read the Docs 慷慨地提供了文档托管服务。

## 健康和安全警示

* 你的机甲大师可能会伤到人或者宠物，打破东西或者弄坏自己；
* 确保机甲大师有足够的行动空间，确保地面平整且没有障碍；
* 慢慢来，避免在调试代码时使用高速档位；
* 使用缓冲垫；
* 注意安全，玩的愉快！

## 法务

RoboMasterPy 是一个爱好者作品，和DJI没有关系。

大疆、大疆创新、DJI、 RoboMaster是深圳市大疆创新科技有限公司的商标。

## 致谢

RoboMasterPy是在机甲大师EP开发者比赛中孵化的，作者对DJI提供的硬件和技术支持表示感谢。

## 许可

RoboMasterPy 基于MIT许可发布，
您只需要保留署名和版权信息（LICENSE）即可自由使用本软件。