"""
配置验证和加载工具
提供统一的配置管理，确保config.json真正生效
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List


class ConfigValidator:
    """配置验证和加载工具"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化配置验证器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        self.logger = logging.getLogger(__name__)
        
    def load_config(self) -> Dict[str, Any]:
        """
        加载并验证配置文件
        
        Returns:
            验证后的配置字典
        """
        try:
            # 尝试加载配置文件
            if Path(self.config_path).exists():
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_path}")
            else:
                self.logger.warning(f"配置文件不存在: {self.config_path}，使用默认配置")
                config = {}
            
            # 验证和补充配置
            validated_config = self._validate_and_merge_config(config)
            return validated_config
            
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            return self._get_default_config()
    
    def _validate_and_merge_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证配置并补充缺失的默认值
        
        Args:
            config: 原始配置
            
        Returns:
            验证后的完整配置
        """
        default_config = self._get_default_config()
        validated_config = {}
        
        # 验证和合并AI设置
        ai_settings = config.get("ai_settings", {})
        validated_config["ai_settings"] = {
            "model_name": ai_settings.get("model_name", default_config["ai_settings"]["model_name"]),
            "ollama_base_url": ai_settings.get("ollama_base_url", default_config["ai_settings"]["ollama_base_url"]),
            "temperature": ai_settings.get("temperature", default_config["ai_settings"]["temperature"]),
            "max_tokens": ai_settings.get("max_tokens", default_config["ai_settings"]["max_tokens"]),
            "thinking_mode": ai_settings.get("thinking_mode", default_config["ai_settings"]["thinking_mode"]),
            "context_length": ai_settings.get("context_length", default_config["ai_settings"]["context_length"]),
            "presence_penalty": ai_settings.get("presence_penalty", default_config["ai_settings"]["presence_penalty"])
        }
        
        # 验证和合并游戏设置
        game_settings = config.get("game_settings", {})
        validated_config["game_settings"] = {
            "total_players": game_settings.get("total_players", default_config["game_settings"]["total_players"]),
            "roles": game_settings.get("roles", default_config["game_settings"]["roles"]),
            "discussion_time": game_settings.get("discussion_time", default_config["game_settings"]["discussion_time"])
        }
        
        # max_rounds是可选的，只有在配置文件中明确设置时才添加
        if "max_rounds" in game_settings:
            validated_config["game_settings"]["max_rounds"] = game_settings["max_rounds"]
        
        # 验证和合并UI设置
        ui_settings = config.get("ui_settings", {})
        validated_config["ui_settings"] = {
            "display_thinking": ui_settings.get("display_thinking", default_config["ui_settings"]["display_thinking"]),
            "auto_scroll": ui_settings.get("auto_scroll", default_config["ui_settings"]["auto_scroll"]),
            "save_logs": ui_settings.get("save_logs", default_config["ui_settings"]["save_logs"]),
            "show_reasoning": ui_settings.get("show_reasoning", default_config["ui_settings"]["show_reasoning"]),
            "show_roles_to_user": ui_settings.get("show_roles_to_user", default_config["ui_settings"]["show_roles_to_user"]),
            "hide_roles_from_ai": ui_settings.get("hide_roles_from_ai", default_config["ui_settings"]["hide_roles_from_ai"]),
            "reveal_roles_on_death": ui_settings.get("reveal_roles_on_death", default_config["ui_settings"]["reveal_roles_on_death"]),
            "observation_delays": ui_settings.get("observation_delays", default_config["ui_settings"]["observation_delays"])
        }
        
        return validated_config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        获取与config.json一致的默认配置
        
        Returns:
            默认配置字典
        """
        return {
            "ai_settings": {
                "model_name": "qwen3:0.6b",
                "ollama_base_url": "http://localhost:11434",
                "temperature": 1.1,
                "max_tokens": 800,
                "thinking_mode": True,
                "context_length": 4096,
                "presence_penalty": 1.5
            },
            "game_settings": {
                "total_players": 7,
                "roles": {
                    "villager": 3,
                    "werewolf": 2,
                    "seer": 1,
                    "witch": 1
                },
                "discussion_time": 60
            },
            "ui_settings": {
                "display_thinking": True,
                "auto_scroll": True,
                "save_logs": True,
                "show_reasoning": True,
                "show_roles_to_user": True,
                "hide_roles_from_ai": True,
                "reveal_roles_on_death": True,
                "observation_delays": {
                    "phase_transition": 2.0,
                    "action_result": 1.5,
                    "death_announcement": 3.0,
                    "speech": 2.0,
                    "voting_result": 1.5
                }
            }
        }
    
    def validate_config(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """
        验证配置的完整性
        
        Args:
            config: 要验证的配置
            
        Returns:
            验证结果字典
        """
        results = {
            "ai_settings": False,
            "game_settings": False,
            "ui_settings": False,
            "model_name": False,
            "ollama_url": False,
            "roles_config": False
        }
        
        # 验证AI设置
        ai_settings = config.get("ai_settings", {})
        if ai_settings:
            results["ai_settings"] = True
            results["model_name"] = bool(ai_settings.get("model_name"))
            results["ollama_url"] = bool(ai_settings.get("ollama_base_url"))
        
        # 验证游戏设置
        game_settings = config.get("game_settings", {})
        if game_settings:
            results["game_settings"] = True
            results["roles_config"] = bool(game_settings.get("roles"))
        
        # 验证UI设置
        ui_settings = config.get("ui_settings", {})
        if ui_settings:
            results["ui_settings"] = True
        
        return results
    
    def get_config_value(self, config: Dict[str, Any], key_path: str, default: Any = None) -> Any:
        """
        安全地获取配置值
        
        Args:
            config: 配置字典
            key_path: 键路径，如 "ai_settings.model_name"
            default: 默认值
            
        Returns:
            配置值或默认值
        """
        try:
            keys = key_path.split(".")
            value = config
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def validate_game_settings(self, config: Dict[str, Any]) -> Dict[str, bool]:
        """
        验证游戏设置的完整性
        
        Args:
            config: 游戏配置
            
        Returns:
            验证结果字典
        """
        results = {
            "total_players": False,
            "roles_config": False,
            "role_distribution": False,
            "discussion_time": False
        }
        
        game_settings = config.get("game_settings", {})
        
        # 验证总玩家数
        total_players = game_settings.get("total_players")
        if total_players and isinstance(total_players, int) and 5 <= total_players <= 12:
            results["total_players"] = True
        
        # 验证角色配置
        roles = game_settings.get("roles", {})
        if roles and isinstance(roles, dict):
            results["roles_config"] = True
            
            # 验证角色分配
            role_validation = self.validate_role_distribution(config)
            results["role_distribution"] = role_validation["is_valid"]
        
        # 验证最大回合数（可选配置）
        max_rounds = game_settings.get("max_rounds")
        if max_rounds is not None:
            if isinstance(max_rounds, int) and 1 <= max_rounds <= 100:
                # max_rounds配置有效，但不需要在results中标记
                pass
            else:
                # max_rounds配置无效，记录错误但不影响其他验证
                self.logger.warning(f"max_rounds配置无效: {max_rounds}，应为1-100之间的整数")
        
        # 验证讨论时间
        discussion_time = game_settings.get("discussion_time")
        if discussion_time and isinstance(discussion_time, (int, float)) and 10 <= discussion_time <= 300:
            results["discussion_time"] = True
        
        return results
    
    def validate_role_distribution(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        验证角色分配是否合理
        
        Args:
            config: 游戏配置
            
        Returns:
            验证结果字典
        """
        game_settings = config.get("game_settings", {})
        total_players = game_settings.get("total_players", 0)
        roles = game_settings.get("roles", {})
        
        # 计算角色总数
        total_from_roles = self.get_total_players_from_roles(roles)
        
        # 检查总数是否一致
        is_valid = total_from_roles == total_players
        
        # 检查角色分配是否合理
        issues = []
        if not is_valid:
            issues.append(f"角色总数({total_from_roles})与总玩家数({total_players})不一致")
        
        # 检查必要角色
        if roles.get("werewolf", 0) == 0:
            issues.append("缺少狼人角色")
        if roles.get("villager", 0) == 0:
            issues.append("缺少村民角色")
        
        # 检查角色数量合理性
        werewolf_count = roles.get("werewolf", 0)
        villager_count = roles.get("villager", 0)
        
        if werewolf_count > villager_count:
            issues.append("狼人数量不能超过村民数量")
        
        if werewolf_count > total_players // 2:
            issues.append("狼人数量过多，游戏不平衡")
        
        return {
            "is_valid": is_valid and len(issues) == 0,
            "total_players": total_players,
            "total_from_roles": total_from_roles,
            "roles": roles,
            "issues": issues
        }
    
    def get_total_players_from_roles(self, roles: Dict[str, int]) -> int:
        """
        从角色配置计算总玩家数
        
        Args:
            roles: 角色配置字典
            
        Returns:
            总玩家数
        """
        return sum(roles.values())
    
    def suggest_config_fixes(self, validation_results: Dict[str, Any]) -> List[str]:
        """
        根据验证结果提供配置修复建议
        
        Args:
            validation_results: 验证结果
            
        Returns:
            修复建议列表
        """
        suggestions = []
        
        role_validation = validation_results.get("role_distribution", {})
        if not role_validation.get("is_valid", True):
            total_players = role_validation.get("total_players", 0)
            total_from_roles = role_validation.get("total_from_roles", 0)
            roles = role_validation.get("roles", {})
            issues = role_validation.get("issues", [])
            
            for issue in issues:
                if "不一致" in issue:
                    if total_from_roles > total_players:
                        suggestions.append(f"减少角色数量，当前总数为{total_from_roles}，需要{total_players}")
                    else:
                        suggestions.append(f"增加角色数量，当前总数为{total_from_roles}，需要{total_players}")
                
                elif "缺少狼人" in issue:
                    suggestions.append("添加至少1个狼人角色")
                
                elif "缺少村民" in issue:
                    suggestions.append("添加至少1个村民角色")
                
                elif "狼人数量不能超过村民" in issue:
                    suggestions.append("减少狼人数量或增加村民数量")
                
                elif "狼人数量过多" in issue:
                    suggestions.append(f"减少狼人数量，建议不超过{total_players // 2}个")
        
        return suggestions 