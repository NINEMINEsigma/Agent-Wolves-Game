"""
通用工具函数集
定义所有角色都可以使用的通用工具函数
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.tools import FunctionTool

from ...ai_agent import BaseAIAgent


class CommonTools:
    """通用工具函数集合"""
    
    def __init__(self, agent: BaseAIAgent):
        self.agent = agent
        self.logger = logging.getLogger(f"CommonTools_{agent.player_id}")
    
    def get_tools(self) -> List[FunctionTool]:
        """获取所有通用工具"""
        return [
            FunctionTool.from_defaults(
                fn=self.analyze_game_situation,
                name="analyze_game_situation",
                description="分析当前游戏局势"
            ),
            FunctionTool.from_defaults(
                fn=self.get_player_info,
                name="get_player_info",
                description="获取玩家信息"
            ),
            FunctionTool.from_defaults(
                fn=self.update_suspicion,
                name="update_suspicion",
                description="更新对某个玩家的怀疑度"
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_speech_patterns,
                name="analyze_speech_patterns",
                description="分析发言模式"
            ),
            FunctionTool.from_defaults(
                fn=self.evaluate_voting_strategy,
                name="evaluate_voting_strategy",
                description="评估投票策略"
            ),
            FunctionTool.from_defaults(
                fn=self.get_memory_summary,
                name="get_memory_summary",
                description="获取记忆摘要"
            ),
            FunctionTool.from_defaults(
                fn=self.analyze_behavior_consistency,
                name="analyze_behavior_consistency",
                description="分析行为一致性"
            )
        ]
    
    def analyze_game_situation(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """分析当前游戏局势"""
        try:
            alive_players = game_state.get("alive_players", [])
            dead_players = game_state.get("dead_players", [])
            current_round = game_state.get("current_round", 1)
            
            # 基础分析
            analysis = {
                "action": "analyze_situation",
                "success": True,
                "alive_count": len(alive_players),
                "dead_count": len(dead_players),
                "current_round": current_round,
                "game_phase": "early" if current_round <= 2 else "mid" if current_round <= 4 else "late"
            }
            
            # 根据角色进行特定分析
            if self.agent.role == "witch":
                analysis["potion_status"] = {
                    "has_antidote": getattr(self.agent, 'has_antidote', True),
                    "has_poison": getattr(self.agent, 'has_poison', True)
                }
            elif self.agent.role == "seer":
                vision_results = getattr(self.agent, 'vision_results', {})
                analysis["vision_count"] = len(vision_results)
                analysis["known_werewolves"] = [p for p, role in vision_results.items() if role == "werewolf"]
                analysis["known_villagers"] = [p for p, role in vision_results.items() if role == "villager"]
            
            return analysis
            
        except Exception as e:
            self.logger.error(f"分析游戏局势失败: {e}")
            return {
                "action": "analyze_situation",
                "success": False,
                "message": f"分析失败: {e}"
            }
    
    def get_player_info(self, player_id: int, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """获取玩家信息"""
        try:
            alive_players = game_state.get("alive_players", [])
            dead_players = game_state.get("dead_players", [])
            
            # 查找玩家
            player = None
            for p in alive_players + dead_players:
                if p["id"] == player_id:
                    player = p
                    break
            
            if not player:
                return {
                    "action": "get_player_info",
                    "success": False,
                    "message": f"玩家{player_id}不存在"
                }
            
            # 获取怀疑度
            suspicion = self.agent.suspicions.get(player_id, 0.0)
            
            return {
                "action": "get_player_info",
                "success": True,
                "player_id": player_id,
                "player_name": player.get("name", ""),
                "is_alive": player_id in [p["id"] for p in alive_players],
                "suspicion_level": suspicion,
                "suspicion_description": self._get_suspicion_description(suspicion)
            }
            
        except Exception as e:
            self.logger.error(f"获取玩家信息失败: {e}")
            return {
                "action": "get_player_info",
                "success": False,
                "message": f"获取失败: {e}"
            }
    
    def update_suspicion(self, target_id: int, suspicion_change: float, reason: str) -> Dict[str, Any]:
        """更新对某个玩家的怀疑度"""
        try:
            if target_id == self.agent.player_id:
                return {
                    "action": "update_suspicion",
                    "success": False,
                    "message": "不能更新对自己的怀疑度"
                }
            
            # 更新怀疑度
            self.agent.update_suspicion(target_id, suspicion_change, reason)
            
            new_suspicion = self.agent.suspicions.get(target_id, 0.0)
            
            return {
                "action": "update_suspicion",
                "success": True,
                "target_id": target_id,
                "suspicion_change": suspicion_change,
                "new_suspicion": new_suspicion,
                "reason": reason,
                "message": f"更新玩家{target_id}怀疑度: {suspicion_change:+.2f}, 新值: {new_suspicion:.2f}"
            }
            
        except Exception as e:
            self.logger.error(f"更新怀疑度失败: {e}")
            return {
                "action": "update_suspicion",
                "success": False,
                "message": f"更新失败: {e}"
            }
    
    def _get_suspicion_description(self, suspicion: float) -> str:
        """获取怀疑度描述"""
        if suspicion >= 0.7:
            return "高度可疑"
        elif suspicion >= 0.3:
            return "较为可疑"
        elif suspicion >= -0.1:
            return "中性"
        elif suspicion >= -0.5:
            return "较为可信"
        else:
            return "高度可信"
    
    def analyze_speech_patterns(self, target_id: int) -> Dict[str, Any]:
        """分析发言模式"""
        try:
            speeches = self.agent.game_memory.get("speeches", [])
            target_speeches = [s for s in speeches if s.get("speaker_id") == target_id]
            
            if not target_speeches:
                return {
                    "action": "analyze_speech",
                    "success": False,
                    "message": f"玩家{target_id}没有发言记录"
                }
            
            # 分析发言特征
            speech_count = len(target_speeches)
            avg_length = sum(len(s.get("content", "")) for s in target_speeches) / speech_count
            
            # 分析情感词汇
            positive_words = ['相信', '信任', '无辜', '可靠', '真实', '支持']
            negative_words = ['怀疑', '可疑', '狡猾', '撒谎', '奇怪', '反对']
            
            positive_count = sum(1 for s in target_speeches 
                               for word in positive_words if word in s.get("content", ""))
            negative_count = sum(1 for s in target_speeches 
                               for word in negative_words if word in s.get("content", ""))
            
            return {
                "action": "analyze_speech",
                "success": True,
                "target_id": target_id,
                "speech_count": speech_count,
                "avg_length": avg_length,
                "positive_words": positive_count,
                "negative_words": negative_count,
                "sentiment": "positive" if positive_count > negative_count else "negative" if negative_count > positive_count else "neutral"
            }
            
        except Exception as e:
            self.logger.error(f"分析发言模式失败: {e}")
            return {
                "action": "analyze_speech",
                "success": False,
                "message": f"分析失败: {e}"
            }
    
    def evaluate_voting_strategy(self, candidates: List[int]) -> Dict[str, Any]:
        """评估投票策略"""
        try:
            if not candidates:
                return {
                    "action": "evaluate_voting",
                    "success": False,
                    "message": "没有可投票的候选人"
                }
            
            # 分析每个候选人的怀疑度
            candidate_analysis = []
            for candidate_id in candidates:
                if candidate_id == self.agent.player_id:
                    continue
                
                suspicion = self.agent.suspicions.get(candidate_id, 0.0)
                candidate_analysis.append({
                    "player_id": candidate_id,
                    "suspicion": suspicion,
                    "recommendation": "vote" if suspicion > 0.3 else "avoid" if suspicion < -0.3 else "neutral"
                })
            
            # 排序并推荐
            candidate_analysis.sort(key=lambda x: x["suspicion"], reverse=True)
            recommended_target = candidate_analysis[0]["player_id"] if candidate_analysis else None
            
            return {
                "action": "evaluate_voting",
                "success": True,
                "candidates": candidate_analysis,
                "recommended_target": recommended_target,
                "strategy": "vote_most_suspicious"
            }
            
        except Exception as e:
            self.logger.error(f"评估投票策略失败: {e}")
            return {
                "action": "evaluate_voting",
                "success": False,
                "message": f"评估失败: {e}"
            }
    
    def get_memory_summary(self, memory_type: str = "all", limit: int = 5) -> Dict[str, Any]:
        """获取记忆摘要"""
        try:
            if memory_type == "all":
                memories = []
                for mem_type, mem_list in self.agent.game_memory.items():
                    if isinstance(mem_list, list):
                        memories.extend(mem_list[-limit:])
            else:
                memories = self.agent.game_memory.get(memory_type, [])
                if isinstance(memories, list):
                    memories = memories[-limit:]
                else:
                    memories = []
            
            # 格式化记忆
            formatted_memories = []
            for memory in memories:
                if isinstance(memory, dict):
                    formatted_memories.append({
                        "type": memory.get("type", "unknown"),
                        "content": str(memory)[:100] + "..." if len(str(memory)) > 100 else str(memory),
                        "timestamp": memory.get("timestamp", "unknown")
                    })
            
            return {
                "action": "get_memory_summary",
                "success": True,
                "memory_type": memory_type,
                "count": len(formatted_memories),
                "memories": formatted_memories
            }
            
        except Exception as e:
            self.logger.error(f"获取记忆摘要失败: {e}")
            return {
                "action": "get_memory_summary",
                "success": False,
                "message": f"获取失败: {e}"
            }
    
    def analyze_behavior_consistency(self, target_id: int) -> Dict[str, Any]:
        """分析行为一致性"""
        try:
            # 分析投票一致性
            votes = self.agent.game_memory.get("votes", [])
            target_votes = [v for v in votes if v.get("voter_id") == target_id]
            
            # 分析发言一致性
            speeches = self.agent.game_memory.get("speeches", [])
            target_speeches = [s for s in speeches if s.get("speaker_id") == target_id]
            
            # 计算一致性指标
            vote_consistency = self._calculate_vote_consistency(target_votes)
            speech_consistency = self._calculate_speech_consistency(target_speeches)
            
            return {
                "action": "analyze_behavior_consistency",
                "success": True,
                "target_id": target_id,
                "vote_consistency": vote_consistency,
                "speech_consistency": speech_consistency,
                "overall_consistency": (vote_consistency + speech_consistency) / 2,
                "behavior_assessment": self._assess_behavior_consistency(vote_consistency, speech_consistency)
            }
            
        except Exception as e:
            self.logger.error(f"分析行为一致性失败: {e}")
            return {
                "action": "analyze_behavior_consistency",
                "success": False,
                "message": f"分析失败: {e}"
            }
    
    def _calculate_vote_consistency(self, votes: List[Dict[str, Any]]) -> float:
        """计算投票一致性"""
        if len(votes) < 2:
            return 0.5  # 默认中等一致性
        
        # 分析投票目标的一致性
        vote_targets = [v.get("target_id") for v in votes if v.get("target_id")]
        if len(set(vote_targets)) == 1:
            return 1.0  # 完全一致
        elif len(set(vote_targets)) == len(vote_targets):
            return 0.0  # 完全不一致
        
        return 0.5  # 中等一致性
    
    def _calculate_speech_consistency(self, speeches: List[Dict[str, Any]]) -> float:
        """计算发言一致性"""
        if len(speeches) < 2:
            return 0.5  # 默认中等一致性
        
        # 分析发言内容的一致性（简化版本）
        contents = [s.get("content", "") for s in speeches]
        avg_length = sum(len(c) for c in contents) / len(contents)
        length_variance = sum((len(c) - avg_length) ** 2 for c in contents) / len(contents)
        
        # 长度一致性（方差越小越一致）
        consistency = max(0, 1 - length_variance / (avg_length ** 2))
        return consistency
    
    def _assess_behavior_consistency(self, vote_consistency: float, speech_consistency: float) -> str:
        """评估行为一致性"""
        overall = (vote_consistency + speech_consistency) / 2
        
        if overall >= 0.8:
            return "高度一致"
        elif overall >= 0.6:
            return "较为一致"
        elif overall >= 0.4:
            return "中等一致"
        elif overall >= 0.2:
            return "较为不一致"
        else:
            return "高度不一致" 