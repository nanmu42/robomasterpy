RoboMasterPy: Python library and framework for RoboMaster EP
========================================

Release v\ |release|. (:ref:`Installation <install>`)

.. image:: https://img.shields.io/pypi/l/robomasterpy.svg
    :target: https://pypi.org/project/robomasterpy/

.. image:: https://img.shields.io/pypi/wheel/robomasterpy.svg
    :target: https://pypi.org/project/robomasterpy/

.. image:: https://img.shields.io/pypi/pyversions/robomasterpy.svg
    :target: https://pypi.org/project/robomasterpy/

**RoboMasterPy** is a Python library and framework for RoboMaster EP.

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
you can build your controlling logic basing on it, for example(TODO: add links):

* Drive your robomaster using keyboard;
* Make your robomaster a goalkeeper.

The User Guide
--------------

.. toctree::
   :maxdepth: 2

   install
   quickstart
   api

Health and Safety Notice
--------------

* Your Robomaster may hurt people or pet, break stuffs or itself;
* Make sure your RoboMaster has enough room to move; make sure the ground is clear;
* Start slowly, avoid using high speed for debugging;
* Use cushion;
* Stay safe and have fun!