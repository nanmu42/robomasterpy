# -*- coding: utf-8 -*-

# ██████╗  ██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ ██████╗ ██╗   ██╗
# ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
# ██████╔╝██║   ██║██████╔╝██║   ██║██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝██████╔╝ ╚████╔╝
# ██╔══██╗██║   ██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗██╔═══╝   ╚██╔╝
# ██║  ██║╚██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║██║        ██║
# ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝        ╚═╝

import logging
import multiprocessing as mp
import queue
import signal
import socket
import sys
import time
from typing import List, Callable, Tuple, Optional, Iterator

import cv2 as cv

from .client import CTX, LOG_LEVEL, PUSH_PORT, GimbalAttitude, ChassisPosition, ChassisAttitude, ChassisStatus, DEFAULT_BUF_SIZE, EVENT_PORT, ARMOR_HIT, ArmorHitEvent, SOUND_APPLAUSE, SoundApplauseEvent, VIDEO_PORT, Commander


class Worker:
    """
    用户逻辑的载体，继承这个类然后将你的逻辑写到 ``work()`` 方法中即可。
    你的逻辑可以是有状态的或无状态的，如果需要，你可以在继承的新类中使用自定义的任意属性保存你的状态。
    如果你需要打印日志，使用 ``Worker.logger`` 属性。
    使用 ``Hub.worker()`` 将Worker及其参数注册到Hub实例供其调用。

    一个Worker子类一般只做一件事情，多个Worker子类各司其职，相互协作，通过 ``multiprocessing.Queue`` 进行单向通讯，
    最终，负责传感器的Worker的数据会汇聚到负责控制的Worker中，负责控制的Worker再使用 ``Commander`` 向机甲下令。

    RoboMasterPy.framework中提供了多个定制化，开箱即用的Worker以满足
    接收视频流（Vision）、接收事件（EventListener）和推送（PushListener）、汇聚信息控制机甲（Mind）等常见需求，
    请参阅API文档中的“预置Worker”部分。

    Worker takes user's business logic. Inherit this class and write logic code in ``work()`` method.
    A worker can be stateful or stateless, at your choice. You may use some user-defined attributes to store your state if the need arises.
    Use ``Worker.logger`` attribute if some logs need to be printed.
    Register your user-defined worker class along with its params to hub using ``Hub.worker()`` so that hub schedule and calls your logic.

    One Worker subclass nearly always does only one business. Multiple Worker subclasses do their own jobs and cooperate,
    communicate through ``multiprocessing.Queue`` in one-way fashion.
    Data from those subclasses in charge of sensor flows into subclass in charge of controlling, who command your Robomaster by ``Commander``.

    RoboMasterPy.framework provides many customized and out-of-box Worker to cover common usage like
    receiving video stream(vision), receiving events(EventListener) & pushes(PushListener), gathering info and controlling the Robomaster(Mind), etc.
    Please refer to "Sugared Workers" section in API doc.
    """

    QUEUE_TIMEOUT: float = 0.05

    def __init__(self, name: str, out: Optional[mp.Queue], protocol: Optional[str], address: Tuple[str, int], timeout: Optional[float], loop: bool = True):
        """
        初始化Worker，这个方法一般在子类的__init__()方法中调用，不会直接使用。

        Initialize Worker, called in its subclasses's __init__(), seldom used directly.

        :param name: worker实例的名称，这个名称也会作为进程的名称，你应该使用一个有利于调试的，描述性好的名字。
            name of Worker instance, which is also the name of the process. Choose wisely to benefit when debugging.
        :param out: （可选）用于输出产物的multiprocessing.Queue，定义后Worker._outlet()方法可用。
            (Optional) a multiprocessing.Queue to put worker's product. Worker._outlet() is available after this parameter is defined.
        :param protocol: 连接机甲的协议名称，从tcp, udp和None中选择，在tcp和udp选项下Worker._intake()方法可用。
            Protocol to use to connect your Robomaster, choose one in tcp, udp, None. Worker._intake() is available under tcp or udp.
        :param address: 机甲的IP地址和端口号，可从Commander.get_ip()中获得机甲IP，端口号和业务有关，见framework.*_PORT.
            IP and port to Robomaster. IP is available using Commander.get_ip(), and refer to framework.*_PORT for port number.
        :param timeout: tcp或udp的连接超时。   timeout of tcp or udp.
        :param loop: 是否在Worker的生命周期中循环调用work()方法，常见True，在方法提供自己的生命周期管理的时候可选False.
            Whether call work() method in a loop for Worker's lifetime, usually True. Set to False when work() has its own lifecycle management.
        """
        assert name is not None and name != '', 'choose a good name to make life easier'

        self._mu = CTX.Lock()
        with self._mu:
            signal.signal(signal.SIGINT, self._handle_close_signal)
            signal.signal(signal.SIGTERM, self._handle_close_signal)
            self._name: str = name
            self._closed: bool = False
            self._address: Tuple[str, int] = address
            self._out: Optional[mp.Queue] = out
            self._logger: logging.Logger = logging.getLogger(name)
            self._logger.setLevel(LOG_LEVEL)
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s %(name)-12s : %(levelname)-8s %(message)s')
            handler.setFormatter(formatter)
            self._logger.addHandler(handler)
            self._loop: bool = loop

            if protocol == 'tcp':
                self._conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self._conn.settimeout(timeout)
                self._conn.connect(self._address)
            elif protocol == 'udp':
                self._conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                self._conn.settimeout(timeout)
                self._conn.bind(self._address)
            elif protocol is None:
                self._conn: Optional[socket.socket] = None
                pass
            else:
                raise ValueError(f'unknown protocol {protocol}')

    def _handle_close_signal(self, sig, stacks):
        self.close()

    @property
    def closed(self) -> bool:
        """
        当前Worker是否已经永久停止。

        Whether the worker has stopped working eventually.

        :return: True for stopped.
        """
        return self._closed

    def close(self):
        """
        让Worker停止工作，本方法一般由Hub调用。

        Let worker stop. Nearly always called by Hub.
        """
        with self._mu:
            if self.closed:
                return

            self._closed = True
            self.logger.info('signal received, closing...')
            if self._conn is not None:
                self._conn.close()
            if self._out is not None and type(self._out) == mp.Queue:
                self._out.close()

    @property
    def name(self) -> str:
        """
        当前Worker的名字。

        The worker's name.
        """
        return self._name

    def work(self) -> None:
        """
        在本方法中实现你的业务逻辑，你可能需要在这里使用下列方法和属性：

        * 使用 ``self._intake()`` 方法从tcp或udp中获取数据；
        * 使用 ``self._outlet()`` 方法将产物放到out中，注意，如果out被没有即时消费的产物填满，self._outlet()会丢弃最新的产物；
        * 使用 ``self.logger`` 属性打印日志。

        预置worker不需要自己实现本方法。

        Implement your business logic in this method. These methods and attributes may be useful:

        * use ``self._intake()`` method to intake data from tcp or udp connection;
        * use ``self._outlet()`` to put product to ``out``. Keep in mind if ``out`` is filled up with unconsumed product, self._outlet() discards the latest products.
        * use ``self.logger`` for log printing.

        There's no need to implement this method in Sugared Workers.
        """
        raise NotImplementedError('implement me')

    def __call__(self) -> None:
        try:
            if self._loop:
                while not self.closed:
                    self.work()
            else:
                self.work()
        except EOFError:
            if not self.closed:
                raise
        finally:
            self.close()

    @property
    def logger(self) -> logging.Logger:
        """
        使用本属性打印日志。

        Use this attribute for logging.
        """
        return self._logger

    def _assert_ready(self):
        assert not self.closed, 'Worker is already closed'

    def _intake(self, buf_size: int):
        self._assert_ready()
        return self._conn.recv(buf_size)

    def _outlet(self, payload):
        self._assert_ready()
        while not self.closed:
            try:
                self._out.put(payload, block=True, timeout=self.QUEUE_TIMEOUT)
            except queue.Full:
                continue
            break

    def get_address(self) -> Tuple[str, int]:
        """
        获取Worker连接的IP和port.

        get IP and port which the worker currently connects to.

        :return: (IP, port)
        """
        return self._address

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()


class Hub:
    """
    程序中枢。

    * 使用 ``self.worker()`` 注册你的Worker；
    * 使用 ``self.run()`` 开始运行；
    * 使用 ``Ctrl + C`` 停止程序。

    Hub is the orchestrator.

    * Use ``self.worker()`` to register your worker;
    * Use ``self.run()`` to run;
    * Use ``Ctrl + C`` for exiting.
    """

    TERMINATION_TIMEOUT = 10

    def __init__(self):
        """
        创建Hub不需要提供参数。

        Hub does not need parameters to initialize.
        """
        self._mu = CTX.Lock()
        with self._mu:
            self._closed: bool = False
            self._workers: List = []

    def close(self):
        """
        让Hub以及Hub名下的所有Worker停止工作。这个方法不需要用户来调用。

        Stop hub and workers registered under hub. This method does not need to be called by user.
        """
        with self._mu:
            if self._closed:
                return
            self._closed = True

            end_time = time.time() + self.TERMINATION_TIMEOUT
            for worker in self._workers:
                remain_time = max(0.0, end_time - time.time())
                worker.join(remain_time)
            for worker in self._workers:
                if worker.is_alive():
                    worker.terminate()

    def _assert_ready(self):
        assert not self._closed, 'Hub is closed'

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def worker(self, worker_class, name: str, args: Tuple = (), kwargs=None):
        """
        将worker注册到hub.
        所有的worker都在独立的进程中运行。

        Register worker to hub.
        All workers run in their own operating system process.

        :param worker_class: worker的类，注意不是worker实例。
            class of worker to be registered, note provide the class, instead of an instance.
        :param name: worker的名字，选个好名字可以让调试更容易。
            worker's name. A good name makes debugging less painful.
        :param args: 创建worker需要使用的参数。
            args to initialize the worker.
        :param kwargs: 创建worker需要使用的kwargs参数。
            kwargs to initialize the worker.
        """
        if kwargs is None:
            kwargs = {}
        process = CTX.Process(name=name, target=self._build_worker_and_run, args=(worker_class, name, *args), kwargs=kwargs)
        self._workers.append(process)

    @staticmethod
    def _build_worker_and_run(*args, **kwargs):
        worker_class = args[0]
        worker = worker_class(*args[1:], **kwargs)
        worker()

    def run(self):
        """
        按注册顺序启动所有worker，阻塞主进程。
        Hub在接收到 ``SIGTERM`` 或者 ``SIGINT`` 时会尝试安全退出。

        Start workers and block the main process.
        Hub tries to shutdown itself gracefully when receiving
        ``SIGTERM`` or ``SIGINT``.
        """
        with self._mu:
            self._assert_ready()
            assert len(self._workers) > 0, 'no worker registered'
        for worker in self._workers:
            worker.start()

        signal.sigwait((signal.SIGINT, signal.SIGTERM))
        self.close()
        for worker in self._workers:
            try:
                # close method does not exist until Python 3.7 and better
                if getattr(worker, 'close', False):
                    worker.close()
            except Exception as e:
                logging.error('[resource leak warning] failed to close process "%s": %s', worker._name, e)


class PushListener(Worker):
    """
    监听并解析机甲大师的推送，输出强类型的推送内容。

    Listen and parse pushes from Robomaster, product parsed pushes in strong typed manner.
    """
    PUSH_TYPE_CHASSIS: str = 'chassis'
    PUSH_TYPE_GIMBAL: str = 'gimbal'
    PUSH_TYPES: Tuple[str] = (PUSH_TYPE_CHASSIS, PUSH_TYPE_GIMBAL)

    def __init__(self, name: str, out: mp.Queue):
        """
        初始化自身。

        Initialize self.

        :param name: worker名称   name of worker
        :param out: PushListener会将产物放入其中以供下游消费。
            PushListener puts product into ``out`` for downstream consuming.
        """
        super().__init__(name, out, 'udp', ('', PUSH_PORT), None)

    def _parse(self, msg: str) -> List:
        payloads: Iterator[str] = map(lambda x: x.strip(), msg.strip(' ;').split(';'))
        current_push_type: Optional[str] = None
        has_type_prefix: bool = False
        parsed: List = []
        for index, payload in enumerate(payloads):
            words = payload.split(' ')
            assert len(words) > 1, f'unexpected payload at index {index}, context: {msg}'
            if words[0] in self.PUSH_TYPES:
                current_push_type = words[0]
                has_type_prefix = True
            else:
                has_type_prefix = False
            assert current_push_type is not None, f'can not decide push type of payload at index {index}, context: {msg}'

            if current_push_type == self.PUSH_TYPE_CHASSIS:
                parsed.append(self._parse_chassis_push(words, has_type_prefix))
            elif current_push_type == self.PUSH_TYPE_GIMBAL:
                parsed.append(self._parse_gimbal_push(words, has_type_prefix))
            else:
                raise ValueError(f'unknown push type {current_push_type} at index {index}, context: {msg}')
        return parsed

    @staticmethod
    def _parse_gimbal_push(words: List[str], has_type_prefix: bool):
        subtype: str = ''
        if has_type_prefix:
            assert len(words) > 3, f'invalid gimbal push payload, words: {words}'
            subtype = words[2]
        else:
            assert len(words) > 1, f'invalid gimbal push payload, words: {words}'
            subtype = words[0]

        if subtype == 'attitude':
            return GimbalAttitude(float(words[-2]), float(words[-1]))
        else:
            raise ValueError(f'unknown gimbal push subtype {subtype}, context: {words}')

    @staticmethod
    def _parse_chassis_push(words: List[str], has_type_prefix: bool):
        subtype: str = ''
        if has_type_prefix:
            assert len(words) > 3, f'invalid chassis push payload, words: {words}'
            subtype = words[2]
        else:
            assert len(words) > 1, f'invalid chassis push payload, words: {words}'
            subtype = words[0]

        if subtype == 'position':
            return ChassisPosition(float(words[-2]), float(words[-1]), None)
        elif subtype == 'attitude':
            return ChassisAttitude(float(words[-3]), float(words[-2]), float(words[-1]))
        elif subtype == 'status':
            ans = words[-11:]
            assert len(ans) == 11, f'invalid chassis status payload, words: {words}'
            return ChassisStatus(*map(lambda x: bool(int(x)), ans))
        else:
            raise ValueError(f'unknown chassis push subtype {subtype}, context: {words}')

    def work(self) -> None:
        try:
            msg = self._intake(DEFAULT_BUF_SIZE).decode()
        except OSError:
            if self.closed:
                return
            else:
                raise
        payloads = self._parse(msg)
        for payload in payloads:
            self._outlet(payload)


class EventListener(Worker):
    """
    监听并解析机甲大师的事件，输出强类型的推送内容。

    Listen and parse events from Robomaster, product parsed events in strong typed manner.
    """

    EVENT_TYPE_ARMOR: str = 'armor'
    EVENT_TYPE_SOUND: str = 'sound'
    EVENT_TYPES: Tuple[str] = (EVENT_TYPE_ARMOR, EVENT_TYPE_SOUND)

    def __init__(self, name: str, out: mp.Queue, ip: str):
        """
        初始化自身。

        Initialize self.

        :param name: worker名称   name of worker
        :param out: PushListener会将产物放入其中以供下游消费。
            PushListener puts product into ``out`` for downstream consuming.
        :param ip: 机甲的IP，可从Commander.get_ip()取得。
            IP of your Robomaster, can be obtained from Commander.get_ip()
        """
        super().__init__(name, out, 'tcp', (ip, EVENT_PORT), None)

    def _parse(self, msg: str) -> List:
        payloads: Iterator[str] = map(lambda x: x.strip(), msg.strip(' ;').split(';'))
        current_event_type: Optional[str] = None
        has_type_prefix: bool = False
        parsed: List = []
        for index, payload in enumerate(payloads):
            words = payload.split(' ')
            assert len(words) > 1, f'unexpected payload at index {index}, context: {msg}'
            if words[0] in self.EVENT_TYPES:
                current_event_type = words[0]
                has_type_prefix = True
            else:
                has_type_prefix = False
            assert current_event_type is not None, f'can not decide event type of payload at index {index}, context: {msg}'

            if current_event_type == self.EVENT_TYPE_ARMOR:
                parsed.append(self._parse_armor_event(words, has_type_prefix))
            elif current_event_type == self.EVENT_TYPE_SOUND:
                parsed.append(self._parse_sound_event(words, has_type_prefix))
            else:
                raise ValueError(f'unknown event type {current_event_type} at index {index}, context: {msg}')
        return parsed

    @staticmethod
    def _parse_armor_event(words: List[str], has_type_prefix: bool):
        subtype: str = ''
        if has_type_prefix:
            assert len(words) > 3, f'invalid armor event payload, words: {words}'
            subtype = words[2]
        else:
            assert len(words) > 1, f'invalid armor event payload, words: {words}'
            subtype = words[0]

        if subtype == ARMOR_HIT:
            return ArmorHitEvent(int(words[-2]), int(words[-1]))
        else:
            raise ValueError(f'unknown armor event subtype {subtype}, context: {words}')

    @staticmethod
    def _parse_sound_event(words: List[str], has_type_prefix: bool):
        subtype: str = ''
        if has_type_prefix:
            assert len(words) > 3, f'invalid sound event payload, words: {words}'
            subtype = words[2]
        else:
            assert len(words) > 1, f'invalid sound event payload, words: {words}'
            subtype = words[0]

        if subtype == SOUND_APPLAUSE:
            return SoundApplauseEvent(int(words[-1]))
        else:
            raise ValueError(f'unknown sound event subtype {subtype}, context: {words}')

    def work(self) -> None:
        try:
            msg = self._intake(DEFAULT_BUF_SIZE).decode()
        except OSError:
            if self.closed:
                return
            else:
                raise
        payloads = self._parse(msg)
        for payload in payloads:
            self._outlet(payload)


class Vision(Worker):
    """
    拉取并解析机甲的视频流，回调函数会收到解析好的OpenCV视频帧，回调函数的返回值会被放置到 ``out`` 中。

    Pull and parse Robomaster's video stream, call the callback with parsed OpenCV frame,
    and put return value from callback into ``out``.
    """

    TIMEOUT: float = 5.0

    def __init__(self, name: str, out: Optional[mp.Queue], ip: str, processing: Callable[..., None], none_is_valid=False):
        """
        初始化自身。

        Initialize self.

        :param name: worker名称   name of worker
        :param out: PushListener会将产物放入其中以供下游消费。
            PushListener puts product into ``out`` for downstream consuming.
        :param ip: 机甲的IP，可从Commander.get_ip()取得。
            IP of your Robomaster, can be obtained from Commander.get_ip()
        :param processing: 回调函数，每当有新的视频帧到来时，函数都会被Vision调用，形如 ``processing(frame=frame, logger=self.logger)`` ，
            其中frame为cv2(OpenCV) frame，logger可用于日志打印。
            callback function, is called every time when a new frame comes, in form ``processing(frame=frame, logger=self.logger)``,
            where frame is cv2(OpenCV) frame, and logger is for logging.
        :param none_is_valid: 是否在回调函数返回None时将None放入 ``out`` ，默认为False.
            Whether to put None returned from callback function into ``out``, default to False.
        """
        super().__init__(name, out, None, (ip, VIDEO_PORT), self.TIMEOUT)
        self._none_is_valid = none_is_valid
        self._processing = processing
        self._cap = cv.VideoCapture(f'tcp://{ip}:{VIDEO_PORT}')
        assert self._cap.isOpened(), 'failed to connect to video stream'
        self._cap.set(cv.CAP_PROP_BUFFERSIZE, 4)

    def close(self):
        self._cap.release()
        cv.destroyAllWindows()
        super().close()

    def work(self) -> None:
        ok, frame = self._cap.read()
        if not ok:
            if self.closed:
                return
            else:
                raise ValueError('can not receive frame (stream end?)')
        processed = self._processing(frame=frame, logger=self.logger)
        if processed is not None or self._none_is_valid:
            self._outlet(processed)


class Mind(Worker):
    """
    无状态的控制者，适用于简单的控制。
    对于复杂的，有状态的控制需求，你需要自己继承Worker来实现。

    Stateless controller, suits simple and naive controlling scenario.
    For complicated, stateful controlling, inherit Worker to implement.
    """
    def __init__(self, name: str, queues: Tuple[mp.Queue, ...], ip: str, processing: Callable[..., None], timeout: float = 30, loop: bool = True):
        """
        初始化自身。

        Initialize self.

        :param name: worker名称   name of worker
        :param queues: 队列元组，其中队列的内容由上游提供。
            Tuple of mp.Queue, where their contents are provided by upstream.
        :param ip: 机甲的IP，可从Commander.get_ip()取得。
            IP of your Robomaster, can be obtained from Commander.get_ip()
        :param processing: 回调函数，调用时参数形如 ``processing(cmd=self._cmd, queues=self._queues, logger=self.logger)`` ，
            其中cmd为连接到机甲的Commander，queues为输入的队列元组，logger用于日志打印。
            callback function, is called in form ``processing(cmd=self._cmd, queues=self._queues, logger=self.logger)``,
            where cmd is a connected Commander, queue is the input tuple of mp.Queue, logger is for logging.
        :param timeout: Commander的连接超时。
            timeout for Commander.
        :param loop: 是否循环调用回调函数processing
            whether calls processing(callback) function in loop, default to True.
        """
        super().__init__(name, None, None, (ip, 0), timeout, loop=loop)
        self._queues = queues
        self._processing = processing
        self._cmd = Commander(ip, timeout)

    def close(self):
        self._cmd.close()
        super().close()

    def work(self) -> None:
        self._processing(cmd=self._cmd, queues=self._queues, logger=self.logger)
