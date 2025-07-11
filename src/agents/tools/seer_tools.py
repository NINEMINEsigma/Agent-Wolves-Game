"""
预言家工具函数集
定义预言家角色的所有工具函数
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.tools import FunctionTool

from ...ai_agent import BaseAIAgent


class SeerTools:
    """预言家工具函数集合"""
    
    def __init__(self, seer_agent: BaseAIAgent):
        self.seer = seer_agent
        self.logger = logging.getLogger(f"SeerTools_{seer_agent.player_id}")
    
    def get_tools(self) -> List[FunctionTool]:
        """获取所有预言家工具"""
        return [
            FunctionTool.from_defaults(
                fn=self.analyze_suspicious_players,
                name="analyze_suspicious_players",
                description="分析可疑玩家，选择查验目标"
            ),
            FunctionTool.from_defaults(
                fn=self.evaluate_divine_target,
                name="evaluate_divine_target",
                description="评估是否应该查验某个玩家"
            ),
            FunctionTool.from_defaults(
                fn=self.divine_player,
                name="divine_player",
                description="查验指定玩家的身份"
            )
        ]
    
    def analyze_suspicious_players(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """分析可疑玩家"""
        try:
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.seer.player_id]
            
            # 排除已经查验过的玩家
            unverified_players = [p for p in alive_players 
                                if p not in getattr(self.seer, 'vision_results', {})]
            
            if not unverified_players:
                return {
                    "action": "analyze_suspicious",
                    "success": False,
                    "message": "所有存活玩家都已查验过"
                }
            
            # 获取最可疑的玩家
            most_suspicious = self.seer.get_most_suspicious_players(3)
            recommended_targets = []
            
            for suspect in most_suspicious:
                if suspect in unverified_players:
                    recommended_targets.append(suspect)
            
            if not recommended_targets:
                recommended_targets = unverified_players[:3]
            
            return {
                "action": "analyze_suspicious",
                "success": True,
                "unverified_players": unverified_players,
                "recommended_targets": recommended_targets,
                "message": f"推荐查验目标: {recommended_targets}"
            }
            
        except Exception as e:
            self.logger.error(f"分析可疑玩家失败: {e}")
            return {
                "action": "analyze_suspicious",
                "success": False,
                "message": f"分析失败: {e}"
            }
    
    def evaluate_divine_target(self, target_id: int, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """评估是否应该查验某个玩家"""
        try:
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.seer.player_id]
            
            if target_id not in alive_players:
                return {
                    "action": "evaluate_divine",
                    "success": False,
                    "message": "目标玩家不存在或已死亡"
                }
            
            if target_id in getattr(self.seer, 'vision_results', {}):
                return {
                    "action": "evaluate_divine",
                    "success": False,
                    "message": "该玩家已经查验过"
                }
            
            # 评估查验价值
            suspicion_level = self.seer.suspicions.get(target_id, 0.0)
            
            if suspicion_level > 0.5:
                recommendation = "high_priority"
                reason = f"玩家{target_id}高度可疑，建议优先查验"
            elif suspicion_level > 0.2:
                recommendation = "medium_priority"
                reason = f"玩家{target_id}有一定可疑度，值得查验"
            else:
                recommendation = "low_priority"
                reason = f"玩家{target_id}可疑度较低，但仍有查验价值"
            
            return {
                "action": "evaluate_divine",
                "success": True,
                "target_id": target_id,
                "recommendation": recommendation,
                "reason": reason,
                "suspicion_level": suspicion_level
            }
            
        except Exception as e:
            self.logger.error(f"评估查验目标失败: {e}")
            return {
                "action": "evaluate_divine",
                "success": False,
                "message": f"评估失败: {e}"
            }
    
    def divine_player(self, target_id: int) -> Dict[str, Any]:
        """查验指定玩家的身份"""
        try:
            # 这里只是返回决策结果，实际的查验结果由游戏引擎处理
            self.logger.info(f"预言家{self.seer.player_id}选择查验玩家{target_id}")
            
            return {
                "action": "divine",
                "success": True,
                "target_id": target_id,
                "message": f"选择查验玩家{target_id}",
                "final_decision": True
            }
            
        except Exception as e:
            self.logger.error(f"查验玩家失败: {e}")
            return {
                "action": "divine",
                "success": False,
                "message": f"查验失败: {e}"
            } 