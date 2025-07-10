"""
AI智能体基类模块
定义狼人杀游戏中所有AI角色的基础行为和接口
"""

import json
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from datetime import datetime

from .llm_interface import QwenInterface
from .identity_system import IdentitySystem


class BaseAIAgent(ABC):
    """AI智能体基类，所有角色都继承此类"""
    
    def __init__(self, player_id: int, name: str, role: str, 
                 llm_interface: QwenInterface, prompts: Dict[str, Any], 
                 identity_system: Optional[IdentitySystem] = None):
        """
        初始化AI智能体
        
        Args:
            player_id: 玩家ID
            name: 玩家名称
            role: 角色类型
            llm_interface: LLM接口实例
            prompts: 提示词模板
            identity_system: 身份认同系统
        """
        self.player_id = player_id
        self.name = name
        self.role = role
        self.llm_interface = llm_interface
        self.prompts = prompts
        
        # 身份认同系统
        self.identity_system = identity_system or IdentitySystem()
        self.identity_profile = self.identity_system.create_identity_profile(player_id, name, role)
        
        # 玩家状态
        self.is_alive = True
        self.is_voted_out = False
        
        # 游戏记忆
        self.game_memory = {
            "speeches": [],
            "votes": [],
            "night_actions": [],
            "observations": []
        }
        
        # 角色特定信息
        self.role_info = {}
        self.suspicions = {}  # 对其他玩家的怀疑度
        
        # 设置日志
        self.logger = logging.getLogger(f"{self.__class__.__name__}_{player_id}")
    
    @abstractmethod
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """
        白天发言
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            发言内容
        """
        pass
    
    @abstractmethod
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """
        投票选择
        
        Args:
            game_state: 当前游戏状态
            candidates: 候选玩家ID列表
            
        Returns:
            投票目标的玩家ID
        """
        pass
    
    @abstractmethod
    async def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        夜晚行动
        
        Args:
            game_state: 当前游戏状态
            
        Returns:
            行动结果字典
        """
        pass
    
    def update_memory(self, event_type: str, event_data: Dict[str, Any]):
        """
        更新游戏记忆
        
        Args:
            event_type: 事件类型 (speech, vote, night_action, observation)
            event_data: 事件数据
        """
        timestamp = datetime.now().isoformat()
        event_data["timestamp"] = timestamp
        
        if event_type in self.game_memory:
            self.game_memory[event_type].append(event_data)
            # 限制记忆长度，避免上下文过长
            if len(self.game_memory[event_type]) > 20:
                self.game_memory[event_type] = self.game_memory[event_type][-20:]
    
    def update_suspicion(self, target_id: int, suspicion_change: float, reason: str = ""):
        """
        更新对其他玩家的怀疑度
        
        Args:
            target_id: 目标玩家ID
            suspicion_change: 怀疑度变化（-1.0到1.0）
            reason: 原因
        """
        if target_id == self.player_id:
            return  # 不怀疑自己
        
        current_suspicion = self.suspicions.get(target_id, 0.0)
        new_suspicion = max(-1.0, min(1.0, current_suspicion + suspicion_change))
        self.suspicions[target_id] = new_suspicion
        
        self.logger.debug(f"更新对玩家{target_id}的怀疑度: {current_suspicion:.2f} -> {new_suspicion:.2f} ({reason})")
    
    def get_role_prompt(self, prompt_type: str = "base_prompt") -> str:
        """
        获取角色相关的提示词
        
        Args:
            prompt_type: 提示词类型
            
        Returns:
            角色提示词
        """
        role_prompts = self.prompts.get(self.role, {})
        return role_prompts.get(prompt_type, "")
    
    def get_enhanced_prompt(self, prompt_type: str = "base_prompt") -> str:
        """
        获取身份强化的提示词
        
        Args:
            prompt_type: 提示词类型
            
        Returns:
            增强后的提示词
        """
        base_prompt = self.get_role_prompt(prompt_type)
        if self.identity_system:
            return self.identity_system.get_role_enhanced_prompt(self.player_id, base_prompt)
        return base_prompt
    
    def get_identity_context(self) -> str:
        """
        获取身份上下文信息
        
        Returns:
            身份上下文字符串
        """
        if self.identity_system:
            return self.identity_system.get_enhanced_prompt_prefix(self.player_id)
        return f"你是玩家{self.player_id}号{self.name}。"
    
    def format_suspicions(self) -> str:
        """格式化怀疑度信息为文本"""
        if not self.suspicions:
            return "暂无明确怀疑对象"
        
        suspicion_list = []
        for player_id, suspicion in sorted(self.suspicions.items(), 
                                         key=lambda x: x[1], reverse=True):
            if suspicion > 0.1:
                level = "高度怀疑" if suspicion > 0.6 else "中度怀疑" if suspicion > 0.3 else "轻微怀疑"
                suspicion_list.append(f"玩家{player_id}({level})")
        
        return "怀疑对象: " + ", ".join(suspicion_list) if suspicion_list else "暂无明确怀疑对象"
    
    def format_memory_context(self, max_events: int = 5) -> str:
        """
        格式化记忆为上下文文本
        
        Args:
            max_events: 最多包含的事件数量
            
        Returns:
            格式化的记忆上下文
        """
        context_parts = []
        
        # 最近的发言
        recent_speeches = self.game_memory["speeches"][-max_events:]
        if recent_speeches:
            speech_texts = []
            for speech in recent_speeches:
                speaker = speech.get("speaker", "未知")
                content = speech.get("content", "")[:100]  # 限制长度
                speech_texts.append(f"{speaker}: {content}")
            context_parts.append("最近发言:\n" + "\n".join(speech_texts))
        
        # 最近的投票
        recent_votes = self.game_memory["votes"][-max_events:]
        if recent_votes:
            vote_texts = []
            for vote in recent_votes:
                voter = vote.get("voter", "未知")
                target = vote.get("target", "未知")
                vote_texts.append(f"{voter}投票给{target}")
            context_parts.append("最近投票:\n" + "\n".join(vote_texts))
        
        # 观察记录
        recent_observations = self.game_memory["observations"][-max_events:]
        if recent_observations:
            obs_texts = []
            for obs in recent_observations:
                content = obs.get("content", "")
                obs_texts.append(content)
            context_parts.append("观察记录:\n" + "\n".join(obs_texts))
        
        return "\n\n".join(context_parts) if context_parts else "暂无相关记忆"
    
    async def analyze_speech(self, speaker_id: int, speech_content: str) -> Dict[str, Any]:
        """
        分析其他玩家的发言
        
        Args:
            speaker_id: 发言者ID
            speech_content: 发言内容
            
        Returns:
            分析结果
        """
        if speaker_id == self.player_id:
            return {"suspicion_change": 0, "analysis": "自己的发言"}
        
        # 构建分析提示
        analysis_prompt = f"""
        请分析以下发言的可疑程度：
        
        发言者：玩家{speaker_id}
        发言内容：{speech_content}
        
        你的角色：{self.role}
        你的怀疑度情况：{self.format_suspicions()}
        
        请从以下角度分析：
        1. 逻辑是否合理
        2. 是否有矛盾之处
        3. 是否在转移注意力
        4. 整体可信度如何
        
        请给出-0.3到0.3之间的怀疑度变化值和简短分析。
        格式：怀疑度变化:X.X,分析:XXXX
        """
        
        try:
            role_context = self.get_role_prompt()
            response = await self.llm_interface.generate_response(
                analysis_prompt, role_context
            )
            
            # 解析回复
            import re
            suspicion_match = re.search(r'怀疑度变化:([-+]?\d*\.?\d+)', response)
            analysis_match = re.search(r'分析:(.+)', response)
            
            suspicion_change = 0.0
            if suspicion_match:
                suspicion_change = float(suspicion_match.group(1))
                suspicion_change = max(-0.3, min(0.3, suspicion_change))
            
            analysis = analysis_match.group(1).strip() if analysis_match else response
            
            # 更新怀疑度
            self.update_suspicion(speaker_id, suspicion_change, f"发言分析: {analysis[:50]}")
            
            return {
                "suspicion_change": suspicion_change,
                "analysis": analysis
            }
            
        except Exception as e:
            self.logger.error(f"分析发言时出错: {e}")
            return {"suspicion_change": 0, "analysis": "分析失败"}
    
    def get_most_suspicious_players(self, count: int = 3) -> List[int]:
        """
        获取最可疑的玩家列表
        
        Args:
            count: 返回的玩家数量
            
        Returns:
            按怀疑度排序的玩家ID列表
        """
        sorted_suspicions = sorted(self.suspicions.items(), 
                                 key=lambda x: x[1], reverse=True)
        
        # 过滤掉怀疑度太低的
        suspicious_players = [player_id for player_id, suspicion in sorted_suspicions 
                            if suspicion > 0.1]
        
        return suspicious_players[:count]
    
    def get_least_suspicious_players(self, count: int = 3) -> List[int]:
        """
        获取最不可疑的玩家列表
        
        Args:
            count: 返回的玩家数量
            
        Returns:
            按怀疑度排序的玩家ID列表（最低的在前）
        """
        sorted_suspicions = sorted(self.suspicions.items(), 
                                 key=lambda x: x[1])
        
        # 过滤掉怀疑度太高的
        trustworthy_players = [player_id for player_id, suspicion in sorted_suspicions 
                             if suspicion < 0.5]
        
        return trustworthy_players[:count]
    
    def die(self, cause: str = "未知"):
        """
        玩家死亡
        
        Args:
            cause: 死亡原因
        """
        self.is_alive = False
        self.logger.info(f"玩家{self.player_id}({self.name})死亡，原因：{cause}")
        
        # 记录死亡事件
        self.update_memory("observation", {
            "type": "death",
            "target": self.player_id,
            "cause": cause,
            "content": f"我死亡了，原因：{cause}"
        })
    
    def observe_death(self, player_id: int, cause: str = "未知"):
        """
        观察到其他玩家死亡
        
        Args:
            player_id: 死亡玩家ID
            cause: 死亡原因
        """
        self.update_memory("observation", {
            "type": "death",
            "target": player_id,
            "cause": cause,
            "content": f"玩家{player_id}死亡，原因：{cause}"
        })
        
        # 如果是被投票死亡，增加对投票者的好感
        if cause == "投票放逐":
            # 这里可以添加更复杂的分析逻辑
            pass
    
    def observe_vote(self, voter_id: int, target_id: int):
        """
        观察到投票
        
        Args:
            voter_id: 投票者ID
            target_id: 被投票者ID
        """
        self.update_memory("vote", {
            "voter": f"玩家{voter_id}",
            "target": f"玩家{target_id}",
            "voter_id": voter_id,
            "target_id": target_id
        })
        
        # 如果投票目标是自己怀疑的人，降低对投票者的怀疑
        if target_id in self.suspicions and self.suspicions[target_id] > 0.3:
            self.update_suspicion(voter_id, -0.1, f"投票给可疑玩家{target_id}")
    
    def __str__(self) -> str:
        """字符串表示"""
        status = "存活" if self.is_alive else "死亡"
        return f"玩家{self.player_id}({self.name}) - {self.role} - {status}"
    
    def _filter_speech_output(self, speech: str) -> str:
        """
        通用的发言输出过滤器，移除不当内容
        
        Args:
            speech: 原始发言内容
            
        Returns:
            过滤后的发言内容
        """
        try:
            # 移除常见的元游戏内容和分析标记
            import re
            
            # 移除分析标记和括号内容
            speech = re.sub(r'\*\*[^*]*\*\*', '', speech)  # 移除**标记内容
            speech = re.sub(r'\([^)]*分析[^)]*\)', '', speech)  # 移除包含"分析"的括号内容
            speech = re.sub(r'（[^）]*分析[^）]*）', '', speech)  # 移除包含"分析"的中文括号内容
            speech = re.sub(r'\([^)]*策略[^)]*\)', '', speech)  # 移除包含"策略"的括号内容
            speech = re.sub(r'（[^）]*策略[^）]*）', '', speech)  # 移除包含"策略"的中文括号内容
            
            # 移除常见的元游戏词汇
            dangerous_phrases = [
                "作为.*?角色", "我的身份是", "真实身份", "角色扮演", 
                "元游戏", "游戏策略", "AI分析", "系统提示"
            ]
            
            for phrase in dangerous_phrases:
                speech = re.sub(phrase, '', speech, flags=re.IGNORECASE)
            
            # 清理多余的空格和标点
            speech = ' '.join(speech.split())
            speech = speech.strip()
            
            # 如果过滤后内容过短，返回安全的默认发言
            if len(speech) < 8:
                return "我需要仔细观察每个人的行为。"
            
            return speech
            
        except Exception as e:
            # 过滤出错时返回安全的默认发言
            return "我觉得需要更仔细地分析当前的局势。"

    def __repr__(self) -> str:
        """详细字符串表示"""
        return f"<{self.__class__.__name__}(id={self.player_id}, name='{self.name}', role='{self.role}', alive={self.is_alive})>" 