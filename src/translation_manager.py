"""
翻译管理工具类
统一管理游戏中的各种翻译，支持从配置文件加载翻译
"""

import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path


class TranslationManager:
    """翻译管理器"""
    
    def __init__(self, config_path: str = "translations/zh_CN.json"):
        """
        初始化翻译管理器
        
        Args:
            config_path: 翻译配置文件路径
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        self.translations = {}
        self.load_translations()
    
    def load_translations(self) -> Dict[str, Any]:
        """
        加载翻译配置
        
        Returns:
            翻译配置字典
        """
        try:
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.translations = json.load(f)
                self.logger.info(f"成功加载翻译配置: {self.config_path}")
            else:
                self.logger.warning(f"翻译配置文件不存在: {self.config_path}，使用默认翻译")
                self.translations = self._get_default_translations()
        except Exception as e:
            self.logger.error(f"加载翻译配置失败: {e}，使用默认翻译")
            self.translations = self._get_default_translations()
        
        return self.translations
    
    def get_translation(self, key_path: str, default: Optional[str] = None) -> str:
        """
        获取翻译文本
        
        Args:
            key_path: 翻译键路径，支持点号分隔的嵌套路径，如 "roles.villager"
            default: 默认值，如果找不到翻译则返回此值
            
        Returns:
            翻译后的文本
        """
        try:
            keys = key_path.split('.')
            value = self.translations
            
            for key in keys:
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    return default if default is not None else key_path
            
            return str(value) if value is not None else (default if default is not None else key_path)
            
        except Exception as e:
            self.logger.error(f"获取翻译失败 {key_path}: {e}")
            return default if default is not None else key_path
    
    def get_role_name(self, role: str) -> str:
        """
        获取角色名称翻译
        
        Args:
            role: 角色英文名称
            
        Returns:
            角色中文名称
        """
        return self.get_translation(f"roles.{role}", role)
    
    def get_phase_name(self, phase: str) -> str:
        """
        获取游戏阶段名称翻译
        
        Args:
            phase: 阶段英文名称
            
        Returns:
            阶段中文名称
        """
        return self.get_translation(f"phases.{phase}", phase)
    
    def get_game_term(self, term: str) -> str:
        """
        获取游戏术语翻译
        
        Args:
            term: 术语英文名称
            
        Returns:
            术语中文名称
        """
        return self.get_translation(f"game_terms.{term}", term)
    
    def get_ui_message(self, message: str) -> str:
        """
        获取UI消息翻译
        
        Args:
            message: 消息英文名称
            
        Returns:
            消息中文内容
        """
        return self.get_translation(f"ui_messages.{message}", message)
    
    def reload_translations(self) -> bool:
        """
        重新加载翻译配置
        
        Returns:
            是否成功重新加载
        """
        try:
            self.load_translations()
            return True
        except Exception as e:
            self.logger.error(f"重新加载翻译配置失败: {e}")
            return False
    
    def _get_default_translations(self) -> Dict[str, Any]:
        """
        获取默认翻译配置
        
        Returns:
            默认翻译配置字典
        """
        return {
            "roles": {
                "villager": "村民",
                "werewolf": "狼人",
                "seer": "预言家",
                "witch": "女巫",
                "hunter": "猎人",
                "guard": "守卫"
            },
            "phases": {
                "preparation": "准备阶段",
                "night": "夜晚",
                "day": "白天",
                "discussion": "讨论阶段",
                "voting": "投票阶段",
                "game_end": "游戏结束"
            },
            "game_terms": {
                "victory": "胜利",
                "defeat": "失败",
                "alive": "存活",
                "dead": "死亡",
                "round": "轮",
                "player": "玩家",
                "total_players": "总玩家数",
                "game_mode": "游戏模式",
                "max_rounds": "最大回合数",
                "ai_model": "AI模型",
                "player_list": "玩家名单",
                "current_status": "当前状态",
                "surviving": "存活",
                "victory_probability": "胜率预测",
                "role_statistics": "角色统计",
                "thanks_for_watching": "感谢观看AI狼人杀"
            },
            "ui_messages": {
                "game_start": "AI狼人杀游戏开始！",
                "game_settings": "游戏设置",
                "player_list_title": "玩家名单",
                "watch_ai_game": "观看AI们的智慧博弈吧！",
                "current_status_title": "当前状态",
                "surviving_players": "存活",
                "victory_prediction": "胜率预测",
                "role_summary": "角色统计",
                "game_end_thanks": "感谢观看AI狼人杀！",
                "round_limit_reached": "达到最大回合数限制",
                "thinking_process": "思考中...",
                "death_announcement": "死亡公告",
                "voting_result": "投票结果",
                "night_action": "夜晚行动"
            }
        } 