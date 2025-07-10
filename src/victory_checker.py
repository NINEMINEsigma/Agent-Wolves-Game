"""
胜利条件判定器
检测游戏结束条件并判定获胜方
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from .game_state import GameState


class VictoryChecker:
    """胜利条件判定器"""
    
    def __init__(self, game_state: GameState):
        """
        初始化胜利判定器
        
        Args:
            game_state: 游戏状态管理器
        """
        self.game_state = game_state
        self.logger = logging.getLogger(__name__)
        
        # 阵营定义
        self.villager_roles = ["villager", "seer", "witch"]
        self.werewolf_roles = ["werewolf"]
        self.neutral_roles = []  # 第三方角色（如果有）
    
    def check_victory_condition(self, game_state: GameState) -> Optional[str]:
        """
        检查胜利条件
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            获胜阵营名称或None（游戏继续）
        """
        is_game_over, winner = self.is_game_over(game_state)
        
        if is_game_over:
            self.logger.info(f"游戏结束，获胜方: {winner}")
            
            # 更新游戏状态
            game_state.game_winner = winner
            game_state.game_end_reason = self._get_victory_reason(winner or "unknown", game_state)
            
            # 记录游戏结束事件
            game_state.log_event({
                "event_type": "game_end",
                "winner": winner,
                "reason": game_state.game_end_reason,
                "final_counts": self.count_alive_by_faction(game_state),
                "total_rounds": game_state.current_round
            })
            
            return winner
        
        return None
    
    def count_alive_by_faction(self, game_state: GameState) -> Dict[str, int]:
        """
        统计各阵营存活人数
        
        Args:
            game_state: 游戏状态
            
        Returns:
            各阵营人数统计
        """
        villager_count = 0  # 只统计普通村民
        villager_faction_count = 0  # 统计整个村民阵营
        werewolf_count = 0
        neutral_count = 0
        total_alive = 0
        
        for player in game_state.alive_players:
            role = player.get("role", "")
            total_alive += 1
            
            if role == "villager":
                villager_count += 1
                villager_faction_count += 1
            elif role in ["seer", "witch"]:
                villager_faction_count += 1  # 特殊角色也属于村民阵营
            elif role in self.werewolf_roles:
                werewolf_count += 1
            elif role in self.neutral_roles:
                neutral_count += 1
            else:
                self.logger.warning(f"未知角色类型: {role}")
        
        return {
            "villagers": villager_count,  # 普通村民数量
            "villager_faction": villager_faction_count,  # 整个村民阵营数量
            "werewolves": werewolf_count,
            "neutral": neutral_count,
            "total_alive": total_alive
        }
    
    def is_game_over(self, game_state: GameState) -> Tuple[bool, Optional[str]]:
        """
        判断游戏是否结束
        
        Args:
            game_state: 游戏状态
            
        Returns:
            (是否结束, 获胜方)
        """
        faction_counts = self.count_alive_by_faction(game_state)
        
        villager_count = faction_counts["villagers"]  # 普通村民数量
        villager_faction_count = faction_counts["villager_faction"]  # 整个村民阵营数量
        werewolf_count = faction_counts["werewolves"]
        total_alive = faction_counts["total_alive"]
        
        # 检查狼人胜利条件：消灭所有村民（包括特殊角色）
        if villager_faction_count == 0 and werewolf_count > 0:
            return True, "werewolves"
        
        # 检查村民阵营胜利条件：消灭所有狼人
        if werewolf_count == 0 and villager_faction_count > 0:
            return True, "villagers"
        
        # 检查无人存活（平局，很少见）
        if total_alive == 0:
            return True, "draw"
        
        # 轮次限制已移除，游戏将持续到自然结束
        
        # 游戏继续
        return False, None
    
    def _get_victory_reason(self, winner: str, game_state: GameState) -> str:
        """
        获取胜利原因描述
        
        Args:
            winner: 获胜方
            game_state: 游戏状态
            
        Returns:
            胜利原因文本
        """
        faction_counts = self.count_alive_by_faction(game_state)
        
        if winner == "werewolves":
            if faction_counts["villager_faction"] == 0:
                return "狼人阵营胜利！消灭了所有村民"
        
        elif winner == "villagers":
            if faction_counts["werewolves"] == 0:
                return "村民阵营胜利！消灭了所有狼人"
        
        elif winner == "draw":
            if faction_counts["total_alive"] == 0:
                return "所有玩家都死亡，平局"
        
        return f"未知胜利原因（获胜方: {winner}）"
    
    def get_game_summary(self, game_state: GameState) -> Dict[str, Any]:
        """
        生成游戏总结
        
        Args:
            game_state: 游戏状态
            
        Returns:
            游戏总结信息
        """
        faction_counts = self.count_alive_by_faction(game_state)
        
        # 统计各角色最终状态
        role_summary = {}
        for player in game_state.players:
            role = player["role"]
            if role not in role_summary:
                role_summary[role] = {"total": 0, "alive": 0, "dead": 0}
            
            role_summary[role]["total"] += 1
            if player["is_alive"]:
                role_summary[role]["alive"] += 1
            else:
                role_summary[role]["dead"] += 1
        
        # 统计死亡原因
        death_causes = {}
        for player in game_state.dead_players:
            cause = player.get("death_cause", "unknown")
            death_causes[cause] = death_causes.get(cause, 0) + 1
        
        # 计算游戏时长
        game_duration = None
        if hasattr(game_state, 'game_start_time'):
            from datetime import datetime
            game_duration = (datetime.now() - game_state.game_start_time).total_seconds()
        
        return {
            "winner": game_state.game_winner,
            "victory_reason": game_state.game_end_reason,
            "total_rounds": game_state.current_round,
            "game_duration_seconds": game_duration,
            "final_faction_counts": faction_counts,
            "role_summary": role_summary,
            "death_causes": death_causes,
            "total_players": len(game_state.players),
            "total_events": len(game_state.game_history),
            "voting_rounds": len([e for e in game_state.game_history 
                                if e.get("event_type") == "vote_execution"])
        }
    
    def predict_victory_probability(self, game_state: GameState) -> Dict[str, float]:
        """
        预测各阵营胜利概率（简单算法）
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            各阵营胜利概率
        """
        faction_counts = self.count_alive_by_faction(game_state)
        
        villager_count = faction_counts["villagers"]  # 普通村民
        villager_faction_count = faction_counts["villager_faction"]  # 整个村民阵营
        werewolf_count = faction_counts["werewolves"]
        total_alive = faction_counts["total_alive"]
        
        # 如果游戏已结束
        if werewolf_count == 0:
            return {"villagers": 1.0, "werewolves": 0.0, "draw": 0.0}
        if villager_faction_count == 0:  # 村民阵营全死，狼人胜利
            return {"villagers": 0.0, "werewolves": 1.0, "draw": 0.0}
        
        # 简单概率计算（基于人数比例）
        if total_alive > 0:
            villager_faction_ratio = villager_faction_count / total_alive
            werewolf_ratio = werewolf_count / total_alive
            
            # 村民需要更大优势才能获胜（因为狼人有夜杀能力）
            # 但狼人只需要杀死普通村民就获胜，这给了狼人优势
            villager_advantage = max(0, villager_faction_ratio - 0.3)
            werewolf_advantage = werewolf_ratio + 0.3  # 增加狼人优势，因为胜利条件更容易
            
            total_advantage = villager_advantage + werewolf_advantage
            
            if total_advantage > 0:
                villager_prob = villager_advantage / total_advantage
                werewolf_prob = werewolf_advantage / total_advantage
            else:
                villager_prob = werewolf_prob = 0.5
            
            # 轮次限制已移除，游戏将持续到自然胜负
            
            # 归一化
            total_prob = villager_prob + werewolf_prob
            if total_prob > 0:
                villager_prob /= total_prob
                werewolf_prob /= total_prob
            
            draw_prob = max(0.0, 1.0 - villager_prob - werewolf_prob)
            
            return {
                "villagers": round(villager_prob, 3),
                "werewolves": round(werewolf_prob, 3),
                "draw": round(draw_prob, 3)
            }
        
        return {"villagers": 0.5, "werewolves": 0.5, "draw": 0.0}
    
    def get_critical_players(self, game_state: GameState) -> Dict[str, List[Dict[str, Any]]]:
        """
        识别关键玩家（对胜负影响重大的玩家）
        
        Args:
            game_state: 游戏状态
            
        Returns:
            关键玩家信息
        """
        critical_players = {
            "high_value_targets": [],  # 狼人的高价值目标
            "suspected_werewolves": [],  # 疑似狼人
            "confirmed_roles": []  # 已确认角色
        }
        
        # 识别高价值目标（特殊角色）
        for player in game_state.alive_players:
            if player["role"] in ["seer", "witch"]:
                critical_players["high_value_targets"].append({
                    "id": player["id"],
                    "name": player["name"],
                    "role": player["role"],
                    "threat_level": "high" if player["role"] == "seer" else "medium"
                })
        
        # 基于投票模式识别疑似狼人（简单算法）
        vote_patterns = self._analyze_voting_patterns(game_state)
        for player_id, suspicion_score in vote_patterns.items():
            if suspicion_score > 0.6:  # 高怀疑度阈值
                player_info = game_state.get_player_by_id(player_id)
                if player_info and player_info["is_alive"]:
                    critical_players["suspected_werewolves"].append({
                        "id": player_id,
                        "name": player_info["name"],
                        "suspicion_score": round(suspicion_score, 2),
                        "reason": "投票模式异常"
                    })
        
        return critical_players
    
    def _analyze_voting_patterns(self, game_state: GameState) -> Dict[int, float]:
        """
        分析投票模式，计算怀疑度
        
        Args:
            game_state: 游戏状态
            
        Returns:
            玩家怀疑度分数
        """
        suspicion_scores = {}
        
        # 简化的投票模式分析
        for player in game_state.players:
            player_id = player["id"]
            suspicion_scores[player_id] = 0.0
            
            # 分析该玩家的投票历史
            votes_cast = player.get("votes_cast", [])
            
            # 如果投票总是针对村民，增加怀疑度
            village_targets = 0
            werewolf_targets = 0
            
            for vote in votes_cast:
                target_id = vote.get("target_id")
                target_player = game_state.get_player_by_id(target_id)
                if target_player:
                    if target_player["role"] in self.villager_roles:
                        village_targets += 1
                    elif target_player["role"] in self.werewolf_roles:
                        werewolf_targets += 1
            
            total_votes = len(votes_cast)
            if total_votes > 0:
                village_ratio = village_targets / total_votes
                # 总是投村民的玩家更可疑
                suspicion_scores[player_id] += village_ratio * 0.5
        
        return suspicion_scores 