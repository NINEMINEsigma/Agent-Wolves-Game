"""
完整狼人杀游戏整合器
集成所有组件，提供统一的游戏启动接口
"""

import asyncio
import json
import logging
import random
from typing import Dict, List, Any, Optional
from pathlib import Path

from .ai_agent import BaseAIAgent
from .llm_interface import LLMInterface
from .agents.agent_factory import AgentFactory
from .game_engine import WerewolfGameEngine
from .translation_manager import TranslationManager


class WerewolfGame:
    """完整的狼人杀游戏"""
    
    def __init__(self, config_path: str = "config.json"):
        """
        初始化游戏
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = config_path
        
        # 首先初始化logger
        self.logger = logging.getLogger(__name__)
        
        # 然后加载配置和提示词
        self.config = self._load_config()
        
        # 游戏组件
        self.llm_interface = None
        self.players: List[BaseAIAgent] = []
        self.game_engine = None
        
        # 角色提示词
        self.role_prompts = self._load_role_prompts()
        self.game_prompts = self._load_game_prompts()
        
        # 翻译管理器
        self.translation_manager = TranslationManager()
    
    def _load_config(self) -> Dict[str, Any]:
        """加载游戏配置"""
        try:
            from .config_validator import ConfigValidator
            validator = ConfigValidator(self.config_path)
            config = validator.load_config()
            self.logger.info(f"成功加载配置文件: {self.config_path}")
            return config
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            # 返回默认配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
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
                "max_rounds": 10,
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
            },
            "translation_settings": {
                "translation_file": "translations/zh_CN.json",
                "fallback_to_default": True
            }
        }
    
    def _load_role_prompts(self) -> Dict[str, Any]:
        """加载角色提示词"""
        try:
            with open("prompts/role_prompts.json", 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            self.logger.info("成功加载角色提示词")
            return prompts
        except Exception as e:
            self.logger.error(f"加载角色提示词失败: {e}")
            return {}
    
    def _load_game_prompts(self) -> Dict[str, Any]:
        """加载游戏提示词"""
        try:
            with open("prompts/game_prompts.json", 'r', encoding='utf-8') as f:
                prompts = json.load(f)
            self.logger.info("成功加载游戏提示词")
            return prompts
        except Exception as e:
            self.logger.error(f"加载游戏提示词失败: {e}")
            return {}
    
    async def initialize(self) -> bool:
        """
        初始化游戏组件
        
        Returns:
            是否初始化成功
        """
        try:
            # 1. 验证游戏配置
            if not self._validate_game_config():
                self.logger.error("游戏配置验证失败")
                return False
            
            # 2. 初始化LLM接口
            self.llm_interface = LLMInterface(self.config)
            
            # 3. 测试LLM连接
            test_response = await self.llm_interface.generate_response(
                "简单回复：连接测试成功",
                "你是一个AI助手"
            )
            
            if not test_response:
                self.logger.error("LLM连接测试失败")
                return False
            
            # 4. 创建AI玩家
            await self._create_players()
            
            # 5. 初始化游戏引擎
            self.game_engine = WerewolfGameEngine(self.config, self.players)
            
            self.logger.info("游戏组件初始化完成")
            return True
            
        except Exception as e:
            self.logger.error(f"游戏初始化异常: {e}")
            return False
    
    async def _create_players(self) -> None:
        """创建AI玩家"""
        role_counts = self.config.get("game_settings", {}).get("roles", {})
        player_id = 1
        
        # 创建角色列表
        role_list = []
        for role, count in role_counts.items():
            role_list.extend([role] * count)
        
        # 随机打乱角色分配
        random.shuffle(role_list)
        
        # 创建身份系统
        from src.identity_system import IdentitySystem
        identity_system = IdentitySystem()
        
        # 获取记忆配置
        memory_config = self.config.get("memory_settings", {})
        
        # 确保包含夜晚记忆配置
        if "night_discussion_memory_limit" not in memory_config:
            memory_config["night_discussion_memory_limit"] = 20
        if "night_thinking_memory_limit" not in memory_config:
            memory_config["night_thinking_memory_limit"] = 15
        if "include_night_context_in_speech" not in memory_config:
            memory_config["include_night_context_in_speech"] = True
        
        # 创建Agent工厂
        agent_factory = AgentFactory(self.config)
        
        # 创建玩家
        for role in role_list:
            # 统一命名为"玩家N"，确保AI之间无法通过名称识别角色身份
            # 身份隐藏仅针对AI，用户界面会显示完整信息供观察
            player_name = f"玩家{player_id}"
            
            # 使用Agent工厂创建对应的AI代理
            player = agent_factory.create_agent(
                player_id, player_name, role, self.llm_interface, 
                self.role_prompts, identity_system, memory_config
            )
            
            self.players.append(player)
            player_id += 1
        
        self.logger.info(f"创建了{len(self.players)}个AI玩家")
    
    def _validate_game_config(self) -> bool:
        """
        验证游戏配置
        
        Returns:
            配置是否有效
        """
        try:
            from .config_validator import ConfigValidator
            validator = ConfigValidator()
            
            # 验证游戏设置
            game_validation = validator.validate_game_settings(self.config)
            role_validation = validator.validate_role_distribution(self.config)
            
            # 检查验证结果
            all_valid = all(game_validation.values()) and role_validation["is_valid"]
            
            if not all_valid:
                self.logger.error("游戏配置验证失败:")
                
                # 显示游戏设置问题
                for setting, is_valid in game_validation.items():
                    if not is_valid:
                        self.logger.error(f"  - {setting}: 配置无效")
                
                # 显示角色分配问题
                if not role_validation["is_valid"]:
                    self.logger.error("  - 角色分配问题:")
                    for issue in role_validation["issues"]:
                        self.logger.error(f"    * {issue}")
                
                # 提供修复建议
                suggestions = validator.suggest_config_fixes({
                    "role_distribution": role_validation
                })
                if suggestions:
                    self.logger.error("  - 修复建议:")
                    for suggestion in suggestions:
                        self.logger.error(f"    * {suggestion}")
                
                return False
            
            self.logger.info("游戏配置验证通过")
            return True
            
        except Exception as e:
            self.logger.error(f"配置验证异常: {e}")
            return False
    
    def _get_role_name(self, role: str) -> str:
        """获取角色名翻译"""
        return self.translation_manager.get_role_name(role)
    
    async def start(self) -> Dict[str, Any]:
        """
        开始游戏
        
        Returns:
            游戏结果
        """
        try:
            # 检查初始化状态
            if not self.game_engine:
                self.logger.error("游戏引擎未初始化")
                return {"success": False, "error": "游戏引擎未初始化"}
            
            # 启动游戏
            self.logger.info("开始AI狼人杀游戏")
            result = await self.game_engine.start_game()
            
            return result
            
        except Exception as e:
            self.logger.error(f"游戏启动异常: {e}")
            return {"success": False, "error": str(e)}
    
    def get_player_info(self) -> List[Dict[str, Any]]:
        """
        获取玩家信息
        
        Returns:
            玩家信息列表
        """
        return [
            {
                "id": player.player_id,
                "name": player.name,
                "role": player.role,
                "is_alive": player.is_alive
            }
            for player in self.players
        ]
    
    def get_game_status(self) -> Dict[str, Any]:
        """
        获取游戏状态
        
        Returns:
            游戏状态信息
        """
        if self.game_engine:
            return self.game_engine.get_game_status()
        else:
            return {
                "is_running": False,
                "status": "not_initialized"
            }
    
    async def quick_demo(self) -> Dict[str, Any]:
        """
        快速演示模式（使用配置文件中的设置）
        
        Returns:
            演示结果
        """
        try:
            self.logger.info("启动快速演示模式")
            
            # 使用配置文件中的设置，但限制最大回合数用于演示
            demo_config = self.config.copy()
            demo_config["game_settings"]["max_rounds"] = min(
                demo_config["game_settings"].get("max_rounds", 10), 3
            )
            
            # 验证演示配置
            from .config_validator import ConfigValidator
            validator = ConfigValidator()
            role_validation = validator.validate_role_distribution(demo_config)
            
            if not role_validation["is_valid"]:
                self.logger.error("演示配置验证失败:")
                for issue in role_validation["issues"]:
                    self.logger.error(f"  - {issue}")
                return {"success": False, "error": "演示配置无效"}
            
            # 重新初始化 - 清空现有玩家列表
            self.config = demo_config
            self.players = []  # 清空玩家列表
            await self._create_players()
            self.game_engine = WerewolfGameEngine(self.config, self.players)
            
            # 开始演示
            result = await self.game_engine.start_game()
            
            self.logger.info("快速演示完成")
            return result
            
        except Exception as e:
            self.logger.error(f"快速演示异常: {e}")
            return {"success": False, "error": str(e)}
    
    def pause(self) -> bool:
        """
        暂停游戏
        
        Returns:
            是否成功暂停
        """
        if self.game_engine:
            self.game_engine.pause_game()
            return True
        return False
    
    def resume(self) -> bool:
        """
        恢复游戏
        
        Returns:
            是否成功恢复
        """
        if self.game_engine:
            self.game_engine.resume_game()
            return True
        return False
    
    def stop(self) -> bool:
        """
        停止游戏
        
        Returns:
            是否成功停止
        """
        if self.game_engine:
            self.game_engine.stop_game()
            return True
        return False
    
    def save_config(self, filename: Optional[str] = None) -> str:
        """
        保存当前配置
        
        Args:
            filename: 保存文件名
            
        Returns:
            保存的文件路径
        """
        try:
            if not filename:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"config_backup_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"配置已保存到: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return ""
    
    @staticmethod
    def validate_environment() -> Dict[str, bool]:
        """
        验证运行环境
        
        Returns:
            环境检查结果
        """
        results = {
            "config_file": False,
            "role_prompts": False,
            "game_prompts": False,
            "llm_connection": False
        }
        
        # 检查配置文件
        if Path("config.json").exists():
            results["config_file"] = True
        
        # 检查提示词文件
        if Path("prompts/role_prompts.json").exists():
            results["role_prompts"] = True
        
        if Path("prompts/game_prompts.json").exists():
            results["game_prompts"] = True
        
        # 检查LLM连接（使用配置中的URL）
        try:
            import requests
            from .config_validator import ConfigValidator
            validator = ConfigValidator()
            config = validator.load_config()
            ollama_url = config.get("ai_settings", {}).get("ollama_base_url", "http://localhost:11434")
            response = requests.get(f"{ollama_url}/api/tags", timeout=5)
            if response.status_code == 200:
                results["llm_connection"] = True
        except:
            pass
        
        return results
    
    def get_environment_report(self) -> str:
        """
        获取环境检查报告
        
        Returns:
            环境报告文本
        """
        validation = self.validate_environment()
        
        report = "🔍 环境检查报告\n"
        report += "=" * 30 + "\n"
        
        for item, status in validation.items():
            icon = "✅" if status else "❌"
            item_name = {
                "config_file": "配置文件",
                "role_prompts": "角色提示词",
                "game_prompts": "游戏提示词",
                "llm_connection": "LLM连接"
            }.get(item, item)
            
            report += f"{icon} {item_name}\n"
        
        # 总体状态
        all_ok = all(validation.values())
        if all_ok:
            report += "\n🎉 环境检查全部通过，可以开始游戏！"
        else:
            report += "\n⚠️ 存在环境问题，请检查缺失项目"
        
        return report
    
    async def test_ai_functionality(self) -> Dict[str, Any]:
        """
        测试AI功能
        
        Returns:
            测试结果
        """
        try:
            if not self.llm_interface:
                self.llm_interface = LLMInterface(self.config)
            
            # 测试基础对话
            test_prompt = "请简单回复：AI狼人杀测试成功"
            response = await self.llm_interface.generate_response(
                test_prompt, "你是一个友好的AI助手"
            )
            
            if response:
                return {
                    "success": True,
                    "response": response,
                    "message": "AI功能测试通过"
                }
            else:
                return {
                    "success": False,
                    "message": "AI未返回有效响应"
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "AI功能测试失败"
            }


async def create_and_run_game(config_path: str = "config.json") -> Dict[str, Any]:
    """
    创建并运行完整游戏的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        游戏结果
    """
    game = WerewolfGame(config_path)
    
    # 初始化
    init_success = await game.initialize()
    if not init_success:
        return {"success": False, "error": "游戏初始化失败"}
    
    # 开始游戏
    result = await game.start()
    return result


async def run_quick_demo(config_path: str = "config.json") -> Dict[str, Any]:
    """
    运行快速演示的便捷函数
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        演示结果
    """
    game = WerewolfGame(config_path)
    
    # 初始化
    init_success = await game.initialize()
    if not init_success:
        return {"success": False, "error": "游戏初始化失败"}
    
    # 运行演示
    result = await game.quick_demo()
    return result 