# -*- coding: utf-8 -*-

# ██████╗  ██████╗ ██████╗  ██████╗ ███╗   ███╗ █████╗ ███████╗████████╗███████╗██████╗ ██████╗ ██╗   ██╗
# ██╔══██╗██╔═══██╗██╔══██╗██╔═══██╗████╗ ████║██╔══██╗██╔════╝╚══██╔══╝██╔════╝██╔══██╗██╔══██╗╚██╗ ██╔╝
# ██████╔╝██║   ██║██████╔╝██║   ██║██╔████╔██║███████║███████╗   ██║   █████╗  ██████╔╝██████╔╝ ╚████╔╝
# ██╔══██╗██║   ██║██╔══██╗██║   ██║██║╚██╔╝██║██╔══██║╚════██║   ██║   ██╔══╝  ██╔══██╗██╔═══╝   ╚██╔╝
# ██║  ██║╚██████╔╝██████╔╝╚██████╔╝██║ ╚═╝ ██║██║  ██║███████║   ██║   ███████╗██║  ██║██║        ██║
# ╚═╝  ╚═╝ ╚═════╝ ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝  ╚═╝╚══════╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝        ╚═╝

"""
RoboMasterPy: Python library and framework for RoboMaster EP
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~



:copyright: (c) 2020 by LI Zhennan.
:license: MIT, see LICENSE for more details.
"""

from . import framework
from . import measure
from .__version__ import (
    __title__, __description__, __url__, __version__,
    __author__, __author_email__, __license__, __copyright__,
)
from .client import CTX, LOG_LEVEL
from .client import (
    ChassisSpeed, ChassisPosition, ChassisAttitude, ChassisStatus,
    GimbalAttitude,
    ArmorHitEvent, SoundApplauseEvent,
)
from .client import (
    VIDEO_PORT, AUDIO_PORT, CTRL_PORT, PUSH_PORT, EVENT_PORT, IP_PORT,
    DEFAULT_BUF_SIZE,
    SWITCH_ON, SWITCH_OFF,
    MODE_CHASSIS_LEAD, MODE_GIMBAL_LEAD, MODE_FREE,
    ARMOR_HIT,
    SOUND_APPLAUSE,
    LED_ALL, LED_TOP_ALL, LED_TOP_RIGHT, LED_TOP_LEFT, LED_BOTTOM_ALL, LED_BOTTOM_FRONT, LED_BOTTOM_BACK, LED_BOTTOM_LEFT, LED_BOTTOM_RIGHT,
    LED_EFFECT_SOLID, LED_EFFECT_OFF, LED_EFFECT_PULSE, LED_EFFECT_BLINK, LED_EFFECT_SCROLLING,
)
from .client import get_broadcast_ip, Commander
