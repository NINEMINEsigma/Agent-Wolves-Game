"""
Agent工厂系统
提供统一的Agent创建接口，只支持Agent模式
"""

import logging
from typing import Dict, Any, List, Optional
from .base_agent import BaseGameAgent
from .role_agents.witch_agent import WitchAgent
from .role_agents.seer_agent import SeerAgent
from .role_agents.werewolf_agent import WerewolfAgent
from .role_agents.villager_agent import VillagerAgent


class AgentFactory:
    """Agent工厂类"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Agent工厂
        
        Args:
            config: 配置字典，包含Agent设置
        """
        self.config = config
        self.agent_config = config.get("agent_settings", {})
        self.llm_backend = self.agent_config.get("llm_backend", "openai")
        self.tools_enabled = self.agent_config.get("tools_enabled", True)
        self.fallback_enabled = self.agent_config.get("fallback_enabled", True)
        
        self.logger = logging.getLogger(__name__)
        self.logger.info("Agent工厂初始化完成")
    
    def create_agent(self, player_id: int, name: str, role: str, llm_interface, 
                    prompts: Dict[str, Any], identity_system=None, 
                    memory_config=None):
        """
        创建Agent实例
        
        Args:
            player_id: 玩家ID
            name: 玩家名称
            role: 角色类型
            llm_interface: LLM接口
            prompts: 提示词配置
            identity_system: 身份系统
            memory_config: 记忆配置
            
        Returns:
            Agent实例
        """
        try:
            return self._create_agent_mode(player_id, name, role, llm_interface, 
                                         prompts, identity_system, memory_config)
                
        except Exception as e:
            self.logger.error(f"创建Agent失败: {e}")
            if self.fallback_enabled:
                self.logger.info("启用备用方案，创建基础Agent")
                return self._create_fallback_agent(player_id, name, role, llm_interface, 
                                                 prompts, identity_system, memory_config)
            else:
                raise
    
    def _create_agent_mode(self, player_id: int, name: str, role: str, llm_interface, 
                          prompts: Dict[str, Any], identity_system=None, 
                          memory_config=None):
        """创建Agent模式实例"""
        try:
            if role == "witch":
                agent = WitchAgent(player_id, name, llm_interface, prompts, 
                                 identity_system, memory_config)
            elif role == "seer":
                agent = SeerAgent(player_id, name, llm_interface, prompts, 
                                identity_system, memory_config)
            elif role == "werewolf":
                agent = WerewolfAgent(player_id, name, llm_interface, prompts, 
                                    identity_system, memory_config)
            elif role == "villager":
                agent = VillagerAgent(player_id, name, llm_interface, prompts, 
                                    identity_system, memory_config)
            else:
                raise ValueError(f"不支持的角色类型: {role}")
            
            self.logger.info(f"成功创建{role} Agent: 玩家{player_id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"创建Agent模式失败: {e}")
            if self.fallback_enabled:
                return self._create_fallback_agent(player_id, name, role, llm_interface, 
                                                 prompts, identity_system, memory_config)
            else:
                raise
    
    def _create_fallback_agent(self, player_id: int, name: str, role: str, llm_interface, 
                              prompts: Dict[str, Any], identity_system=None, 
                              memory_config=None):
        """创建备用Agent实例"""
        try:
            # 使用VillagerAgent作为通用备用方案
            agent = VillagerAgent(player_id, name, llm_interface, prompts, 
                                identity_system, memory_config)
            
            self.logger.info(f"成功创建备用{role} Agent: 玩家{player_id}")
            return agent
            
        except Exception as e:
            self.logger.error(f"创建备用Agent失败: {e}")
            raise
    
    def create_players(self, player_configs: List[Dict[str, Any]], llm_interface, 
                      prompts: Dict[str, Any], identity_system=None, 
                      memory_config=None) -> List[BaseGameAgent]:
        """
        批量创建玩家Agent
        
        Args:
            player_configs: 玩家配置列表
            llm_interface: LLM接口
            prompts: 提示词配置
            identity_system: 身份系统
            memory_config: 记忆配置
            
        Returns:
            Agent列表
        """
        players = []
        
        for config in player_configs:
            try:
                player_id = config["id"]
                name = config["name"]
                role = config["role"]
                
                agent = self.create_agent(player_id, name, role, llm_interface, 
                                        prompts, identity_system, memory_config)
                players.append(agent)
                
            except Exception as e:
                self.logger.error(f"创建玩家{config.get('id', 'unknown')}失败: {e}")
                if not self.fallback_enabled:
                    raise
        
        self.logger.info(f"成功创建{len(players)}个玩家Agent")
        return players
    
    def get_mode_info(self) -> Dict[str, Any]:
        """获取当前模式信息"""
        return {
            "mode": "agent",
            "llm_backend": self.llm_backend,
            "tools_enabled": self.tools_enabled,
            "fallback_enabled": self.fallback_enabled,
            "supported_roles": ["witch", "seer", "werewolf", "villager"]
        }
    
    def validate_config(self) -> Dict[str, Any]:
        """验证配置有效性"""
        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }
        
        # 检查LLM后端
        if self.llm_backend not in ["openai", "ollama", "custom"]:
            validation_result["warnings"].append(f"未知的LLM后端: {self.llm_backend}")
        
        # 检查工具设置
        if not self.tools_enabled:
            validation_result["warnings"].append("建议启用工具函数以获得更好的Agent性能")
        
        return validation_result 