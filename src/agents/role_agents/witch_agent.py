"""
女巫Agent实现
使用LlamaIndex Agent工具调用架构进行智能药剂决策
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool

from ..base_agent import BaseGameAgent
from ..tools.witch_tools import WitchTools


class WitchAgent(BaseGameAgent):
    """女巫Agent类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], 
                 identity_system=None, memory_config=None):
        super().__init__(player_id, name, "witch", llm_interface, prompts, identity_system, memory_config)
        
        # 女巫特有属性
        self.has_antidote = True
        self.has_poison = True
        self.saved_players = []
        self.poisoned_players = []
        self.last_night_death = None
        self.save_strategy = "conservative"  # conservative, aggressive, balanced
        self.poison_strategy = "conservative"  # conservative, aggressive, balanced
        
        # 初始化工具函数
        self.witch_tools = WitchTools(self)
        
        # 在工具实例化完成后初始化Agent
        self.initialize_agent()
        
        self.logger.info(f"女巫Agent {player_id} 初始化完成")
    
    def register_tools(self) -> None:
        """注册女巫工具函数"""
        try:
            tools = self.witch_tools.get_tools()
            for tool in tools:
                self.add_tool(tool)
            self.logger.info(f"女巫{self.player_id}工具注册完成")
        except Exception as e:
            self.logger.error(f"注册女巫工具失败: {e}")
    
    def _create_agent_runner(self) -> Optional[AgentRunner]:
        """创建女巫Agent Runner"""
        try:
            # 使用父类的默认实现
            return super()._create_agent_runner()
            
        except Exception as e:
            self.logger.error(f"创建女巫Agent Runner失败: {e}")
            return None
    
    async def night_action(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """女巫夜晚药剂行动（Agent模式）"""
        try:
            self.last_night_death = death_info
            
            # 如果没有任何药剂，无法行动
            if not self.has_antidote and not self.has_poison:
                return {
                    "action": "no_action",
                    "success": True,
                    "message": f"女巫{self.player_id}没有可用的药剂"
                }
            
            if not self.agent_runner:
                self.logger.warning("Agent Runner未初始化，使用基础决策")
                return await self._basic_night_action(game_state, death_info)
            
            # 构建Agent提示
            agent_prompt = self._build_witch_agent_prompt(game_state, death_info)
            
            # 使用Agent进行决策（暂时使用传统方式）
            response = await self.llm_interface.generate_response(agent_prompt)
            
            # 解析Agent响应
            action_result = self._parse_agent_response(response, game_state, death_info)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": action_result.get("action", "unknown"),
                "target": action_result.get("target_id"),
                "player_id": self.player_id,
                "agent_response": str(response),
                "mode": "agent"
            })
            
            return action_result
            
        except Exception as e:
            self.logger.error(f"女巫Agent夜晚行动失败: {e}")
            # 回退到基础决策
            return await self._basic_night_action(game_state, death_info)
    
    def _build_witch_agent_prompt(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> str:
        """构建女巫Agent提示"""
        game_context = self.llm_interface.format_game_context(game_state)
        potion_status = self._format_potion_status()
        suspicion_info = self.format_suspicions()
        
        death_context = ""
        if death_info:
            death_context = f"""
            今晚死亡信息：
            - 死亡玩家：{death_info.get('player_id', 'unknown')}
            - 死亡原因：{death_info.get('reason', 'unknown')}
            """
        
        prompt = f"""
        你是女巫，现在是夜晚药剂使用时间。
        
        当前游戏情况：
        {game_context}
        
        你的药剂状态：
        {potion_status}
        
        {death_context}
        
        你的怀疑情况：
        {suspicion_info}
        
        你的任务：
        1. 分析今晚的死亡情况
        2. 评估是否需要使用解药救人
        3. 评估是否需要使用毒药杀人
        4. 执行药剂使用决策
        
        请使用提供的工具函数来完成药剂使用决策。谨慎使用药剂，每瓶药剂只能使用一次。
        """
        
        return prompt
    
    def _parse_agent_response(self, response, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """解析Agent响应"""
        try:
            # 从Agent响应中提取决策信息
            response_text = str(response)
            
            # 查找最终决策
            if "final_decision" in response_text and "action" in response_text:
                # 尝试提取行动类型和目标ID
                import re
                
                # 检查是否使用解药
                if "use_antidote" in response_text.lower() or "救人" in response_text:
                    target_matches = re.findall(r'target_id["\']?\s*:\s*(\d+)', response_text)
                    target_id = int(target_matches[0]) if target_matches else None
                    
                    if target_id and self.has_antidote:
                        return {
                            "action": "use_antidote",
                            "target_id": target_id,
                            "success": True,
                            "message": f"女巫Agent选择使用解药救玩家{target_id}",
                            "agent_mode": True
                        }
                
                # 检查是否使用毒药
                elif "use_poison" in response_text.lower() or "毒人" in response_text:
                    target_matches = re.findall(r'target_id["\']?\s*:\s*(\d+)', response_text)
                    target_id = int(target_matches[0]) if target_matches else None
                    
                    if target_id and self.has_poison:
                        return {
                            "action": "use_poison",
                            "target_id": target_id,
                            "success": True,
                            "message": f"女巫Agent选择使用毒药杀玩家{target_id}",
                            "agent_mode": True
                        }
            
            # 如果无法解析，返回默认决策
            return self._get_default_potion_decision(game_state, death_info)
            
        except Exception as e:
            self.logger.error(f"解析Agent响应失败: {e}")
            return self._get_default_potion_decision(game_state, death_info)
    
    def _get_default_potion_decision(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """获取默认药剂使用决策"""
        try:
            # 如果有死亡信息且还有解药，考虑救人
            if death_info and self.has_antidote:
                dead_player_id = death_info.get("player_id")
                if dead_player_id and dead_player_id not in self.saved_players:
                    # 基于策略决定是否救人
                    if self.should_save_player(dead_player_id, game_state):
                        return {
                            "action": "use_antidote",
                            "target_id": dead_player_id,
                            "success": True,
                            "message": f"女巫默认选择使用解药救玩家{dead_player_id}"
                        }
            
            # 如果有毒药，考虑毒人
            if self.has_poison:
                poison_target = self.get_recommended_poison_target(game_state)
                if poison_target and self.should_poison_player(poison_target, game_state):
                    return {
                        "action": "use_poison",
                        "target_id": poison_target,
                        "success": True,
                        "message": f"女巫默认选择使用毒药杀玩家{poison_target}"
                    }
            
            # 不使用药剂
            return {
                "action": "no_action",
                "success": True,
                "message": "女巫选择不使用药剂"
            }
            
        except Exception as e:
            self.logger.error(f"获取默认药剂决策失败: {e}")
            return {
                "action": "no_action",
                "success": False,
                "message": "药剂决策失败"
            }
    
    async def _basic_night_action(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """基础夜晚行动（备用方案）"""
        try:
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
            self.logger.error(f"基础夜晚行动失败: {e}")
            return {
                "action": "no_action",
                "success": False,
                "message": f"女巫夜晚行动失败: {e}"
            }
    
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
    
    # 女巫特有方法实现
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """女巫发言 - 使用Agent智能决策"""
        try:
            context = {
                "game_state": game_state,
                "role": "witch",
                "player_id": self.player_id,
                "potion_status": self._format_potion_status()
            }
            
            speech_result = await self.execute_decision_chain(context)
            return speech_result.get("speech", f"我是玩家{self.player_id}，我是好人")
            
        except Exception as e:
            self.logger.error(f"女巫发言失败: {e}")
            return f"我是玩家{self.player_id}，我是好人"
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """女巫投票 - 使用Agent智能决策"""
        try:
            context = {
                "game_state": game_state,
                "candidates": candidates,
                "role": "witch",
                "player_id": self.player_id
            }
            
            vote_result = await self.execute_decision_chain(context)
            return vote_result.get("target_id", candidates[0] if candidates else 0)
            
        except Exception as e:
            self.logger.error(f"女巫投票失败: {e}")
            return candidates[0] if candidates else 0
    
    def should_save_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该救某个玩家"""
        try:
            # 如果没有解药，无法救人
            if not self.has_antidote:
                return False
            
            # 如果已经救过这个玩家，不能再救
            if target_id in self.saved_players:
                return False
            
            # 基于策略判断
            if self.save_strategy == "conservative":
                # 保守策略：只救自己或明显的好人
                return target_id == self.player_id
            elif self.save_strategy == "aggressive":
                # 激进策略：救任何可能的好人
                return True
            else:  # balanced
                # 平衡策略：救自己或信任的玩家
                return target_id == self.player_id or self.is_trusted_player(target_id)
                
        except Exception as e:
            self.logger.error(f"判断是否救人失败: {e}")
            return False
    
    def should_poison_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该毒某个玩家"""
        try:
            # 如果没有毒药，无法毒人
            if not self.has_poison:
                return False
            
            # 如果已经毒过这个玩家，不能再毒
            if target_id in self.poisoned_players:
                return False
            
            # 基于策略判断
            if self.poison_strategy == "conservative":
                # 保守策略：不轻易使用毒药
                return False
            elif self.poison_strategy == "aggressive":
                # 激进策略：毒杀可疑玩家
                return self.is_suspicious_player(target_id)
            else:  # balanced
                # 平衡策略：毒杀高度可疑的玩家
                return self.is_highly_suspicious_player(target_id)
                
        except Exception as e:
            self.logger.error(f"判断是否毒人失败: {e}")
            return False
    
    def get_recommended_poison_target(self, game_state: Dict[str, Any]) -> Optional[int]:
        """获取推荐的毒杀目标"""
        try:
            alive_players = [p for p in game_state.get("players", []) if p.get("is_alive", True)]
            
            # 找出最可疑的玩家
            most_suspicious = None
            highest_suspicion = 0
            
            for player in alive_players:
                if player["id"] == self.player_id:
                    continue  # 不毒自己
                
                suspicion_level = self.get_suspicion_level(player["id"])
                if suspicion_level > highest_suspicion:
                    highest_suspicion = suspicion_level
                    most_suspicious = player["id"]
            
            return most_suspicious
            
        except Exception as e:
            self.logger.error(f"获取毒杀目标失败: {e}")
            return None
    
    def analyze_night_deaths(self, deaths: List[Dict[str, Any]]):
        """分析夜晚死亡情况"""
        try:
            for death in deaths:
                player_id = death.get("player_id")
                death_type = death.get("type", "unknown")
                
                if death_type == "werewolf_kill":
                    # 狼人击杀，记录信息
                    self.update_memory("night_deaths", {
                        "player_id": player_id,
                        "type": death_type,
                        "timestamp": datetime.now().isoformat()
                    })
                elif death_type == "witch_poison":
                    # 女巫毒杀，记录信息
                    self.update_memory("night_deaths", {
                        "player_id": player_id,
                        "type": death_type,
                        "timestamp": datetime.now().isoformat()
                    })
                    
        except Exception as e:
            self.logger.error(f"分析夜晚死亡失败: {e}")
    
    def get_strategy_hint(self) -> str:
        """获取女巫策略提示"""
        hints = []
        
        if self.has_antidote:
            hints.append("🌿 解药可用，谨慎使用")
        else:
            hints.append("🌿 解药已用")
        
        if self.has_poison:
            hints.append("🧪 毒药可用，谨慎使用")
        else:
            hints.append("🧪 毒药已用")
        
        hints.append(f"💡 救人策略: {self.save_strategy}")
        hints.append(f"💡 毒人策略: {self.poison_strategy}")
        
        return "\n".join(hints)
    
    def is_trusted_player(self, player_id: int) -> bool:
        """判断是否为信任的玩家"""
        # 简化实现：基于基础信任度判断
        # 在实际游戏中，这应该基于更复杂的记忆分析
        return player_id != self.player_id  # 暂时信任除自己外的所有玩家
    
    def is_suspicious_player(self, player_id: int) -> bool:
        """判断是否为可疑玩家"""
        suspicion_level = self.get_suspicion_level(player_id)
        return suspicion_level > 0.5
    
    def is_highly_suspicious_player(self, player_id: int) -> bool:
        """判断是否为高度可疑玩家"""
        suspicion_level = self.get_suspicion_level(player_id)
        return suspicion_level > 0.8
    
    def get_suspicion_level(self, player_id: int) -> float:
        """获取玩家可疑度"""
        # 简化实现：基于基础可疑度计算
        # 在实际游戏中，这应该基于记忆中的行为分析
        if player_id == self.player_id:
            return 0.0  # 自己不可疑
        
        # 随机生成可疑度（在实际实现中应该基于记忆分析）
        import random
        return random.uniform(0.0, 1.0) 