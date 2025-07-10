"""
游戏状态管理器
中央化管理狼人杀游戏的所有状态信息
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from enum import Enum


class GamePhase(Enum):
    """游戏阶段枚举"""
    PREPARATION = "preparation"
    NIGHT = "night"
    DAY = "day"
    DISCUSSION = "discussion"
    VOTING = "voting"
    GAME_END = "game_end"


class GameState:
    """游戏状态管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化游戏状态
        
        Args:
            config: 游戏配置字典
        """
        self.config = config
        self.game_settings = config.get("game_settings", {})
        
        # 基本游戏信息
        self.current_round = 1
        self.current_phase = GamePhase.PREPARATION
        self.max_rounds = self.game_settings.get("max_rounds")  # 可选配置
        self.total_players = self.game_settings.get("total_players", 7)
        
        # 玩家信息
        self.players: List[Dict[str, Any]] = []
        self.alive_players: List[Dict[str, Any]] = []
        self.dead_players: List[Dict[str, Any]] = []
        
        # 角色配置
        self.roles_config = self.game_settings.get("roles", {})
        
        # 验证配置一致性
        self._validate_player_config()
        
        # 游戏历史和事件
        self.game_history: List[Dict[str, Any]] = []
        self.current_round_events: List[Dict[str, Any]] = []
        
        # 夜晚行动记录
        self.night_actions: Dict[str, Any] = {}
        self.pending_deaths: List[Dict[str, Any]] = []
        
        # 投票相关
        self.voting_results: Dict[str, Any] = {}
        self.nominations: List[Dict[str, Any]] = []
        
        # 特殊角色信息
        self.seer_results: Dict[int, str] = {}  # {player_id: role}
        self.witch_actions: Dict[str, Any] = {}
        
        # 胜利条件追踪
        self.game_winner: Optional[str] = None
        self.game_end_reason: Optional[str] = None
        
        # 日志设置
        self.logger = logging.getLogger(__name__)
        
        # 初始化游戏开始时间
        self.game_start_time = datetime.now()
        self.current_phase_start_time = datetime.now()
    
    def _validate_player_config(self) -> None:
        """
        验证玩家配置的一致性
        """
        try:
            # 计算角色总数
            total_from_roles = sum(self.roles_config.values())
            
            # 检查总数是否一致
            if total_from_roles != self.total_players:
                self.logger.warning(
                    f"配置不一致: 角色总数({total_from_roles}) != 总玩家数({self.total_players})"
                )
            
            # 检查必要角色
            if self.roles_config.get("werewolf", 0) == 0:
                self.logger.warning("配置警告: 缺少狼人角色")
            
            if self.roles_config.get("villager", 0) == 0:
                self.logger.warning("配置警告: 缺少村民角色")
            
            # 检查角色数量合理性
            werewolf_count = self.roles_config.get("werewolf", 0)
            villager_count = self.roles_config.get("villager", 0)
            
            if werewolf_count > villager_count:
                self.logger.warning("配置警告: 狼人数量超过村民数量")
            
            if werewolf_count > self.total_players // 2:
                self.logger.warning("配置警告: 狼人数量过多，可能影响游戏平衡")
                
        except Exception as e:
            self.logger.error(f"配置验证异常: {e}")
    
    def has_round_limit(self) -> bool:
        """
        检查是否有回合数限制
        
        Returns:
            是否有回合数限制
        """
        return self.max_rounds is not None
    
    def add_player(self, player_info: Dict[str, Any]) -> None:
        """
        添加玩家到游戏
        
        Args:
            player_info: 玩家信息字典 {id, name, role, is_alive}
        """
        player_data = {
            "id": player_info["id"],
            "name": player_info["name"],
            "role": player_info["role"],
            "is_alive": True,
            "death_round": None,
            "death_cause": None,
            "votes_received": 0,
            "votes_cast": [],
            "speeches": [],
            "night_actions": []
        }
        
        self.players.append(player_data)
        self.alive_players.append(player_data)
        
        self.log_event({
            "event_type": "player_added",
            "player_id": player_info["id"],
            "player_name": player_info["name"],
            "role": player_info["role"]
        })
    
    def kill_player(self, player_id: int, cause: str = "unknown") -> bool:
        """
        杀死玩家
        
        Args:
            player_id: 玩家ID
            cause: 死亡原因
            
        Returns:
            是否成功杀死玩家
        """
        # 在存活玩家中查找
        player_to_kill = None
        for player in self.alive_players:
            if player["id"] == player_id:
                player_to_kill = player
                break
        
        if not player_to_kill:
            self.logger.warning(f"尝试杀死不存在或已死亡的玩家: {player_id}")
            return False
        
        # 更新玩家状态
        player_to_kill["is_alive"] = False
        player_to_kill["death_round"] = self.current_round
        player_to_kill["death_cause"] = cause
        
        # 移动到死亡列表
        self.alive_players.remove(player_to_kill)
        self.dead_players.append(player_to_kill)
        
        # 同时更新主players列表中的状态
        for player in self.players:
            if player["id"] == player_id:
                player.update(player_to_kill)
                break
        
        self.log_event({
            "event_type": "player_death",
            "player_id": player_id,
            "player_name": player_to_kill["name"],
            "cause": cause,
            "round": self.current_round,
            "phase": self.current_phase.value
        })
        
        self.logger.info(f"玩家{player_id}({player_to_kill['name']})死亡，原因：{cause}")
        return True
    
    def revive_player(self, player_id: int) -> bool:
        """
        复活玩家（女巫救人）
        
        Args:
            player_id: 玩家ID
            
        Returns:
            是否成功复活玩家
        """
        # 在死亡玩家中查找（仅当晚死亡的）
        player_to_revive = None
        for player in self.dead_players:
            if (player["id"] == player_id and 
                player["death_round"] == self.current_round):
                player_to_revive = player
                break
        
        if not player_to_revive:
            self.logger.warning(f"无法复活玩家{player_id}，可能不在当晚死亡列表中")
            return False
        
        # 恢复玩家状态
        player_to_revive["is_alive"] = True
        player_to_revive["death_round"] = None
        player_to_revive["death_cause"] = None
        
        # 移回存活列表
        self.dead_players.remove(player_to_revive)
        self.alive_players.append(player_to_revive)
        
        # 更新主players列表
        for player in self.players:
            if player["id"] == player_id:
                player.update(player_to_revive)
                break
        
        self.log_event({
            "event_type": "player_revived",
            "player_id": player_id,
            "player_name": player_to_revive["name"],
            "round": self.current_round
        })
        
        self.logger.info(f"玩家{player_id}({player_to_revive['name']})被救活")
        return True
    
    def get_alive_players_by_role(self, role: str) -> List[Dict[str, Any]]:
        """
        获取指定角色的存活玩家
        
        Args:
            role: 角色名称
            
        Returns:
            符合条件的玩家列表
        """
        return [player for player in self.alive_players if player["role"] == role]
    
    def get_player_by_id(self, player_id: int) -> Optional[Dict[str, Any]]:
        """
        根据ID获取玩家信息
        
        Args:
            player_id: 玩家ID
            
        Returns:
            玩家信息字典或None
        """
        for player in self.players:
            if player["id"] == player_id:
                return player
        return None
    
    def advance_phase(self) -> GamePhase:
        """
        推进游戏阶段
        
        Returns:
            新的游戏阶段
        """
        # 记录阶段转换
        old_phase = self.current_phase
        self.current_phase_start_time = datetime.now()
        
        if self.current_phase == GamePhase.PREPARATION:
            self.current_phase = GamePhase.NIGHT
        elif self.current_phase == GamePhase.NIGHT:
            self.current_phase = GamePhase.DAY
        elif self.current_phase == GamePhase.DAY:
            self.current_phase = GamePhase.DISCUSSION
        elif self.current_phase == GamePhase.DISCUSSION:
            self.current_phase = GamePhase.VOTING
        elif self.current_phase == GamePhase.VOTING:
            # 投票结束，进入下一轮
            self.current_round += 1
            self.current_phase = GamePhase.NIGHT
            self.current_round_events = []  # 清空当前轮事件
        
        self.log_event({
            "event_type": "phase_change",
            "old_phase": old_phase.value,
            "new_phase": self.current_phase.value,
            "round": self.current_round
        })
        
        return self.current_phase
    
    def log_event(self, event: Dict[str, Any]) -> None:
        """
        记录游戏事件
        
        Args:
            event: 事件信息字典
        """
        event_data = {
            "timestamp": datetime.now().isoformat(),
            "round": self.current_round,
            "phase": self.current_phase.value,
            **event
        }
        
        self.game_history.append(event_data)
        self.current_round_events.append(event_data)
    
    def record_speech(self, player_id: int, speech_content: str) -> None:
        """
        记录玩家发言
        
        Args:
            player_id: 玩家ID
            speech_content: 发言内容
        """
        speech_data = {
            "player_id": player_id,
            "content": speech_content,
            "timestamp": datetime.now().isoformat(),
            "round": self.current_round,
            "phase": self.current_phase.value
        }
        
        # 添加到对应玩家的发言记录
        player = self.get_player_by_id(player_id)
        if player:
            if "speeches" not in player:
                player["speeches"] = []
            player["speeches"].append(speech_data)
        
        self.log_event({
            "event_type": "speech",
            "player_id": player_id,
            "content": speech_content[:100] + "..." if len(speech_content) > 100 else speech_content
        })
    
    def record_vote(self, voter_id: int, target_id: int, reason: str = "") -> None:
        """
        记录投票
        
        Args:
            voter_id: 投票者ID
            target_id: 被投票者ID
            reason: 投票理由
        """
        vote_data = {
            "voter_id": voter_id,
            "target_id": target_id,
            "reason": reason,
            "timestamp": datetime.now().isoformat(),
            "round": self.current_round
        }
        
        # 更新投票者记录
        voter = self.get_player_by_id(voter_id)
        if voter:
            if "votes_cast" not in voter:
                voter["votes_cast"] = []
            voter["votes_cast"].append(vote_data)
        
        # 更新被投票者记录
        target = self.get_player_by_id(target_id)
        if target:
            target["votes_received"] = target.get("votes_received", 0) + 1
        
        self.log_event({
            "event_type": "vote",
            "voter_id": voter_id,
            "target_id": target_id,
            "reason": reason[:50] + "..." if len(reason) > 50 else reason
        })
    
    def record_night_action(self, player_id: int, action_type: str, 
                          target_id: Optional[int] = None, 
                          action_data: Optional[Dict] = None) -> None:
        """
        记录夜晚行动
        
        Args:
            player_id: 行动者ID
            action_type: 行动类型 (kill, divine, save, poison, etc.)
            target_id: 目标玩家ID（如果有）
            action_data: 额外行动数据
        """
        action_record = {
            "player_id": player_id,
            "action_type": action_type,
            "target_id": target_id,
            "action_data": action_data or {},
            "timestamp": datetime.now().isoformat(),
            "round": self.current_round
        }
        
        # 添加到夜晚行动记录
        if action_type not in self.night_actions:
            self.night_actions[action_type] = []
        self.night_actions[action_type].append(action_record)
        
        # 添加到玩家个人记录
        player = self.get_player_by_id(player_id)
        if player:
            if "night_actions" not in player:
                player["night_actions"] = []
            player["night_actions"].append(action_record)
        
        self.log_event({
            "event_type": "night_action",
            "player_id": player_id,
            "action_type": action_type,
            "target_id": target_id
        })
    
    def get_faction_counts(self) -> Dict[str, int]:
        """
        获取各阵营存活人数
        
        Returns:
            阵营人数统计字典
        """
        villager_roles = ["villager", "seer", "witch"]
        werewolf_roles = ["werewolf"]
        
        villager_count = len([p for p in self.alive_players 
                            if p["role"] in villager_roles])
        werewolf_count = len([p for p in self.alive_players 
                            if p["role"] in werewolf_roles])
        
        return {
            "villagers": villager_count,
            "werewolves": werewolf_count,
            "total_alive": len(self.alive_players)
        }
    
    def export_state(self, hide_roles_from_ai: bool = True) -> Dict[str, Any]:
        """
        导出当前游戏状态（用于保存或传递）
        
        Args:
            hide_roles_from_ai: 是否对AI隐藏角色信息
        
        Returns:
            包含所有状态信息的字典
        """
        # 收集当前轮次的所有发言
        recent_speeches = []
        for event in self.game_history:
            if (event.get("event_type") == "speech" and 
                event.get("round") == self.current_round):
                
                player_id = event.get("player_id")
                if player_id is not None:
                    speaker_info = self.get_player_by_id(player_id)
                    recent_speeches.append({
                        "speaker": speaker_info["name"] if speaker_info else f"玩家{player_id}",
                        "speaker_id": player_id,
                        "content": event.get("content", ""),
                        "timestamp": event.get("timestamp")
                    })
        
        # 决定是否隐藏角色信息
        if hide_roles_from_ai:
            # 为AI隐藏角色信息 - 只显示ID、名字、生死状态
            players_safe = []
            for player in self.players:
                safe_player = {
                    "id": player["id"],
                    "name": player["name"],
                    "is_alive": player["is_alive"],
                    "death_round": player.get("death_round"),
                    "death_cause": player.get("death_cause") if not player["is_alive"] else None
                }
                players_safe.append(safe_player)
            
            alive_players_safe = [p for p in players_safe if p["is_alive"]]
            dead_players_safe = [p for p in players_safe if not p["is_alive"]]
            
            return {
                "current_round": self.current_round,
                "current_phase": self.current_phase.value,
                "players": players_safe,
                "alive_players": alive_players_safe,
                "dead_players": dead_players_safe,
                "recent_speeches": recent_speeches,
                "faction_counts": self.get_faction_counts(),
                "timestamp": datetime.now().isoformat()
            }
        else:
            # 为用户/管理员显示完整信息
            return {
                "current_round": self.current_round,
                "current_phase": self.current_phase.value,
                "players": self.players.copy(),
                "alive_players": self.alive_players.copy(),
                "dead_players": self.dead_players.copy(),
                "game_history": self.game_history.copy(),
                "recent_speeches": recent_speeches,
                "night_actions": self.night_actions.copy(),
                "voting_results": self.voting_results.copy(),
                "seer_results": self.seer_results.copy(),
                "witch_actions": self.witch_actions.copy(),
                "game_winner": self.game_winner,
                "game_end_reason": self.game_end_reason,
                "faction_counts": self.get_faction_counts(),
                "timestamp": datetime.now().isoformat()
            }
    
    def get_recent_events(self, count: int = 5) -> List[Dict[str, Any]]:
        """
        获取最近的游戏事件
        
        Args:
            count: 返回的事件数量
            
        Returns:
            最近事件列表
        """
        return self.game_history[-count:] if self.game_history else []
    
    def __str__(self) -> str:
        """字符串表示"""
        faction_counts = self.get_faction_counts()
        return (f"GameState(Round {self.current_round}, {self.current_phase.value}, "
                f"存活: {faction_counts['total_alive']}, "
                f"村民: {faction_counts['villagers']}, "
                f"狼人: {faction_counts['werewolves']})")
    
    def __repr__(self) -> str:
        """详细字符串表示"""
        return self.__str__() 