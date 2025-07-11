"""
工具函数模块
定义狼人杀游戏中各角色的工具函数
"""

from .witch_tools import WitchTools
from .seer_tools import SeerTools
from .werewolf_tools import WerewolfTools
from .common_tools import CommonTools

__all__ = [
    'WitchTools',
    'SeerTools',
    'WerewolfTools',
    'CommonTools'
] 