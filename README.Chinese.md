# RoboMasterPy

[English](https://github.com/nanmu42/robomasterpy/blob/master/README.md) | **中文**

[![](https://img.shields.io/pypi/l/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/wheel/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/pyversions/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)

**RoboMasterPy** 是一个适用于机甲大师EP的Python库和编程框架。

下面是运用RoboMasterPy Python库的一个简单示例：

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

![RoboMasterPy 守门员](https://user-images.githubusercontent.com/8143068/82755582-186d5700-9e07-11ea-9c08-1ff1d82e7a7e.jpg)

RoboMasterPy编程框架抽象了视频流、推送和事件的获取，模块之间的信息通讯，
提供了一个高层的逻辑组织方式，期望降低开发者的心智负担，提升开发效率。

一些例子：

* [使用键盘控制你的机甲大师EP](https://github.com/nanmu42/robo-playground/blob/master/README.Chinese.md#%E4%BD%BF%E7%94%A8%E9%94%AE%E7%9B%98%E6%8E%A7%E5%88%B6%E4%BD%A0%E7%9A%84%E6%9C%BA%E7%94%B2%E5%A4%A7%E5%B8%88ep)；
* [让你的机甲大师变身为守门员](https://github.com/nanmu42/robo-playground/blob/master/README.Chinese.md#%E8%AE%A9%E4%BD%A0%E7%9A%84%E6%9C%BA%E7%94%B2%E5%A4%A7%E5%B8%88ep%E5%8F%98%E8%BA%AB%E4%B8%BA%E5%AE%88%E9%97%A8%E5%91%98)。
* [更多示例](https://github.com/nanmu42/robo-playground)

## 安装

RoboMasterPy 需要Python 3.6或更高版本。

```bash
pip install robomasterpy
```

如果你正使用Python 3.6.x，你需要额外安装`dataclasses`：

```bash
pip install dataclasses
```

## 用户指南

https://robomasterpy.nanmu.me/

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