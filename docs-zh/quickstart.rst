.. _quickstart:

快速入门
============

本教程会带你熟悉RoboMasterPy的组件，以及它们的概念、关系和功能。

RoboMasterPy由三部分组成，SDK、框架、帮手函数/常量。

* SDK提供对RoboMaster文本API近乎一对一的映射，你可以用它畅快地对机甲进行遥测和控制；
* 框架会调用你编写的代码，它会处理控制循环、数据流、视频流拉取解析、推送和事件的接收和解析、日志打印等等和业务无关的部分；
* 帮手函数/常量是一些可能可以帮助你完成特定任务的工具。

SDK
---------------------

创建一个 ``Commander`` 以遥测和控制你的机甲::

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

一般情况下，遥测用的方法都以 ``get_`` 开头。你可以在 :ref:`API 文档 <api>` 中看到完整的方法列表。

关于 ``Commander`` ，下面是一些值得注意的地方：

* 在USB模式下，机甲的IP固定为 ``192.168.42.2`` ，在直连模式下则固定为 ``192.168.2.1`` ；
* Commander 在完成创建后立即可用。如果创建失败，它会抛出异常；
* 在需要释放 Commander 占据的系统socket资源时，可以调用其 ``close()`` 方法，需要注意的是， ``close()`` 方法并不会发送 ``quit;`` 到机甲，以避免给其他还在工作的 Commander 造成困扰；
* 同时使用多个 Commander 遥测和控制同一台机甲是常见操作；
* Commander 使用了锁来保证同一时间只有一条命令发往机甲，下一条命令在上一条命令返回前不会发送；
* 控制云台的命令一般都会阻塞直到命令完成执行，鉴于此， Commander 的超时最好大一些。

编程框架
--------------------------------

Hub 和 Worker
^^^^^^^^^^^^^^^^^^^^^^^^^^

RoboMasterPy编程框架基于Python的 ``multiprocessing`` 包构建，以避开GIL，利用多核处理器。

在使用框架时，你需要将你的代码按功能分成几个部分，例如视觉、事件处理、控制。每一个部分都会继承 ``Worker`` ，继承出的子类承载有你的业务逻辑。 ``Worker`` 之间使用 ``multiprocessing.Queue`` 进行通讯。

``Worker`` 的子类们都会注册到同一个 ``Hub`` ， ``Hub`` 负责调度和安全退出。

RoboMasterPy 预置了一些 Worker 以应对常见需求。当预置的 Worker 不能满足你的需求时，你可以继承 ``Worker`` 创建自己的子类来完成你的任务。

下面是一个展示 Hub 和 Worker 之间协作的案例，基本上，你的代码的最上层会和本例很类似 ::

    import click
    import multiprocessing as mp
    from robomasterpy import CTX
    import robomasterpy as rm
    from robomasterpy import framework as rmf

    @click.command()
    @click.option('--ip', default='', type=str, help='(Optional) IP of Robomaster EP')
    @click.option('--timeout', default=10.0, type=float, help='(Optional) Timeout for commands')
    def cli(ip: str, timeout: float):
        # manager 负责在进程之间传递信息
        manager: mp.managers.SyncManager = CTX.Manager()

        with manager:
            # hub 是注册 worker 的地方
            hub = rmf.Hub()
            cmd = rm.Commander(ip=ip, timeout=timeout)
            ip = cmd.get_ip()

            # 初始化你的机甲
            cmd.robot_mode(rm.MODE_GIMBAL_LEAD)
            cmd.gimbal_recenter()

            # 开启视频流
            cmd.stream(True)
            # rm.Vision 是一个预置worker，能够拉取和解析视频流，
            # display 是用户自定义的回调函数，会被 rm.Vision 调用。
            hub.worker(rmf.Vision, 'vision', (None, ip, display))

            # 开启事件和推送
            cmd.chassis_push_on(PUSH_FREQUENCY, PUSH_FREQUENCY, PUSH_FREQUENCY)
            cmd.gimbal_push_on(PUSH_FREQUENCY)
            cmd.armor_sensitivity(10)
            cmd.armor_event(rm.ARMOR_HIT, True)
            cmd.sound_event(rm.SOUND_APPLAUSE, True)

            # 数据经由 Queue 在Worker之间流动
            push_queue = manager.Queue(QUEUE_SIZE)
            event_queue = manager.Queue(QUEUE_SIZE)

            # PushListener 和 EventListener 处理机甲的推送和事件，
            # 将解析好的，强类型的结果放到Queue中。
            hub.worker(rmf.PushListener, 'push', (push_queue,))
            hub.worker(rmf.EventListener, 'event', (event_queue, ip))

            # Mind 是一个预置的Worker，你可以给他提供一个无状态的函数作为控制逻辑，
            # 此处这个函数名为 handle_event ，它能从各个 Queue 中消费信息。
            hub.worker(rmf.Mind, 'event-handler', ((push_queue, event_queue), ip, handle_event))

            # Mind 的数目并不受限制，
            # 此处控制逻辑在函数 control 中。
            hub.worker(rmf.Mind, 'controller', ((), ip, control), {'loop': False})

            # run() 会让所有Worker按注册顺序开始工作，直到接收到 SIGTERM 或 SIGINT
            hub.run()


    if __name__ == '__main__':
        cli()

完整的例子可以查看 `这里 <https://github.com/nanmu42/robo-playground/blob/2274f1a311546c47a1705b20bb115cdd05cd8326/drive.py#L158-L198>`_.


数据流
^^^^^^^^^^^^^

上面例子的数据流如图所示：

.. image:: ./assets/drive-data-flow.svg
   :alt: RoboMasterPy data flow of drive.py

一个单向，清晰的数据流能让程序保持简明和可维护。

帮手函数/常量
----------------------------

帮手函数/常量是一些可能可以帮助你完成特定任务的工具。
参阅 :ref:`API 文档 <api>` 。

跟着例子学RoboMasterPy
------------------------------------------

下面是一些可执行的范例，你也许可以用它们作为起点：

* `使用键盘控制你的机甲大师 <https://github.com/nanmu42/robo-playground#drive-your-robomaster-using-keyboard>`_;
* `让你的机甲大师变身为守门员 <https://github.com/nanmu42/robo-playground#make-your-robomaster-a-goalkeeper>`_;
* `更多示例 <https://github.com/nanmu42/robo-playground>`_.