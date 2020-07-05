# -*- coding: utf-8 -*-

# ██████╗  ██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ ██████╗ ██╗   ██╗
# ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
# ██████╔╝██║   ██║██████╔╝██║   ██║██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝██████╔╝ ╚████╔╝
# ██╔══██╗██║   ██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗██╔═══╝   ╚██╔╝
# ██║  ██║╚██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║██║        ██║
# ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝        ╚═╝

import socket
from unittest import TestCase
from unittest.mock import patch

import robomasterpy
from robomasterpy import Commander
from robomasterpy import framework


class TestConnection(TestCase):
    def test_get_broadcast_ip(self):
        with patch.object(socket.socket, 'recvfrom', return_value=(b'robot ip 192.168.42.42', ('192.168.42.42', 40101))):
            ip = robomasterpy.get_broadcast_ip(2)
            self.assertEqual('192.168.42.42', ip)


class TestCommander(TestCase):
    @patch('socket.socket')
    def setUp(self, mock_socket):
        IP = '127.0.0.1'
        TIMEOUT = 42.1234

        m = mock_socket()
        m.recv.return_value = b'ok'
        self.commander = Commander(ip=IP, timeout=TIMEOUT)
        m.settimeout.assert_called_with(TIMEOUT)
        m.connect.assert_called_with((IP, robomasterpy.CTRL_PORT))
        m.recv.assert_called_with(robomasterpy.DEFAULT_BUF_SIZE)
        m.send.assert_called_with(b'command;')
        m.recv.assert_called_once()

    def test__is_ok(self):
        self.assertTrue(Commander._is_ok('ok'))
        self.assertFalse(Commander._is_ok('fail'))

    def test_version(self):
        VERSION = '1.2.3.4.5'

        with patch('robomasterpy.Commander._do', return_value=VERSION) as m:
            self.assertEqual(VERSION, self.commander.version())
            m.assert_called_with('version')

    def test_chassis_speed(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.chassis_speed(1.1, 1.2, 1.3))
            m.assert_called_with('chassis', 'speed', 'x', 1.1, 'y', 1.2, 'z', 1.3)

    def test_robot_mode(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.robot_mode(robomasterpy.MODE_FREE))
            m.assert_called_with('robot', 'mode', robomasterpy.MODE_FREE)

    def test_get_robot_mode(self):
        with patch('robomasterpy.Commander._do', return_value=robomasterpy.MODE_GIMBAL_LEAD) as m:
            self.assertEqual(robomasterpy.MODE_GIMBAL_LEAD, self.commander.get_robot_mode())
            m.assert_called_with('robot', 'mode', '?')

    def test_chassis_wheel(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.chassis_wheel(-1, -2, -3, -4))
            m.assert_called_with('chassis', 'wheel', 'w1', -1, 'w2', -2, 'w3', -3, 'w4', -4)

    def test_chassis_wheel_out_of_range(self):
        self.assertRaises(AssertionError, self.commander.chassis_wheel, 0, -2000, -3, -4)

    def test_chassis_move(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.chassis_move(5, 4, 3))
            m.assert_called_with('chassis', 'move', 'x', 5, 'y', 4, 'z', 3)
            self.assertEqual('ok', self.commander.chassis_move(5, 4, 3, 2))
            m.assert_called_with('chassis', 'move', 'x', 5, 'y', 4, 'z', 3, 'vxy', 2)
            self.assertEqual('ok', self.commander.chassis_move(5, 4, 3, 2, 1))
            m.assert_called_with('chassis', 'move', 'x', 5, 'y', 4, 'z', 3, 'vxy', 2, 'vz', 1)

    def test_chassis_move_out_of_range(self):
        self.assertRaises(AssertionError, self.commander.chassis_move, 6)
        self.assertRaises(AssertionError, self.commander.chassis_move, 5, 6)
        self.assertRaises(AssertionError, self.commander.chassis_move, 5, 5, 1801)
        self.assertRaises(AssertionError, self.commander.chassis_move, 5, 5, 5, 3.6)
        self.assertRaises(AssertionError, self.commander.chassis_move, 5, 5, 5, 0)
        self.assertRaises(AssertionError, self.commander.chassis_move, 5, 5, 5, 3.5, 0)
        self.assertRaises(AssertionError, self.commander.chassis_move, 5, 5, 5, 3.5, 601)

    def test_get_chassis_speed(self):
        with patch('robomasterpy.Commander._do', return_value='1 2 30 100 150 200 250') as m:
            self.assertEqual(robomasterpy.ChassisSpeed(1, 2, 30, 100, 150, 200, 250), self.commander.get_chassis_speed())
            m.assert_called_with('chassis', 'speed', '?')

    def test_get_chassis_speed_raise(self):
        with patch('robomasterpy.Commander._do', return_value='fail') as m:
            self.assertRaises(AssertionError, self.commander.get_chassis_speed)

    def test_get_chassis_position(self):
        with patch('robomasterpy.Commander._do', return_value='1 1.5 20') as m:
            self.assertEqual(robomasterpy.ChassisPosition(1, 1.5, 20), self.commander.get_chassis_position())
            m.assert_called_with('chassis', 'position', '?')

    def test_get_chassis_position_raise(self):
        with patch('robomasterpy.Commander._do', return_value='fail') as m:
            self.assertRaises(AssertionError, self.commander.get_chassis_position)

    def test_get_chassis_attitude(self):
        with patch('robomasterpy.Commander._do', return_value='-20 -50.5 -70') as m:
            self.assertEqual(robomasterpy.ChassisAttitude(-20, -50.5, -70), self.commander.get_chassis_attitude())
            m.assert_called_with('chassis', 'attitude', '?')

    def test_get_chassis_attitude_raise(self):
        with patch('robomasterpy.Commander._do', return_value='fail') as m:
            self.assertRaises(AssertionError, self.commander.get_chassis_attitude)

    def test_get_chassis_status(self):
        TRUES = [True for i in range(11)]
        FALSES = [False for i in range(11)]

        with patch('robomasterpy.Commander._do', return_value='1 1 1 1 1 1 1 1 1 1 1') as m:
            self.assertEqual(robomasterpy.ChassisStatus(*TRUES), self.commander.get_chassis_status())
            m.assert_called_with('chassis', 'status', '?')

        with patch('robomasterpy.Commander._do', return_value='0 0 0 0 0 0 0 0 0 0 0') as m:
            self.assertEqual(robomasterpy.ChassisStatus(*FALSES), self.commander.get_chassis_status())
            m.assert_called_with('chassis', 'status', '?')

    def test_chassis_push_on(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.chassis_push_on(all_freq=5))
            m.assert_called_with('chassis', 'push', 'freq', 5)
            self.assertEqual('ok', self.commander.chassis_push_on(all_freq=10, position_freq=5))
            m.assert_called_with('chassis', 'push', 'freq', 10)
            self.assertEqual('ok', self.commander.chassis_push_on(position_freq=10, attitude_freq=20, status_freq=30))
            m.assert_called_with('chassis', 'push', 'position', 'on', 'pfreq', 10, 'attitude', 'on', 'afreq', 20, 'status', 'on', 'sfreq', 30)

    def test_chassis_push_on_raise(self):
        self.assertRaises(AssertionError, self.commander.chassis_push_on)

    def test_chassis_push_off(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.chassis_push_off(all=True))
            m.assert_called_with('chassis', 'push', 'position', 'off', 'attitude', 'off', 'status', 'off')
            self.assertEqual('ok', self.commander.chassis_push_off(position=True, attitude=True, status=True))
            m.assert_called_with('chassis', 'push', 'position', 'off', 'attitude', 'off', 'status', 'off')
            self.assertEqual('ok', self.commander.chassis_push_off(status=True))
            m.assert_called_with('chassis', 'push', 'status', 'off')

    def test_chassis_push_off_raise(self):
        self.assertRaises(AssertionError, self.commander.chassis_push_off)

    def test_gimbal_speed(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_speed(15, 20))
            m.assert_called_with('gimbal', 'speed', 'p', 15, 'y', 20)

    def test_gimbal_speed_raise(self):
        self.assertRaises(AssertionError, self.commander.gimbal_speed, -451, 450)
        self.assertRaises(AssertionError, self.commander.gimbal_speed, 450, 451)
        self.assertRaises(AssertionError, self.commander.gimbal_speed, 451, 450)
        self.assertRaises(AssertionError, self.commander.gimbal_speed, 450, -451)

    def test_gimbal_move(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_move(42, -42))
            m.assert_called_with('gimbal', 'move', 'p', 42, 'y', -42)
            self.assertEqual('ok', self.commander.gimbal_move(42, -42, 120))
            m.assert_called_with('gimbal', 'move', 'p', 42, 'y', -42, 'vp', 120)
            self.assertEqual('ok', self.commander.gimbal_move(42, -42, 120, 150))
            m.assert_called_with('gimbal', 'move', 'p', 42, 'y', -42, 'vp', 120, 'vy', 150)

    def test_gimbal_move_raise(self):
        self.assertRaises(AssertionError, self.commander.gimbal_move, 56, 55)
        self.assertRaises(AssertionError, self.commander.gimbal_move, 55, -56)
        self.assertRaises(AssertionError, self.commander.gimbal_move, 0, 0, 541)
        self.assertRaises(AssertionError, self.commander.gimbal_move, 0, 0, 1, 541)

    def test_gimbal_moveto(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_moveto(12, -12))
            m.assert_called_with('gimbal', 'moveto', 'p', 12, 'y', -12)
            self.assertEqual('ok', self.commander.gimbal_moveto(12, -12, 120))
            m.assert_called_with('gimbal', 'moveto', 'p', 12, 'y', -12, 'vp', 120)
            self.assertEqual('ok', self.commander.gimbal_moveto(12, -12, 120, 150))
            m.assert_called_with('gimbal', 'moveto', 'p', 12, 'y', -12, 'vp', 120, 'vy', 150)

    def test_gimbal_moveto_raise(self):
        self.assertRaises(AssertionError, self.commander.gimbal_moveto, 56, 55)
        self.assertRaises(AssertionError, self.commander.gimbal_moveto, 55, -56)
        self.assertRaises(AssertionError, self.commander.gimbal_moveto, 0, 0, 541)
        self.assertRaises(AssertionError, self.commander.gimbal_moveto, 0, 0, 1, 541)

    def test_gimbal_suspend(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_suspend())
            m.assert_called_with('gimbal', 'suspend')

    def test_gimbal_resume(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_resume())
            m.assert_called_with('gimbal', 'resume')

    def test_gimbal_recenter(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_recenter())
            m.assert_called_with('gimbal', 'recenter')

    def test_get_gimbal_attitude(self):
        with patch('robomasterpy.Commander._do', return_value='-10 20') as m:
            self.assertEqual(robomasterpy.GimbalAttitude(-10, 20), self.commander.get_gimbal_attitude())
            m.assert_called_with('gimbal', 'attitude', '?')

    def test_gimbal_push_on(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_push_on(attitude_freq=20))
            m.assert_called_with('gimbal', 'push', 'attitude', 'on', 'afreq', 20)

    def test_gimbal_push_on_raise(self):
        self.assertRaises(AssertionError, self.commander.gimbal_push_on, 17)

    def test_gimbal_push_off(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.gimbal_push_off(True))
            m.assert_called_with('gimbal', 'push', 'attitude', 'off')

    def test_gimbal_push_off_raise(self):
        self.assertRaises(AssertionError, self.commander.chassis_push_off, False)

    def test_armor_sensitivity(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.armor_sensitivity(8))
            m.assert_called_with('armor', 'sensitivity', 8)

    def test_armor_sensitivity_raise(self):
        self.assertRaises(AssertionError, self.commander.armor_sensitivity, 0)
        self.assertRaises(AssertionError, self.commander.armor_sensitivity, 11)

    def test_get_armor_sensitivity(self):
        with patch('robomasterpy.Commander._do', return_value='7') as m:
            self.assertEqual(7, self.commander.get_armor_sensitivity())
            m.assert_called_with('armor', 'sensitivity', '?')

    def test_armor_event(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.armor_event(robomasterpy.ARMOR_HIT, True))
            m.assert_called_with('armor', 'event', robomasterpy.ARMOR_HIT, 'on')
            self.assertEqual('ok', self.commander.armor_event(robomasterpy.ARMOR_HIT, False))
            m.assert_called_with('armor', 'event', robomasterpy.ARMOR_HIT, 'off')

    def test_armor_event_raise(self):
        self.assertRaises(AssertionError, self.commander.armor_event, 'whatever', True)
        self.assertRaises(AssertionError, self.commander.armor_event, 'whatever', False)

    def test_sound_event(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.sound_event(robomasterpy.SOUND_APPLAUSE, True))
            m.assert_called_with('sound', 'event', robomasterpy.SOUND_APPLAUSE, 'on')
            self.assertEqual('ok', self.commander.sound_event(robomasterpy.SOUND_APPLAUSE, False))
            m.assert_called_with('sound', 'event', robomasterpy.SOUND_APPLAUSE, 'off')

    def test_sound_event_raise(self):
        self.assertRaises(AssertionError, self.commander.sound_event, 'whatever', True)
        self.assertRaises(AssertionError, self.commander.sound_event, 'whatever', False)

    def test_led_control(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.led_control(robomasterpy.LED_TOP_ALL, robomasterpy.LED_EFFECT_SCROLLING, 255, 128, 64))
            m.assert_called_with('led', 'control', 'comp', robomasterpy.LED_TOP_ALL, 'r', 255, 'g', 128, 'b', 64, 'effect', robomasterpy.LED_EFFECT_SCROLLING)

    def test_led_raise(self):
        self.assertRaises(AssertionError, self.commander.led_control, 'whatever', robomasterpy.LED_EFFECT_SCROLLING, 255, 128, 64)
        self.assertRaises(AssertionError, self.commander.led_control, robomasterpy.LED_ALL, 'whatever', 255, 128, 64)
        self.assertRaises(AssertionError, self.commander.led_control, robomasterpy.LED_TOP_ALL, robomasterpy.LED_EFFECT_SCROLLING, 256, 128, 64)
        self.assertRaises(AssertionError, self.commander.led_control, robomasterpy.LED_TOP_ALL, robomasterpy.LED_EFFECT_SCROLLING, 255, 256, 64)
        self.assertRaises(AssertionError, self.commander.led_control, robomasterpy.LED_TOP_ALL, robomasterpy.LED_EFFECT_SCROLLING, 255, 255, 256)

    def test_ir_sensor_measure(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.ir_sensor_measure(True))
            m.assert_called_with('ir_distance_sensor', 'measure', 'on')
            self.assertEqual('ok', self.commander.ir_sensor_measure(False))
            m.assert_called_with('ir_distance_sensor', 'measure', 'off')

    def test_get_ir_sensor_distance(self):
        with patch('robomasterpy.Commander._do', return_value='57.3456') as m:
            self.assertEqual(57.3456, self.commander.get_ir_sensor_distance(4))
            m.assert_called_with('ir_distance_sensor', 'distance', 4, '?')

    def test_get_ir_sensor_distance_raise(self):
        self.assertRaises(AssertionError, self.commander.get_ir_sensor_distance, 0)
        self.assertRaises(AssertionError, self.commander.get_ir_sensor_distance, 5)

    def test_stream(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.stream(True))
            m.assert_called_with('stream', 'on')
            self.assertEqual('ok', self.commander.stream(False))
            m.assert_called_with('stream', 'off')

    def test_audio(self):
        with patch('robomasterpy.Commander._do', return_value='ok') as m:
            self.assertEqual('ok', self.commander.audio(True))
            m.assert_called_with('audio', 'on')
            self.assertEqual('ok', self.commander.audio(False))
            m.assert_called_with('audio', 'off')


class TestPushListener(TestCase):
    def test__parse(self):
        with patch('robomasterpy.framework.PushListener.__init__', return_value=None):
            # noinspection PyArgumentList
            listener = framework.PushListener()
            ans = listener._parse('chassis push attitude -0.894 -0.117 0.423 ; status 0 1 0 0 0 0 0 0 0 0 0 ;gimbal push attitude -0.300 -0.100 ;chassis push position 0.001 0.000 ; attitude -0.892 -0.115 0.422 ;')
            self.assertEqual([
                robomasterpy.ChassisAttitude(pitch=-0.894, roll=-0.117, yaw=0.423),
                robomasterpy.ChassisStatus(static=False, uphill=True, downhill=False, on_slope=False, pick_up=False, slip=False, impact_x=False, impact_y=False, impact_z=False, roll_over=False, hill_static=False),
                robomasterpy.GimbalAttitude(pitch=-0.3, yaw=-0.1),
                robomasterpy.ChassisPosition(x=0.001, y=0.0, z=None),
                robomasterpy.ChassisAttitude(pitch=-0.892, roll=-0.115, yaw=0.422),
            ], ans)

            ans = listener._parse('gimbal push attitude -0.300 -0.100 ;')
            self.assertEqual([robomasterpy.GimbalAttitude(pitch=-0.3, yaw=-0.1)], ans)

            self.assertRaises(AssertionError, listener._parse, '')
            self.assertRaises(AssertionError, listener._parse, 'whatever')


class TestEventListener(TestCase):
    def test__parse(self):
        with patch('robomasterpy.framework.EventListener.__init__', return_value=None):
            # noinspection PyArgumentList
            listener = framework.EventListener()
            ans = listener._parse('armor event hit 1 0 ;armor event hit 2 1 ;armor event hit 3 0 ;armor event hit 4 0 ;sound event applause 2 ;sound event applause 3 ;sound event applause 2 ;')
            self.assertEqual([
                robomasterpy.ArmorHitEvent(index=1, type=0),
                robomasterpy.ArmorHitEvent(index=2, type=1),
                robomasterpy.ArmorHitEvent(index=3, type=0),
                robomasterpy.ArmorHitEvent(index=4, type=0),
                robomasterpy.SoundApplauseEvent(count=2),
                robomasterpy.SoundApplauseEvent(count=3),
                robomasterpy.SoundApplauseEvent(count=2),
            ], ans)

            ans = listener._parse('sound event applause 2 ;')
            self.assertEqual([
                robomasterpy.SoundApplauseEvent(count=2),
            ], ans)

            self.assertRaises(AssertionError, listener._parse, '')
            self.assertRaises(AssertionError, listener._parse, 'whatever')
