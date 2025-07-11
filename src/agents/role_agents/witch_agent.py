"""
女巫Agent实现
基于LlamaIndex Agent的女巫角色智能决策系统
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..base_agent import BaseGameAgent
from ..tools.witch_tools import WitchTools
from ...roles.witch import Witch


class WitchAgent(BaseGameAgent):
    """女巫Agent类，继承BaseGameAgent并实现女巫特定功能"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], 
                 identity_system=None, memory_config=None):
        # 先创建基础女巫实例来获取女巫特有属性
        self.witch_base = Witch(player_id, name, llm_interface, prompts, identity_system, memory_config)
        
        # 调用父类初始化
        super().__init__(player_id, name, "witch", llm_interface, prompts, identity_system, memory_config)
        
        # 复制女巫特有属性
        self.has_antidote = self.witch_base.has_antidote
        self.has_poison = self.witch_base.has_poison
        self.saved_players = self.witch_base.saved_players
        self.poisoned_players = self.witch_base.poisoned_players
        self.last_night_death = self.witch_base.last_night_death
        self.save_strategy = self.witch_base.save_strategy
        self.poison_strategy = self.witch_base.poison_strategy
        
        # 初始化女巫工具
        self.witch_tools = WitchTools(self)
        
        self.logger = logging.getLogger(f"WitchAgent_{player_id}")
    
    def register_tools(self) -> None:
        """注册女巫特定的工具函数"""
        try:
            # 获取女巫工具集
            tools = self.witch_tools.get_tools()
            
            # 添加工具到Agent
            for tool in tools:
                self.add_tool(tool)
            
            self.logger.info(f"女巫Agent {self.player_id} 注册了 {len(tools)} 个工具")
            
        except Exception as e:
            self.logger.error(f"注册女巫工具失败: {e}")
    
    async def night_action(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """女巫夜晚行动 - 使用Agent进行智能决策"""
        try:
            self.last_night_death = death_info
            
            # 如果没有任何药剂，无法行动
            if not self.has_antidote and not self.has_poison:
                return {
                    "action": "no_action",
                    "success": True,
                    "message": f"女巫{self.player_id}没有可用的药剂"
                }
            
            # 构建决策上下文
            context = {
                "game_state": game_state,
                "death_info": death_info,
                "potion_status": self._format_potion_status(),
                "suspicions": self.format_suspicions(),
                "role": "witch",
                "player_id": self.player_id
            }
            
            # 使用Agent进行决策
            decision_result = await self.execute_decision_chain(context)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": decision_result.get("action", "unknown"),
                "target": decision_result.get("target_id"),
                "player_id": self.player_id,
                "reason": decision_result.get("message", ""),
                "timestamp": datetime.now().isoformat()
            })
            
            return decision_result
            
        except Exception as e:
            self.logger.error(f"女巫Agent夜晚行动失败: {e}")
            # 回退到基础女巫逻辑
            return await self.witch_base.night_action(game_state, death_info)
    
    def update_state(self, action_result: Dict[str, Any]):
        """更新女巫Agent状态"""
        try:
            action = action_result.get("action")
            
            if action == "use_antidote":
                # 更新解药状态
                self.has_antidote = False
                target_id = action_result.get("target_id")
                if target_id and target_id not in self.saved_players:
                    self.saved_players.append(target_id)
                    
            elif action == "use_poison":
                # 更新毒药状态
                self.has_poison = False
                target_id = action_result.get("target_id")
                if target_id and target_id not in self.poisoned_players:
                    self.poisoned_players.append(target_id)
            
            # 同步到基础女巫实例
            self.witch_base.has_antidote = self.has_antidote
            self.witch_base.has_poison = self.has_poison
            self.witch_base.saved_players = self.saved_players
            self.witch_base.poisoned_players = self.poisoned_players
            
        except Exception as e:
            self.logger.error(f"更新女巫状态失败: {e}")
    
    def _format_potion_status(self) -> str:
        """格式化药剂状态"""
        status = []
        if self.has_antidote:
            status.append("🌿 解药: ✅ 可用")
        else:
            status.append("🌿 解药: ❌ 已使用")
        
        if self.has_poison:
            status.append("🧪 毒药: ✅ 可用")
        else:
            status.append("🧪 毒药: ❌ 已使用")
        
        return "\n".join(status)
    
    # 继承基础女巫的其他方法
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """女巫发言 - 使用基础女巫逻辑"""
        return await self.witch_base.make_speech(game_state)
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """女巫投票 - 使用基础女巫逻辑"""
        return await self.witch_base.vote(game_state, candidates)
    
    def should_save_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该救某个玩家"""
        return self.witch_base.should_save_player(target_id, game_state)
    
    def should_poison_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该毒某个玩家"""
        return self.witch_base.should_poison_player(target_id, game_state)
    
    def get_recommended_poison_target(self, game_state: Dict[str, Any]) -> Optional[int]:
        """获取推荐的毒杀目标"""
        return self.witch_base.get_recommended_poison_target(game_state)
    
    def analyze_night_deaths(self, deaths: List[Dict[str, Any]]):
        """分析夜晚死亡情况"""
        self.witch_base.analyze_night_deaths(deaths)
    
    def get_strategy_hint(self) -> str:
        """获取女巫策略提示"""
        return self.witch_base.get_strategy_hint() 