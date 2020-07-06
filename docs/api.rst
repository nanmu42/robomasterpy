.. _api:

API
============

If you are new to RoboMasterPy, you may want to read :ref:`Quick Start <quickstart>` firstly.

The API documentation here are in Chinese-English contraposition style.

Receive IP Broadcast
------------------------------

Robomaster broadcasts its IP address under router mode.

.. autofunction:: robomasterpy.get_broadcast_ip

Commander
------------------

Commander is a SDK(client) for Robomaster TCP text API.

.. autoclass:: robomasterpy.Commander
   :members:
   :inherited-members:
   :undoc-members:

Framework
--------------------

For a brief introduction on framework, read :ref:`Quick Start <quickstart>`.

Hub
^^^^^^^^^^^^

Hub is where workers live, its API is declarative rather than imperative.

.. autoclass:: robomasterpy.framework.Hub
   :members:
   :inherited-members:
   :undoc-members:

Worker
^^^^^^^^^^^^^^^^

.. autoclass:: robomasterpy.framework.Worker
   :members:
   :inherited-members:
   :undoc-members:

Sugared Workers
^^^^^^^^^^^^^^^^

RoboMasterPy comes with some sugared worker to satisfy common needs, their names are self-explanatory.

You can always inherit and implement your own worker if sugared ones do not cover your need.

.. autoclass:: robomasterpy.framework.Vision
   :members:

.. autoclass:: robomasterpy.framework.PushListener
   :members:

.. autoclass:: robomasterpy.framework.EventListener
   :members:

.. autoclass:: robomasterpy.framework.Mind
   :members:

Helpers
---------------------------------------

Helpers are some good-to-have features that may be useful for your task.

Distance Measure
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some helpers for distance measure and analysis on video stream.

.. autofunction:: robomasterpy.measure.pinhole_distance
.. autofunction:: robomasterpy.measure.distance_decomposition