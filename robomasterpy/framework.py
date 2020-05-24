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
    QUEUE_TIMEOUT: float = 0.05

    def __init__(self, name: str, out: Optional[mp.Queue], protocol: Optional[str], address: Tuple[str, int], timeout: Optional[float], loop: bool = True):
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
    def closed(self):
        return self._closed

    def close(self):
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
        return self._name

    def work(self) -> None:
        raise SyntaxError('implement me')

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
    def logger(self):
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
        return self._address

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()


class Hub:
    TERMINATION_TIMEOUT = 10

    def __init__(self):
        self._mu = CTX.Lock()
        with self._mu:
            self._closed: bool = False
            self._workers: List = []

    def close(self):
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
        assert not self._closed, 'EP is closed'

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    def worker(self, worker_class, name: str, args: Tuple = (), kwargs=None):
        """
        Register worker to process sensor data fetching, calculation,
        inference,controlling, communication and more.
        All workers run in their own operating system process.

        :param worker_class:
        :param name:
        :param args: args to func
        :param kwargs: kwargs to func
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
        Start workers and block the main process until
        all workers terminate.

        Mind tries to shutdown itself gracefully when receiving
        SIGTERM or SIGINT.
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
                worker.close()
            except Exception as e:
                logging.error('[resource leak warning] failed to close process "%s": %s', worker._name, e)


class PushListener(Worker):
    PUSH_TYPE_CHASSIS: str = 'chassis'
    PUSH_TYPE_GIMBAL: str = 'gimbal'
    PUSH_TYPES: Tuple[str] = (PUSH_TYPE_CHASSIS, PUSH_TYPE_GIMBAL)

    def __init__(self, name: str, out: mp.Queue):
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
    EVENT_TYPE_ARMOR: str = 'armor'
    EVENT_TYPE_SOUND: str = 'sound'
    EVENT_TYPES: Tuple[str] = (EVENT_TYPE_ARMOR, EVENT_TYPE_SOUND)

    def __init__(self, name: str, out: mp.Queue, ip: str):
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
    TIMEOUT: float = 5.0

    def __init__(self, name: str, out: Optional[mp.Queue], ip: str, processing: Callable[..., None], none_is_valid=False):
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
    def __init__(self, name: str, queues: Tuple[mp.Queue, ...], ip: str, processing: Callable[..., None], timeout: float = 30, loop: bool = True):
        super().__init__(name, None, None, (ip, 0), timeout, loop=loop)
        self._queues = queues
        self._processing = processing
        self._cmd = Commander(ip, timeout)

    def close(self):
        self._cmd.close()
        super().close()

    def work(self) -> None:
        self._processing(cmd=self._cmd, queues=self._queues, logger=self.logger)
