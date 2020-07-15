.. _api:

API文档
============

如果你刚刚才接触 RoboMasterPy，建议你从 :ref:`新手教程 <quickstart>` 开始。

这里的 API 文档以中英对照的方式提供。

接收 IP 广播
----------------------------------------------------

在路由器模式下，机甲大师会广播其IP地址。

.. autofunction:: robomasterpy.get_broadcast_ip

Commander：遥测和控制
--------------------------------------------------------

Commander 是机甲大师TCP文本API的客户端。

.. autoclass:: robomasterpy.Commander
   :members:
   :inherited-members:
   :undoc-members:

编程框架
--------------------------------------------

在 :ref:`新手教程 <quickstart>` 中有对编程框架的简要介绍和示例。

Hub：聚合你的业务逻辑
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Hub是注册Worker的地方，它的API更偏向于声明式而非命令式。

.. autoclass:: robomasterpy.framework.Hub
   :members:
   :inherited-members:
   :undoc-members:

Worker：承载你的业务逻辑
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: robomasterpy.framework.Worker
   :members:
   :inherited-members:
   :undoc-members:

预置Worker：满足常见需求
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

RoboMasterPy 预置了一些 Worker 以应对常见需求。

当预置的 Worker 不能满足你的需求时，你可以继承 ``Worker`` 创建自己的子类来完成你的任务。

.. autoclass:: robomasterpy.framework.Vision
   :members: __init__

.. autoclass:: robomasterpy.framework.PushListener
   :members: __init__

.. autoclass:: robomasterpy.framework.EventListener
   :members: __init__

.. autoclass:: robomasterpy.framework.Mind
   :members: __init__

帮手函数/常量
---------------------------------------

帮手函数/常量是一些可能可以帮助你完成特定任务的工具。

距离的度量和分析
^^^^^^^^^^^^^^^^^^^^^^^^^^^

以视频流为依据度量和分析物体到机甲的距离。

.. autofunction:: robomasterpy.measure.pinhole_distance
.. autofunction:: robomasterpy.measure.distance_decomposition