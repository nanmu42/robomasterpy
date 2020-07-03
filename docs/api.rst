.. _api:

API
============

Receive IP Broadcast
------------------------------

Robomaster broadcast its IP address under router mode.

.. autofunction:: robomasterpy.get_broadcast_ip

Commander
------------------

Commander is a SDK(client) for Robomaster TCP API.

.. autoclass:: robomasterpy.Commander
   :members:
   :inherited-members:
   :undoc-members:

Framework
--------------------

The framework deals with video streaming, push and event,
you can build your controlling logic basing on it, for example:

* `Drive your robomaster using keyboard <https://github.com/nanmu42/robo-playground#drive-your-robomaster-using-keyboard>`_;
* `Make your robomaster a goalkeeper <https://github.com/nanmu42/robo-playground#make-your-robomaster-a-goalkeeper>`_.

.. autoclass:: robomasterpy.framework.Hub
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: robomasterpy.framework.Worker
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: robomasterpy.framework.Vision
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: robomasterpy.framework.PushListener
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: robomasterpy.framework.EventListener
   :members:
   :inherited-members:
   :undoc-members:

.. autoclass:: robomasterpy.framework.Mind
   :members:
   :inherited-members:
   :undoc-members:

Helpers for Measure
-----------------------------

Some helpers for distance measure and analysis on video stream.

.. autofunction:: robomasterpy.measure.pinhole_distance
.. autofunction:: robomasterpy.measure.distance_decomposition