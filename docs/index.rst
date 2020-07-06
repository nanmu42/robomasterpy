RoboMasterPy: RoboMaster Python SDK and framework
=====================================================================

Release v\ |release|. (:ref:`Installation <install>`)

.. image:: https://img.shields.io/pypi/l/robomasterpy.svg
    :target: https://pypi.org/project/robomasterpy/

.. image:: https://img.shields.io/pypi/wheel/robomasterpy.svg
    :target: https://pypi.org/project/robomasterpy/

.. image:: https://img.shields.io/pypi/pyversions/robomasterpy.svg
    :target: https://pypi.org/project/robomasterpy/

**RoboMasterPy** is a RoboMaster Python SDK and framework:

* Python SDK: inspect and control your Robomaster, remotely;
* framework: development framework providing and regularising control flow and data flow, resolving common needs like pulling and parsing on video stream, events and pushes, decoupling boilerplate codes like controlling loop, logging, graceful shutdown. You may rely on the framework, implement your business logic with ease of mind and less manual labor.

-------------------

The library(client) is straightforward to use::

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

The framework deals with video streaming, push and event,
provides a high-level interface for controlling and communication.
You can build your controlling logic basing on it, for example:

* `Drive your robomaster using keyboard <https://github.com/nanmu42/robo-playground#drive-your-robomaster-using-keyboard>`_;
* `Make your robomaster a goalkeeper <https://github.com/nanmu42/robo-playground#make-your-robomaster-a-goalkeeper>`_;
* `More examples <https://github.com/nanmu42/robo-playground>`_.

.. image:: https://user-images.githubusercontent.com/8143068/82755582-186d5700-9e07-11ea-9c08-1ff1d82e7a7e.jpg
   :alt: RoboMasterPy Goalkeeper

User Guide
--------------------------------

.. toctree::
   :maxdepth: 4

   install
   quickstart
   api

Health and Safety Notice
--------------------------------------------------------------

* Your Robomaster may hurt people or pet, break stuffs or itself;
* Make sure your RoboMaster has enough room to move; make sure the ground is clear;
* Start slowly, avoid using high speed for debugging;
* Use cushion;
* Stay safe and have fun!

Paperwork
------------------

RoboMasterPy is a fan work, and it has no concern with DJI.

DJI, RoboMaster are trademarks of SZ DJI Technology Co., Ltd.

Acknowledgement
-------------------------------

RoboMasterPy was developed during a RoboMaster EP developing contest. The author would like to thank DJI for hardware and technical support.

License
--------------

RoboMasterPy is released under MIT license.