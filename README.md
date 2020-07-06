# RoboMasterPy

**English** | [中文](https://github.com/nanmu42/robomasterpy/blob/master/README.Chinese.md)

[![Documentation Status](https://readthedocs.org/projects/robomasterpy/badge/?version=latest)](https://robomasterpy.nanmu.me/en/latest/)
[![](https://img.shields.io/pypi/l/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/wheel/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/pyversions/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)

**RoboMasterPy** is a RoboMaster Python SDK and framework:

* Python SDK: inspect and control your Robomaster, remotely;
* framework: development framework providing and regularising control flow and data flow, resolving common needs like pulling and parsing on video stream, events and pushes, decoupling boilerplate codes like controlling loop, logging, graceful shutdown. You may rely on the framework, implement your business logic with ease of mind and less manual labor.

The SDK(client) is straightforward to use:

```python
>>> import robomasterpy as rm

# IP of RoboMaster is detected under router mode
>>> cmd = rm.Commander()

# check RoboMaster's API version
>>> cmd.version()
'version 00.00.00.60'

>>> cmd.get_robot_mode()
'chassis_lead'

# ensure your Robomaster has enough room to move
>>> cmd.chassis_move(x=-1, z=30)
'ok'

# activate video streaming,
# which can be handled by the framework.
>>> cmd.stream(rm.SWITCH_ON)
'ok'

# activate gimbal attitude push at 5Hz,
# which can be handled by the framework.
>>> cmd.gimbal_push_on(attitude_freq=5)
'ok'

# Watch out!
>>> cmd.blaster_fire()
'ok'
```

The framework lets you create complicated application easier, e.g.:

* [Drive your robomaster using keyboard](https://github.com/nanmu42/robo-playground#drive-your-robomaster-using-keyboard);
* [Make your robomaster a goalkeeper](https://github.com/nanmu42/robo-playground#make-your-robomaster-a-goalkeeper);
* [More examples](https://github.com/nanmu42/robo-playground)

![RoboMasterPy Goalkeeper](https://user-images.githubusercontent.com/8143068/82755582-186d5700-9e07-11ea-9c08-1ff1d82e7a7e.jpg)

## Installation

RoboMasterPy requires Python 3.6 and above.

### Install Dependencies First

If you are using Python 3.6.x, you need to install `dataclasses`, which is already included in Python 3.7 and better:

```bash
pip install dataclasses
```

Install OpenCV of your flavor, suggestion::

```bash
# if you are using conda
conda install -c conda-forge opencv

# if you are using pip only
pip install opencv-contrib-python
```

### Install RoboMasterPy

```bash
pip install robomasterpy
```

## User Guide

https://robomasterpy.nanmu.me/

Documentation is generously hosted by Read the Docs.

## Health and Safety Notice

* Your Robomaster may hurt people or pet, break stuffs or itself;
* Make sure your RoboMaster has enough room to move; make sure the ground is clear;
* Start slowly, avoid using high speed for debugging;
* Use cushion;
* Stay safe and have fun!

## Paperwork

RoboMasterPy is a fan work, and it has no concern with DJI.

DJI, RoboMaster are trademarks of SZ DJI Technology Co., Ltd.

## Acknowledgement

RoboMasterPy was incubated during a RoboMaster EP developing contest. The author would like to thank DJI for hardware and technical support.

## License

RoboMasterPy is released under MIT license.