import logging
import multiprocessing as mp
import queue
import signal
import socket
import sys
import time
from dataclasses import dataclass
from typing import List, Callable, Tuple, Optional, Iterator

import cv2 as cv

CTX = mp.get_context('spawn')
LOG_LEVEL = logging.DEBUG

VIDEO_PORT: int = 40921
AUDIO_PORT: int = 40922
CTRL_PORT: int = 40923
PUSH_PORT: int = 40924
EVENT_PORT: int = 40925
IP_PORT: int = 40926

DEFAULT_BUF_SIZE: int = 512
MEDIA_BUF_SIZE: int = 1500
VIDEO_CHUNK_SIZE: int = 1460

# switch_enum
SWITCH_ON: str = 'on'
SWITCH_OFF: str = 'off'

# mode_enum
MODE_CHASSIS_LEAD: str = 'chassis_lead'
MODE_GIMBAL_LEAD: str = 'gimbal_lead'
MODE_FREE: str = 'free'
MODE_ENUMS = (MODE_CHASSIS_LEAD, MODE_GIMBAL_LEAD, MODE_FREE)

# armor_event_attr_enum
ARMOR_HIT: str = 'hit'
ARMOR_ENUMS = (ARMOR_HIT,)

# sound_event_attr_enum
SOUND_APPLAUSE: str = 'applause'
SOUND_ENUMS = (SOUND_APPLAUSE,)

# led_comp_enum
LED_ALL = 'all'
LED_TOP_ALL = 'top_all'
LED_TOP_RIGHT = 'top_right'
LED_TOP_LEFT = 'top_left'
LED_BOTTOM_ALL = 'bottom_all'
LED_BOTTOM_FRONT = 'bottom_front'
LED_BOTTOM_BACK = 'bottom_back'
LED_BOTTOM_LEFT = 'bottom_left'
LED_BOTTOM_RIGHT = 'bottom_right'
LED_ENUMS = (LED_ALL, LED_TOP_ALL, LED_TOP_RIGHT, LED_TOP_LEFT,
             LED_BOTTOM_ALL, LED_BOTTOM_FRONT, LED_BOTTOM_BACK,
             LED_BOTTOM_LEFT, LED_BOTTOM_RIGHT)

# led_effect_enum
LED_EFFECT_SOLID = 'solid'
LED_EFFECT_OFF = 'off'
LED_EFFECT_PULSE = 'pulse'
LED_EFFECT_BLINK = 'blink'
LED_EFFECT_SCROLLING = 'scrolling'
LED_EFFECT_ENUMS = (LED_EFFECT_SOLID, LED_EFFECT_OFF,
                    LED_EFFECT_PULSE, LED_EFFECT_BLINK,
                    LED_EFFECT_SCROLLING)


@dataclass
class ChassisSpeed:
    x: float
    y: float
    z: float
    w1: int
    w2: int
    w3: int
    w4: int


@dataclass
class ChassisPosition:
    x: float
    y: float
    z: Optional[float]


@dataclass
class ChassisAttitude:
    pitch: float
    roll: float
    yaw: float


@dataclass
class ChassisStatus:
    # 是否静止
    static: bool
    # 是否上坡
    uphill: bool
    # 是否下坡
    downhill: bool
    # 是否溜坡
    on_slope: bool
    # 是否被拿起
    pick_up: bool
    # 是否滑行
    slip: bool
    # x轴是否感应到撞击
    impact_x: bool
    # y轴是否感应到撞击
    impact_y: bool
    # z轴是否感应到撞击
    impact_z: bool
    # 是否翻车
    roll_over: bool
    # 是否在坡上静止
    hill_static: bool


@dataclass
class GimbalAttitude:
    pitch: float
    yaw: float


@dataclass
class ArmorHitEvent:
    index: int
    type: int


@dataclass
class SoundApplauseEvent:
    count: int


def get_broadcast_ip(timeout: float = None) -> str:
    """
    接收广播以获取机甲IP

    :param timeout: 等待超时（秒）
    :return: 机甲IP地址
    """
    BROADCAST_INITIAL: str = 'robot ip '

    conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conn.bind(('', IP_PORT))
    conn.settimeout(timeout)
    msg, ip, port = None, None, None
    try:
        msg, (ip, port) = conn.recvfrom(DEFAULT_BUF_SIZE)
    finally:
        conn.close()
    msg = msg.decode()
    assert len(msg) > len(BROADCAST_INITIAL), f'broken msg from {ip}:{port}: {msg}'
    msg = msg[len(BROADCAST_INITIAL):]
    assert msg == ip, f'unmatched source({ip}) and reported IP({msg})'
    return msg


class Commander:
    def __init__(self, ip: str = '', timeout: float = 30):
        self._mu: mp.Lock = CTX.Lock()
        with self._mu:
            if ip == '':
                ip = get_broadcast_ip(timeout)
            self._ip: str = ip
            self._closed: bool = False
            self._conn: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._timeout: float = timeout
            self._conn.settimeout(self._timeout)
            self._conn.connect((self._ip, CTRL_PORT))
            resp = self._do('command')
            assert self._is_ok(resp) or resp == 'Already in SDK mode', f'entering SDK mode: {resp}'

    def close(self):
        with self._mu:
            self._conn.close()
            self._closed = True

    def __enter__(self):
        return self

    def __exit__(self):
        self.close()

    @staticmethod
    def _is_ok(resp: str) -> bool:
        return resp == 'ok'

    def _do(self, *args) -> str:
        assert len(args) > 0, 'empty arg not accepted'
        assert not self._closed, 'connection is already closed'
        cmd = ' '.join(map(str, args)) + ';'
        self._conn.send(cmd.encode())
        buf = self._conn.recv(DEFAULT_BUF_SIZE)
        # 返回值后面有时候会多一个迷之空格，
        # 为了可能的向后兼容，额外剔除终止符。
        return buf.decode().strip(' ;')

    def get_ip(self) -> str:
        """
        返回机甲IP

        :return: 机甲IP
        """
        assert not self._closed, 'connection is already closed'
        return self._ip

    def do(self, *args) -> str:
        """
        执行任意命令

        :param args: 命令内容，list
        :return: 命令返回
        """
        with self._mu:
            return self._do(*args)

    def version(self) -> str:
        """
        query robomaster SDK version

        :return: version string
        """
        return self.do('version')

    def robot_mode(self, mode: str) -> str:
        """
        机器人运动模式控制

        :param mode: 三种模式之一，见enum MODE_*
        :return: ok，否则raise
        """
        assert mode in MODE_ENUMS, f'unknown mode {mode}'
        resp = self.do('robot', 'mode', mode)
        assert self._is_ok(resp), f'robot_mode: {resp}'
        return resp

    def get_robot_mode(self) -> str:
        """
        查询当前机器人运动模式

        :return: 三种模式之一，见enum MODE_*
        """
        resp = self.do('robot', 'mode', '?')
        assert resp in MODE_ENUMS, f'unexpected robot mode result: {resp}'
        return resp

    def chassis_speed(self, x: float = 0, y: float = 0, z: float = 0) -> str:
        """
        控制底盘运动速度

        :param x: x 轴向运动速度，单位 m/s
        :param y: y 轴向运动速度，单位 m/s
        :param z: z 轴向旋转速度，单位 °/s
        :return: ok，否则raise
        """
        assert -3.5 <= x <= 3.5, f'x {x} is out of range'
        assert -3.5 <= y <= 3.5, f'y {y} is out of range'
        assert -600 <= z <= 600, f'z {z} is out of range'
        resp = self.do('chassis', 'speed', 'x', x, 'y', y, 'z', z)
        assert self._is_ok(resp), f'chassis_speed: {resp}'
        return resp

    def get_chassis_speed(self) -> ChassisSpeed:
        """
        获取底盘速度信息

        :return: x 轴向运动速度(m/s)，
        y 轴向运动速度(m/s)，z 轴向旋转速度(°/s)，
        w1 右前麦轮速度(rpm)，w2 左前麦轮速速(rpm)，
        w3 右后麦轮速度(rpm)，w4 左后麦轮速度(rpm)
        """
        resp = self.do('chassis', 'speed', '?')
        ans = resp.split(' ')
        assert len(ans) == 7, f'get_chassis_speed: {resp}'
        return ChassisSpeed(x=float(ans[0]), y=float(ans[1]), z=float(ans[2]), w1=int(ans[3]), w2=int(ans[4]), w3=int(ans[5]), w4=int(ans[6]))

    def chassis_wheel(self, w1: int = 0, w2: int = 0, w3: int = 0, w4: int = 0) -> str:
        """
        底盘轮子速度控制

        :param w1: 右前麦轮速度，单位 rpm
        :param w2: 左前麦轮速度，单位 rpm
        :param w3: 右后麦轮速度，单位 rpm
        :param w4: 左后麦轮速度，单位 rpm
        :return ok: ok，否则raise
        """
        for i, v in enumerate((w1, w2, w3, w4)):
            assert -1000 <= v <= 1000, f'w{i + 1} {v} is out of range'
        resp = self.do('chassis', 'wheel', 'w1', w1, 'w2', w2, 'w3', w3, 'w4', w4)
        assert self._is_ok(resp), f'chassis_wheel: {resp}'
        return resp

    def chassis_move(self, x: float = 0, y: float = 0, z: float = 0, speed_xy: float = None, speed_z: float = None) -> str:
        """
        控制底盘运动当指定位置，坐标轴原点为当前位置

        :param x: x 轴向运动距离，单位 m
        :param y: y 轴向运动距离，单位 m
        :param z: z 轴向旋转角度，单位 °
        :param speed_xy: xy 轴向运动速度，单位 m/s
        :param speed_z: z 轴向旋转速度， 单位 °/s
        :return ok: ok，否则raise
        """
        assert -5 <= x <= 5, f'x {x} is out of range'
        assert -5 <= y <= 5, f'y {y} is out of range'
        assert -1800 <= z <= 1800, f'z {z} is out of range'
        assert speed_xy is None or 0 < speed_xy <= 3.5, f'speed_xy {speed_xy} is out of range'
        assert speed_z is None or 0 < speed_z <= 600, f'speed_z {speed_z} is out of range'
        cmd = ['chassis', 'move', 'x', x, 'y', y, 'z', z]
        if speed_xy is not None:
            cmd += ['vxy', speed_xy]
        if speed_z is not None:
            cmd += ['vz', speed_z]
        resp = self.do(*cmd)
        assert self._is_ok(resp), f'chassis_move: {resp}'
        return resp

    def get_chassis_position(self) -> ChassisPosition:
        """
        获取底盘当前的位置(以上电时刻位置为原点)

        :return: x 轴位置(m)，y 轴位置(m)，偏航角度(°)
        """
        resp = self.do('chassis', 'position', '?')
        ans = resp.split(' ')
        assert len(ans) == 3, f'get_chassis_position: {resp}'
        return ChassisPosition(float(ans[0]), float(ans[1]), float(ans[2]))

    def get_chassis_attitude(self) -> ChassisAttitude:
        """
        获取底盘姿态信息

        :return: pitch 轴角度(°)，roll 轴角度(°)，yaw 轴角度(°)
        """
        resp = self.do('chassis', 'attitude', '?')
        ans = resp.split(' ')
        assert len(ans) == 3, f'get_chassis_attitude: {resp}'
        return ChassisAttitude(float(ans[0]), float(ans[1]), float(ans[2]))

    def get_chassis_status(self) -> ChassisStatus:
        """
        获取底盘状态信息

        :return: 底盘状态，详见 ChassisStatus
        """
        resp = self.do('chassis', 'status', '?')
        ans = resp.split(' ')
        assert len(ans) == 11, f'get_chassis_status: {resp}'
        return ChassisStatus(*map(lambda x: bool(int(x)), ans))

    def chassis_push_on(self, position_freq: int = None, attitude_freq: int = None, status_freq: int = None, all_freq: int = None) -> str:
        """
        打开底盘中相应属性的信息推送，支持的频率 1, 5, 10, 20, 30, 50

        :param position_freq: 位置推送频率，不开启则设为None
        :param attitude_freq: 姿态推送频率，不开启则设为None
        :param status_freq: 状态推送频率，不开启则设为None
        :param all_freq: 统一设置所有推送频率，设置则开启所有推送
        :return: ok，否则raise
        """
        valid_frequencies = (1, 5, 10, 20, 30, 50)
        cmd = ['chassis', 'push']
        if all_freq is not None:
            assert all_freq in valid_frequencies, f'all_freq {all_freq} is not valid'
            cmd += ['afreq', all_freq]
        else:
            if position_freq is not None:
                assert position_freq in valid_frequencies, f'position_freq {position_freq} is not valid'
                cmd += ['position', SWITCH_ON, 'pfreq', position_freq]
            if attitude_freq is not None:
                assert attitude_freq in valid_frequencies, f'attitude_freq {attitude_freq} is not valid'
                cmd += ['attitude', SWITCH_ON, 'afreq', attitude_freq]
            if status_freq is not None:
                assert status_freq in valid_frequencies, f'status_freq {status_freq} is not valid'
                cmd += ['status', SWITCH_ON, 'sfreq', status_freq]
        assert len(cmd) > 2, 'at least one argument should not be None'
        resp = self.do(*cmd)
        assert self._is_ok(resp), f'chassis_push_on: {resp}'
        return resp

    def chassis_push_off(self, position: bool = False, attitude: bool = False, status: bool = False, all: bool = False) -> str:
        """
        关闭底盘中相应属性的信息推送。

        :param position: 是否关闭位置推送
        :param attitude: 是否关闭姿态推送
        :param status: 是否关闭状态推送
        :param all: 关闭所有推送
        :return: ok，否则raise
        """
        cmd = ['chassis', 'push']
        if all or position:
            cmd += ['position', SWITCH_OFF]
        if all or attitude:
            cmd += ['attitude', SWITCH_OFF]
        if all or status:
            cmd += ['status', SWITCH_OFF]

        assert len(cmd) > 2, 'at least one argument should be True'
        resp = self.do(*cmd)
        assert self._is_ok(resp), f'chassis_push_off: {resp}'
        return resp

    def gimbal_speed(self, pitch: float, yaw: float) -> str:
        """
        控制云台运动速度

        :param pitch: pitch 轴速度，单位 °/s
        :param yaw: yaw 轴速度，单位 °/s
        :return: ok，否则raise
        """
        assert -450 <= pitch <= 450, f'pitch {pitch} is out of range'
        assert -450 <= yaw <= 450, f'yaw {yaw} is out of range'
        resp = self.do('gimbal', 'speed', 'p', pitch, 'y', yaw)
        assert self._is_ok(resp), f'gimbal_speed: {resp}'
        return resp

    def gimbal_move(self, pitch: float = 0, yaw: float = 0, pitch_speed: float = None, yaw_speed: float = None) -> str:
        """
        控制云台运动到指定位置，坐标轴原点为当前位置

        :param pitch: pitch 轴角度， 单位 °
        :param yaw: yaw 轴角度， 单位 °
        :param pitch_speed: pitch 轴运动速速，单位 °/s
        :param yaw_speed: yaw 轴运动速速，单位 °/s
        :return: ok，否则raise
        """
        assert -55 <= pitch <= 55, f'pitch {pitch} is out of range'
        assert -55 <= yaw <= 55, f'yaw {yaw} is out of range'
        assert pitch_speed is None or 0 < pitch_speed <= 540, f'pitch_speed {pitch_speed} is out of range'
        assert yaw_speed is None or 0 < yaw_speed <= 540, f'yaw_speed {yaw_speed} is out of range'
        cmd = ['gimbal', 'move', 'p', pitch, 'y', yaw]
        if pitch_speed is not None:
            cmd += ['vp', pitch_speed]
        if yaw_speed is not None:
            cmd += ['vy', yaw_speed]
        resp = self.do(*cmd)
        assert self._is_ok(resp), f'gimbal_move: {resp}'
        return resp

    def gimbal_moveto(self, pitch: float = 0, yaw: float = 0, pitch_speed: float = None, yaw_speed: float = None) -> str:
        """
        控制云台运动到指定位置，坐标轴原点为上电位置

        :param pitch: pitch 轴角度， 单位 °
        :param yaw: yaw 轴角度， 单位 °
        :param pitch_speed: pitch 轴运动速速，单位 °/s
        :param yaw_speed: yaw 轴运动速速，单位 °/s
        :return: ok，否则raise
        """
        assert -25 <= pitch <= 30, f'pitch {pitch} is out of range'
        assert -250 <= yaw <= 250, f'yaw {yaw} is out of range'
        assert pitch_speed is None or 0 < pitch_speed <= 540, f'pitch_speed {pitch_speed} is out of range'
        assert yaw_speed is None or 0 < yaw_speed <= 540, f'yaw_speed {yaw_speed} is out of range'
        cmd = ['gimbal', 'moveto', 'p', pitch, 'y', yaw]
        if pitch_speed is not None:
            cmd += ['vp', pitch_speed]
        if yaw_speed is not None:
            cmd += ['vy', yaw_speed]
        resp = self.do(*cmd)
        assert self._is_ok(resp), f'gimbal_moveto: {resp}'
        return resp

    def gimbal_suspend(self):
        """
        使云台进入休眠状态
        :return: ok，否则raise
        """
        resp = self.do('gimbal', 'suspend')
        assert self._is_ok(resp), f'gimbal_suspend: {resp}'
        return resp

    def gimbal_resume(self):
        """
        控制云台从休眠状态中恢复
        :return: ok，否则raise
        """
        resp = self.do('gimbal', 'resume')
        assert self._is_ok(resp), f'gimbal_resume: {resp}'
        return resp

    def gimbal_recenter(self):
        """
        控制云台回中
        :return: ok，否则raise
        """
        resp = self.do('gimbal', 'recenter')
        assert self._is_ok(resp), f'gimbal_recenter: {resp}'
        return resp

    def get_gimbal_attitude(self) -> GimbalAttitude:
        """
        获取云台姿态信息
        :return: pitch 轴角度(°)，yaw 轴角度(°)
        """
        resp = self.do('gimbal', 'attitude', '?')
        ans = resp.split(' ')
        assert len(ans) == 2, f'get_gimbal_attitude: {resp}'
        return GimbalAttitude(pitch=float(ans[0]), yaw=float(ans[1]))

    def gimbal_push_on(self, attitude_freq: int = 5) -> str:
        """
        打开云台中相应属性的信息推送，支持的频率 1, 5, 10, 20, 30, 50

        :param attitude_freq: 姿态推送频率
        :return: ok，否则raise
        """
        valid_frequencies = (1, 5, 10, 20, 30, 50)
        assert attitude_freq in valid_frequencies, f'invalid attitude_freq {attitude_freq}'
        resp = self.do('gimbal', 'push', 'attitude', SWITCH_ON, 'afreq', attitude_freq)
        assert self._is_ok(resp), f'gimbal_push_on: {resp}'
        return resp

    def gimbal_push_off(self, attitude: bool = True) -> str:
        """
        关闭云台中相应属性的信息推送

        :param attitude: 关闭姿态推送
        :return: ok，否则raise
        """
        assert attitude, 'at least one augment should be True'
        resp = self.do('gimbal', 'push', 'attitude', SWITCH_OFF)
        assert self._is_ok(resp), f'gimbal_push_off: {resp}'
        return resp

    def armor_sensitivity(self, value: int) -> str:
        """
        设置装甲板打击检测灵敏度

        :param value: 装甲板灵敏度，数值越大，越容易检测到打击。
        默认灵敏度值为 5.
        :return: ok，否则raise
        """
        assert 1 <= value <= 10, f'value {value} is out of range'
        resp = self.do('armor', 'sensitivity', value)
        assert self._is_ok(resp), f'armor_sensitivity: {resp}'
        return resp

    def get_armor_sensitivity(self) -> int:
        """
        获取装甲板打击检测灵敏度
        :return: 装甲板灵敏度
        """
        resp = self.do('armor', 'sensitivity', '?')
        return int(resp)

    def armor_event(self, attr: str, switch: bool) -> str:
        """
        控制装甲板检测事件上报

        :param attr: 事件属性名称，范围见 ARMOR_ENUMS
        :param switch: 是否开启上报
        :return: ok，否则raise
        """
        assert attr in ARMOR_ENUMS, f'unexpected armor event attr {attr}'
        resp = self.do('armor', 'event', attr, SWITCH_ON if switch else SWITCH_OFF)
        assert self._is_ok(resp), f'armor_event: {resp}'
        return resp

    def sound_event(self, attr: str, switch: bool) -> str:
        """
        声音识别事件上报控制

        :param attr: 事件属性名称，范围见 SOUND_ENUMS
        :param switch: 是否开启上报
        :return: ok，否则raise
        """
        assert attr in SOUND_ENUMS, f'unexpected armor event attr {attr}'
        resp = self.do('sound', 'event', attr, SWITCH_ON if switch else SWITCH_OFF)
        assert self._is_ok(resp), f'armor_event: {resp}'
        return resp

    def led_control(self, comp: str, effect: str, r: int, g: int, b: int) -> str:
        """
        控制 LED 灯效。跑马灯效果仅可作用于云台两侧 LED。

        :param comp: LED 编号，见 LED_ENUMS
        :param effect: 灯效类型，见 LED_EFFECT_ENUMS
        :param r: RGB 红色分量值
        :param g: RGB 绿色分量值
        :param b: RGB 蓝色分量值
        :return: ok，否则raise
        """
        assert comp in LED_ENUMS, f'unknown comp {comp}'
        assert effect in LED_EFFECT_ENUMS, f'unknown effect {effect}'
        assert 0 <= r <= 255, f'r {r} is out of scope'
        assert 0 <= g <= 255, f'g {g} is out of scope'
        assert 0 <= b <= 255, f'b {b} is out of scope'
        if effect == LED_EFFECT_SCROLLING:
            assert comp in (LED_TOP_ALL, LED_TOP_LEFT, LED_TOP_RIGHT), 'scrolling effect works only on gimbal LEDs'
        resp = self.do('led', 'control', 'comp', comp, 'r', r, 'g', g, 'b', b, 'effect', effect)
        assert self._is_ok(resp), f'led_control: {resp}'
        return resp

    def ir_sensor_measure(self, switch: bool = True):
        """
        打开/关闭所有红外传感器开关

        :param switch: 打开/关闭
        :return: ok，否则raise
        """
        resp = self.do('ir_distance_sensor', 'measure', SWITCH_ON if switch else SWITCH_OFF)
        assert self._is_ok(resp), f'ir_sensor_measure: {resp}'
        return resp

    def get_ir_sensor_distance(self, id: int) -> int:
        """
        获取指定 ID 的红外深度传感器距离

        :param id: 红外传感器的 ID
        :return: 指定 ID 的红外传感器测得的距离值，单位 mm
        """
        assert 1 <= id <= 4, f'invalid IR sensor id {id}'
        resp = self.do('ir_distance_sensor', 'distance', id, '?')
        return int(resp)

    def stream(self, switch: bool) -> str:
        """
        视频流开关控制

        :param switch: 打开/关闭
        :return: ok，否则raise
        """
        resp = self.do('stream', SWITCH_ON if switch else SWITCH_OFF)
        assert self._is_ok(resp), f'stream: {resp}'
        return resp

    def audio(self, switch: bool) -> str:
        """
        音频流开关控制

        :param switch: 打开/关闭
        :return: ok，否则raise
        """
        resp = self.do('audio', SWITCH_ON if switch else SWITCH_OFF)
        assert self._is_ok(resp), f'audio: {resp}'
        return resp

    def blaster_fire(self) -> str:
        """
        控制水弹枪发射一次

        :return: ok，否则raise
        """
        resp = self.do('blaster', 'fire')
        assert self._is_ok(resp), f'blaster_fire: {resp}'
        return resp


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
