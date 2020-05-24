# RoboMasterPy

**English** | [中文](https://github.com/nanmu42/robomasterpy/blob/master/README.Chinese.md)

[![Documentation Status](https://readthedocs.org/projects/robomasterpy/badge/?version=latest)](https://robomasterpy.nanmu.me/en/latest/?badge=latest)
[![](https://img.shields.io/pypi/l/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/wheel/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)
[![](https://img.shields.io/pypi/pyversions/robomasterpy.svg)](https://pypi.org/project/robomasterpy/)

**RoboMasterPy** is a Python library and framework for RoboMaster EP.

The library(client) is straightforward to use:

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

The framework deals with video streaming, push and event,
you can build your controlling logic basing on it, for example(TODO: add links):

* Drive your robomaster using keyboard;
* Make your robomaster a goalkeeper.

## Installation

RoboMasterPy requires Python 3.6 and above.

```bash
pip install robomasterpy
```

If you are using Python 3.6.x, you need to install `dataclasses`:

```bash
pip install dataclasses
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