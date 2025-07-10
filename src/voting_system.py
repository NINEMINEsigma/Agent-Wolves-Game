"""
投票系统
处理投票收集、统计和结果执行
"""

import asyncio
import logging
import random
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter

from .ai_agent import BaseAIAgent
from .game_state import GameState


class VotingSystem:
    """投票系统"""
    
    def __init__(self, game_state: GameState):
        """
        初始化投票系统
        
        Args:
            game_state: 游戏状态管理器
        """
        self.game_state = game_state
        self.logger = logging.getLogger(__name__)
        
        # 投票配置
        self.vote_timeout = 30  # 投票超时时间（秒）
        self.allow_abstention = False  # 是否允许弃权
        self.require_majority = False  # 是否要求过半数票
        
    async def collect_votes(self, voters: List[BaseAIAgent], 
                          candidates: List[int],
                          vote_type: str = "elimination") -> Dict[int, int]:
        """
        收集投票
        
        Args:
            voters: 投票者列表
            candidates: 候选人ID列表
            vote_type: 投票类型（elimination, nomination等）
            
        Returns:
            投票结果字典 {candidate_id: vote_count}
        """
        vote_results = Counter()
        vote_details = []
        
        self.logger.info(f"开始{vote_type}投票，投票者: {len(voters)}人，候选人: {candidates}")
        
        # 并发收集所有投票
        vote_tasks = []
        for voter in voters:
            if voter.is_alive:
                task = self._collect_single_vote(voter, candidates, vote_type)
                vote_tasks.append(task)
        
        # 等待所有投票完成
        vote_responses = await asyncio.gather(*vote_tasks, return_exceptions=True)
        
        # 处理投票结果
        alive_voters = [v for v in voters if v.is_alive]
        for i, response in enumerate(vote_responses):
            voter = alive_voters[i] if i < len(alive_voters) else None
            
            if isinstance(response, Exception):
                self.logger.error(f"投票者{voter.player_id if voter else 'unknown'}投票异常: {response}")
                # 异常情况下随机投票
                if voter and candidates:
                    fallback_vote = random.choice(candidates)
                    vote_results[fallback_vote] += 1
                    vote_details.append({
                        "voter_id": voter.player_id,
                        "target_id": fallback_vote,
                        "reason": "投票异常，随机选择",
                        "is_fallback": True
                    })
                continue
            
            if response is not None and voter:
                target_id, reason = response
                
                # 验证投票有效性
                if target_id in candidates:
                    vote_results[target_id] += 1
                    vote_details.append({
                        "voter_id": voter.player_id,
                        "target_id": target_id,
                        "reason": reason,
                        "is_fallback": False
                    })
                    
                    # 记录到游戏状态
                    self.game_state.record_vote(voter.player_id, target_id, reason)
                    
                    self.logger.info(f"玩家{voter.player_id}投票给玩家{target_id}: {reason[:50]}...")
                else:
                    self.logger.warning(f"玩家{voter.player_id}投票无效，目标{target_id}不在候选人列表中")
                    # 无效投票，随机选择
                    fallback_vote = random.choice(candidates) if candidates else None
                    if fallback_vote:
                        vote_results[fallback_vote] += 1
                        vote_details.append({
                            "voter_id": voter.player_id,
                            "target_id": fallback_vote,
                            "reason": "原投票无效，随机选择",
                            "is_fallback": True
                        })
        
        # 记录投票详情到游戏状态
        self.game_state.voting_results[f"{vote_type}_round_{self.game_state.current_round}"] = {
            "vote_counts": dict(vote_results),
            "vote_details": vote_details,
            "candidates": candidates,
            "total_voters": len(voters)
        }
        
        return dict(vote_results)
    
    async def _collect_single_vote(self, voter: BaseAIAgent, 
                                 candidates: List[int],
                                 vote_type: str) -> Optional[Tuple[int, str]]:
        """
        收集单个玩家的投票
        
        Args:
            voter: 投票者
            candidates: 候选人列表
            vote_type: 投票类型
            
        Returns:
            (目标ID, 投票理由) 或 None
        """
        try:
            # 构建当前游戏状态（对AI隐藏角色信息）
            current_state = self.game_state.export_state(hide_roles_from_ai=True)
            
            # 调用AI进行投票
            target_id = await voter.vote(current_state, candidates)
            
            # 获取投票理由（从最近的记忆中提取）
            recent_votes = voter.game_memory.get("votes", [])
            reason = ""
            if recent_votes:
                reason = recent_votes[-1].get("reason", "")
            
            return target_id, reason
            
        except Exception as e:
            self.logger.error(f"收集玩家{voter.player_id}投票时出错: {e}")
            return None
    
    def calculate_result(self, votes: Dict[int, int]) -> Dict[str, Any]:
        """
        计算投票结果
        
        Args:
            votes: 投票统计 {candidate_id: vote_count}
            
        Returns:
            投票结果分析
        """
        if not votes:
            return {
                "winner": None,
                "is_tie": False,
                "max_votes": 0,
                "tied_players": [],
                "vote_distribution": {},
                "total_votes": 0
            }
        
        total_votes = sum(votes.values())
        max_votes = max(votes.values())
        
        # 找出得票最多的玩家
        winners = [player_id for player_id, vote_count in votes.items() 
                  if vote_count == max_votes]
        
        is_tie = len(winners) > 1
        
        # 计算得票分布
        vote_distribution = {}
        for player_id, vote_count in votes.items():
            percentage = (vote_count / total_votes * 100) if total_votes > 0 else 0
            vote_distribution[player_id] = {
                "votes": vote_count,
                "percentage": round(percentage, 1)
            }
        
        result = {
            "winner": winners[0] if not is_tie else None,
            "is_tie": is_tie,
            "max_votes": max_votes,
            "tied_players": winners if is_tie else [],
            "vote_distribution": vote_distribution,
            "total_votes": total_votes,
            "all_candidates": list(votes.keys())
        }
        
        self.logger.info(f"投票结果: {result}")
        return result
    
    def handle_tie(self, tied_players: List[int], 
                  original_votes: Dict[int, int], 
                  is_revote: bool = False) -> Dict[str, Any]:
        """
        处理平票情况
        
        Args:
            tied_players: 平票的玩家ID列表
            original_votes: 原始投票结果
            is_revote: 是否为重投票
            
        Returns:
            平票处理结果
        """
        if not tied_players:
            return {"action": "no_tie", "target": None}
        
        if len(tied_players) == 1:
            return {"action": "single_winner", "target": tied_players[0]}
        
        self.logger.info(f"平票处理: {tied_players}, 是否重投: {is_revote}")
        
        if not is_revote:
            # 首次平票：要求重新发言和投票
            result = {
                "action": "revote_required",
                "target": None,
                "tied_players": tied_players,
                "reason": "首次平票，需要重新发言和投票"
            }
            self.logger.info("首次平票，将进行重新发言和投票")
        else:
            # 二次平票：跳过放逐
            result = {
                "action": "skip_elimination", 
                "target": None,
                "tied_players": tied_players,
                "reason": "二次平票，跳过放逐环节"
            }
            self.logger.info("二次平票，跳过放逐环节")
        
        # 记录平票处理结果
        self.game_state.log_event({
            "event_type": "tie_break",
            "tied_players": tied_players,
            "is_revote": is_revote,
            "action": result["action"],
            "selected": result["target"],
            "original_votes": original_votes
        })
        
        return result
    
    def execute_vote_result(self, target_id: Optional[int], 
                          vote_result: Dict[str, Any],
                          execution_type: str = "elimination") -> bool:
        """
        执行投票结果
        
        Args:
            target_id: 目标玩家ID
            vote_result: 投票结果详情
            execution_type: 执行类型（elimination, nomination等）
            
        Returns:
            是否成功执行
        """
        if target_id is None:
            self.logger.info(f"{execution_type}投票无结果，无人被选中")
            self.game_state.log_event({
                "event_type": "vote_execution",
                "execution_type": execution_type,
                "target_id": None,
                "result": "no_target",
                "vote_result": vote_result
            })
            return True
        
        target_player = self.game_state.get_player_by_id(target_id)
        if not target_player:
            self.logger.error(f"执行{execution_type}失败：玩家{target_id}不存在")
            return False
        
        if execution_type == "elimination":
            # 放逐玩家
            success = self.game_state.kill_player(target_id, "投票放逐")
            if success:
                self.logger.info(f"玩家{target_id}({target_player['name']})被投票放逐")
            else:
                self.logger.error(f"放逐玩家{target_id}失败")
                
        elif execution_type == "nomination":
            # 提名（不实际执行死亡）
            self.logger.info(f"玩家{target_id}({target_player['name']})被提名")
            success = True
            
        else:
            self.logger.warning(f"未知的执行类型: {execution_type}")
            success = True
        
        # 记录执行结果
        self.game_state.log_event({
            "event_type": "vote_execution",
            "execution_type": execution_type,
            "target_id": target_id,
            "target_name": target_player["name"],
            "result": "success" if success else "failed",
            "vote_result": vote_result
        })
        
        return success
    
    async def conduct_full_vote(self, voters: List[BaseAIAgent],
                              candidates: List[int],
                              vote_type: str = "elimination",
                              is_revote: bool = False) -> Dict[str, Any]:
        """
        进行完整的投票流程
        
        Args:
            voters: 投票者列表
            candidates: 候选人列表
            vote_type: 投票类型
            is_revote: 是否为重投票
            
        Returns:
            完整投票结果
        """
        self.logger.info(f"开始{vote_type}投票流程, 是否重投: {is_revote}")
        
        # 1. 收集投票
        votes = await self.collect_votes(voters, candidates, vote_type)
        
        # 2. 计算结果
        vote_result = self.calculate_result(votes)
        
        # 3. 处理平票
        tie_result = None
        final_target = None
        needs_revote = False
        
        if vote_result["is_tie"]:
            tie_result = self.handle_tie(vote_result["tied_players"], votes, is_revote)
            final_target = tie_result["target"]
            needs_revote = (tie_result["action"] == "revote_required")
        else:
            final_target = vote_result["winner"]
        
        # 4. 执行结果（只有确定目标时才执行）
        execution_success = True
        if final_target is not None and not needs_revote:
            execution_success = self.execute_vote_result(final_target, vote_result, vote_type)
        
        # 5. 汇总结果
        full_result = {
            "vote_counts": votes,
            "vote_analysis": vote_result,
            "final_target": final_target,
            "execution_success": execution_success,
            "vote_type": vote_type,
            "participants": len(voters),
            "needs_revote": needs_revote,
            "tie_result": tie_result,
            "is_revote": is_revote,
            "timestamp": self.game_state.current_phase_start_time.isoformat()
        }
        
        self.logger.info(f"{vote_type}投票完成，结果: {full_result}")
        return full_result
    
    def get_voting_statistics(self) -> Dict[str, Any]:
        """
        获取投票统计信息
        
        Returns:
            投票统计数据
        """
        voting_history = {}
        for key, vote_data in self.game_state.voting_results.items():
            round_info = key.split("_")
            if len(round_info) >= 3:
                round_num = round_info[2]
                voting_history[round_num] = vote_data
        
        return {
            "total_votes_conducted": len(voting_history),
            "voting_history": voting_history,
            "current_round": self.game_state.current_round
        } 