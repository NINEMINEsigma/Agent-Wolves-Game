"""
狼人工具函数集
定义狼人角色的所有工具函数
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.tools import FunctionTool

from ...ai_agent import BaseAIAgent


class WerewolfTools:
    """狼人工具函数集合"""
    
    def __init__(self, werewolf_agent: BaseAIAgent):
        self.werewolf = werewolf_agent
        self.logger = logging.getLogger(f"WerewolfTools_{werewolf_agent.player_id}")
    
    def get_tools(self) -> List[FunctionTool]:
        """获取所有狼人工具"""
        return [
            FunctionTool.from_defaults(
                fn=self.coordinate_with_teammates,
                name="coordinate_with_teammates",
                description="与狼人同伴协调行动"
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_threat_level,
                name="analyze_threat_level",
                description="分析当前威胁等级"
            ),
            FunctionTool.from_defaults(
                fn=self.select_kill_target,
                name="select_kill_target",
                description="选择击杀目标"
            ),
            FunctionTool.from_defaults(
                fn=self.kill_player,
                name="kill_player",
                description="击杀指定玩家"
            )
        ]
    
    def coordinate_with_teammates(self, teammates: List[int], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """与狼人同伴协调行动"""
        try:
            if not teammates:
                return {
                    "action": "coordinate",
                    "success": False,
                    "message": "没有同伴可协调"
                }
            
            # 分析同伴状态
            alive_teammates = [t for t in teammates if t in [p["id"] for p in game_state.get("alive_players", [])]]
            
            if not alive_teammates:
                return {
                    "action": "coordinate",
                    "success": False,
                    "message": "所有同伴都已死亡"
                }
            
            # 简单的协调逻辑
            coordination_result = {
                "action": "coordinate",
                "success": True,
                "alive_teammates": alive_teammates,
                "strategy": "individual_action",  # 或 "coordinated_action"
                "message": f"与{len(alive_teammates)}个同伴协调完成"
            }
            
            return coordination_result
            
        except Exception as e:
            self.logger.error(f"与同伴协调失败: {e}")
            return {
                "action": "coordinate",
                "success": False,
                "message": f"协调失败: {e}"
            }
    
    def analyze_threat_level(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前威胁等级"""
        try:
            # 分析存活的好人数量
            alive_players = game_state.get("alive_players", [])
            alive_good_players = [p for p in alive_players if p["id"] != self.werewolf.player_id 
                                and p["id"] not in getattr(self.werewolf, 'teammates', [])]
            
            # 分析威胁等级
            if len(alive_good_players) <= 2:
                threat_level = "low"
                strategy = "aggressive"
            elif len(alive_good_players) <= 4:
                threat_level = "medium"
                strategy = "balanced"
            else:
                threat_level = "high"
                strategy = "conservative"
            
            return {
                "action": "analyze_threat",
                "success": True,
                "threat_level": threat_level,
                "strategy": strategy,
                "alive_good_players": len(alive_good_players),
                "message": f"威胁等级: {threat_level}, 建议策略: {strategy}"
            }
            
        except Exception as e:
            self.logger.error(f"分析威胁等级失败: {e}")
            return {
                "action": "analyze_threat",
                "success": False,
                "message": f"分析失败: {e}"
            }
    
    def select_kill_target(self, candidates: List[int], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """选择击杀目标"""
        try:
            if not candidates:
                return {
                    "action": "select_kill_target",
                    "success": False,
                    "message": "没有可击杀的目标"
                }
            
            # 排除自己和同伴
            valid_targets = [c for c in candidates 
                           if c != self.werewolf.player_id 
                           and c not in getattr(self.werewolf, 'teammates', [])]
            
            if not valid_targets:
                return {
                    "action": "select_kill_target",
                    "success": False,
                    "message": "没有有效的击杀目标"
                }
            
            # 选择策略：优先击杀威胁大的玩家
            # 这里可以添加更复杂的逻辑
            selected_target = valid_targets[0]
            
            return {
                "action": "select_kill_target",
                "success": True,
                "target_id": selected_target,
                "candidates": valid_targets,
                "reason": f"选择玩家{selected_target}作为击杀目标",
                "message": f"推荐击杀目标: 玩家{selected_target}"
            }
            
        except Exception as e:
            self.logger.error(f"选择击杀目标失败: {e}")
            return {
                "action": "select_kill_target",
                "success": False,
                "message": f"选择失败: {e}"
            }
    
    def kill_player(self, target_id: int) -> Dict[str, Any]:
        """击杀指定玩家"""
        try:
            self.logger.info(f"狼人{self.werewolf.player_id}选择击杀玩家{target_id}")
            
            return {
                "action": "kill",
                "success": True,
                "target_id": target_id,
                "message": f"选择击杀玩家{target_id}",
                "final_decision": True
            }
            
        except Exception as e:
            self.logger.error(f"击杀玩家失败: {e}")
            return {
                "action": "kill",
                "success": False,
                "message": f"击杀失败: {e}"
            } 