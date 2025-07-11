"""
狼人Agent实现
使用LlamaIndex Agent工具调用架构进行智能击杀决策
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool

from ..base_agent import BaseGameAgent
from ..tools.werewolf_tools import WerewolfTools


class WerewolfAgent(BaseGameAgent):
    """狼人Agent类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], 
                 identity_system=None, memory_config=None):
        super().__init__(player_id, name, "werewolf", llm_interface, prompts, identity_system, memory_config)
        
        # 狼人特有属性
        self.teammates = []  # 狼人同伴列表
        self.disguise_strategy = "low_profile"  # 伪装策略：low_profile, active, leader
        self.kill_priority = []  # 击杀优先级列表
        self.fake_suspicions = {}  # 虚假怀疑（用于误导）
        
        # 狼人知道所有同伴身份
        self.role_info["known_werewolves"] = []
        self.role_info["known_villagers"] = []
        
        # 初始化工具函数
        self.werewolf_tools = WerewolfTools(self)
        
        # 创建Agent Runner
        self.agent_runner = self._create_agent_runner()
        
        self.logger.info(f"狼人Agent {player_id} 初始化完成")
    
    def register_tools(self) -> None:
        """注册狼人工具函数"""
        try:
            tools = self.werewolf_tools.get_tools()
            for tool in tools:
                self.add_tool(tool)
            self.logger.info(f"狼人{self.player_id}工具注册完成")
        except Exception as e:
            self.logger.error(f"注册狼人工具失败: {e}")
    
    def _create_agent_runner(self) -> Optional[AgentRunner]:
        """创建狼人Agent Runner"""
        try:
            # 暂时返回None，使用传统模式
            # TODO: 后续实现完整的Agent Runner
            self.logger.info("狼人Agent Runner暂未实现，使用传统模式")
            return None
            
        except Exception as e:
            self.logger.error(f"创建狼人Agent Runner失败: {e}")
            return None
    
    def set_teammates(self, teammates: List[int]):
        """设置狼人同伴"""
        self.teammates = [t for t in teammates if t != self.player_id]
        self.role_info["known_werewolves"] = self.teammates.copy()
        
        # 对同伴的怀疑度设为最低
        for teammate in self.teammates:
            self.suspicions[teammate] = -1.0
    
    async def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """狼人夜晚击杀行动（Agent模式）"""
        try:
            if not self.agent_runner:
                self.logger.warning("Agent Runner未初始化，使用传统模式")
                return await self._traditional_night_action(game_state)
            
            # 构建Agent提示
            agent_prompt = self._build_werewolf_agent_prompt(game_state)
            
            # 使用Agent进行决策（暂时使用传统方式）
            response = await self.llm_interface.generate_response(agent_prompt)
            
            # 解析Agent响应
            action_result = self._parse_agent_response(response, game_state)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": "kill",
                "target": action_result.get("target"),
                "player_id": self.player_id,
                "agent_response": str(response),
                "mode": "agent"
            })
            
            return action_result
            
        except Exception as e:
            self.logger.error(f"狼人Agent夜晚行动失败: {e}")
            # 回退到传统模式
            return await self._traditional_night_action(game_state)
    
    def _build_werewolf_agent_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建狼人Agent提示"""
        game_context = self.llm_interface.format_game_context(game_state)
        suspicion_info = self.format_suspicions()
        
        prompt = f"""
        你是狼人，现在是夜晚击杀时间。
        
        当前游戏情况：
        {game_context}
        
        你的同伴：{self.teammates}
        
        你的怀疑情况：
        {suspicion_info}
        
        你的任务：
        1. 分析威胁等级
        2. 与同伴协调行动
        3. 选择击杀目标
        4. 执行击杀行动
        
        请使用提供的工具函数来完成击杀决策。优先击杀对狼人威胁最大的村民。
        """
        
        return prompt
    
    def _parse_agent_response(self, response, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """解析Agent响应"""
        try:
            # 从Agent响应中提取决策信息
            response_text = str(response)
            
            # 查找最终决策
            if "final_decision" in response_text and "target_id" in response_text:
                # 尝试提取目标ID
                import re
                target_matches = re.findall(r'target_id["\']?\s*:\s*(\d+)', response_text)
                if target_matches:
                    target_id = int(target_matches[0])
                    return {
                        "action": "kill",
                        "target": target_id,
                        "success": True,
                        "message": f"狼人Agent选择击杀玩家{target_id}",
                        "agent_mode": True
                    }
            
            # 如果无法解析，返回默认决策
            return self._get_default_kill_decision(game_state)
            
        except Exception as e:
            self.logger.error(f"解析Agent响应失败: {e}")
            return self._get_default_kill_decision(game_state)
    
    def _get_default_kill_decision(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认击杀决策"""
        alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                        if p["id"] != self.player_id and p["id"] not in self.teammates]
        
        if not alive_players:
            return {
                "action": "kill",
                "success": False,
                "message": "没有可击杀的目标"
            }
        
        # 选择最可疑的玩家
        most_suspicious = self.get_most_suspicious_players(1)
        for suspect in most_suspicious:
            if suspect in alive_players:
                return {
                    "action": "kill",
                    "target": suspect,
                    "success": True,
                    "message": f"狼人默认选择击杀玩家{suspect}"
                }
        
        # 随机选择
        import random
        target = random.choice(alive_players)
        return {
            "action": "kill",
            "target": target,
            "success": True,
            "message": f"狼人随机选择击杀玩家{target}"
        }
    
    async def _traditional_night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """传统模式的夜晚行动（备用方案）"""
        try:
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.player_id and p["id"] not in self.teammates]
            
            if not alive_players:
                return {
                    "action": "kill",
                    "success": False,
                    "message": "没有可击杀的目标"
                }
            
            # 选择击杀目标
            kill_target = self._choose_kill_target(alive_players, game_state)
            
            return {
                "action": "kill",
                "target": kill_target,
                "success": True,
                "message": f"狼人（传统模式）选择击杀玩家{kill_target}",
                "agent_mode": False
            }
            
        except Exception as e:
            self.logger.error(f"传统模式夜晚行动失败: {e}")
            return {
                "action": "kill",
                "success": False,
                "message": "击杀行动失败"
            }
    
    def _choose_kill_target(self, candidates: List[int], game_state: Dict[str, Any]) -> int:
        """选择击杀目标"""
        # 优先级策略：
        # 1. 已知的特殊角色
        # 2. 发言很有逻辑的玩家
        # 3. 对狼人怀疑度高的玩家
        
        # 如果有预设的击杀优先级，优先考虑
        for priority_target in self.kill_priority:
            if priority_target in candidates:
                return priority_target
        
        # 选择最可疑的玩家
        most_suspicious = self.get_most_suspicious_players(3)
        for suspect in most_suspicious:
            if suspect in candidates:
                return suspect
        
        # 否则随机选择
        import random
        return random.choice(candidates)
    
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """狼人伪装发言（保持原有逻辑）"""
        try:
            # 使用身份强化的提示词进行伪装
            identity_context = self.get_identity_context()
            enhanced_speech_prompt = self.get_enhanced_prompt("speech_prompt")
            disguise_prompt = self.get_role_prompt("disguise_prompt")
            
            game_context = self.llm_interface.format_game_context(game_state)
            memory_context = self.format_memory_context()
            
            # 生成虚假怀疑来误导村民
            fake_suspicions = self._generate_fake_suspicions(game_state)
            
            werewolf_speech_prompt = f"""
            {identity_context}
            
            【严重警告】你必须完美伪装成一个真正的无辜村民！绝对禁止在发言中透露任何狼人身份信息！
            
            {enhanced_speech_prompt}
            
            【伪装要求】：
            {disguise_prompt}
            
            当前游戏情况：
            {game_context}
            
            你的记忆：
            {memory_context}
            
            你可以表达的怀疑：
            {fake_suspicions}
            
            【绝对机密信息】（绝不能在发言中提及）：
            - 你的真实身份：狼人
            - 你的同伴：玩家{', 玩家'.join(map(str, self.teammates))}
            - 任何狼人相关的策略或想法
            
            现在，请以玩家{self.player_id}号{self.name}的身份，像一个真正的村民一样发言
            """
            
            enhanced_role_context = self.get_enhanced_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                werewolf_speech_prompt, enhanced_role_context
            )
            
            # 应用狼人专用过滤器
            filtered_response = self._filter_werewolf_speech(response)
            
            # 记录自己的发言
            self.update_memory("speeches", {
                "speaker": f"玩家{self.player_id}",
                "content": filtered_response,
                "speaker_id": self.player_id
            })
            
            return filtered_response
            
        except Exception as e:
            self.logger.error(f"狼人发言时出错: {e}")
            return f"我觉得需要更仔细地分析局势。"
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """狼人投票（伪装投票，保持原有逻辑）"""
        try:
            # 移除自己和同伴
            valid_candidates = [c for c in candidates 
                             if c != self.player_id and c not in self.teammates]
            
            if not valid_candidates:
                # 如果只能投同伴，随机选一个
                import random
                return random.choice([c for c in candidates if c != self.player_id])
            
            vote_prompt = self.get_role_prompt("vote_prompt")
            game_context = self.llm_interface.format_game_context(game_state)
            fake_suspicions = self._generate_fake_suspicions(game_state)
            
            candidate_info = ", ".join([f"玩家{c}" for c in valid_candidates])
            
            werewolf_voting_prompt = f"""
            {vote_prompt}
            
            当前游戏情况：
            {game_context}
            
            你的虚假怀疑（用于误导）：
            {fake_suspicions}
            
            可投票的玩家：{candidate_info}
            
            注意：绝对不能投票给你的同伴：{self.teammates}
            
            选择一个村民投票，要看起来合理且无辜。优先选择对狼人威胁大的村民。
            格式：投票给玩家X，理由：XXXX
            """
            
            role_context = self.get_role_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                werewolf_voting_prompt, role_context
            )
            
            # 提取投票目标
            vote_target = self.llm_interface.extract_vote_choice(response, valid_candidates)
            
            if vote_target is None:
                # 根据威胁度选择
                vote_target = self._choose_strategic_vote_target(valid_candidates, game_state)
            
            # 记录投票
            self.update_memory("votes", {
                "voter": f"玩家{self.player_id}",
                "target": f"玩家{vote_target}",
                "voter_id": self.player_id,
                "target_id": vote_target,
                "reason": response
            })
            
            return vote_target
            
        except Exception as e:
            self.logger.error(f"狼人投票时出错: {e}")
            import random
            return random.choice([c for c in candidates if c != self.player_id])
    
    def _generate_fake_suspicions(self, game_state: Dict[str, Any]) -> str:
        """生成虚假怀疑来误导村民"""
        alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                        if p["id"] != self.player_id and p["id"] not in self.teammates]
        
        if not alive_players:
            return "暂无明确怀疑对象"
        
        # 随机选择一些村民作为虚假怀疑目标
        import random
        fake_targets = random.sample(alive_players, min(2, len(alive_players)))
        
        fake_suspicions = []
        for target in fake_targets:
            suspicion_level = random.choice(["轻微怀疑", "中度怀疑"])
            fake_suspicions.append(f"玩家{target}({suspicion_level})")
        
        return "伪装怀疑: " + ", ".join(fake_suspicions)
    
    def _choose_strategic_vote_target(self, candidates: List[int], game_state: Dict[str, Any]) -> int:
        """战略性选择投票目标"""
        # 优先投票给看起来有威胁的村民
        # 这里可以添加更复杂的逻辑，比如分析发言内容
        
        # 简单策略：随机选择，但避开同伴
        valid_targets = [c for c in candidates if c not in self.teammates]
        import random
        return random.choice(valid_targets) if valid_targets else random.choice(candidates)
    
    def _filter_werewolf_speech(self, speech: str) -> str:
        """狼人发言专用过滤器"""
        # 基础过滤
        filtered = self._filter_speech_output(speech)
        
        # 狼人特定过滤
        werewolf_forbidden_words = [
            "狼人", "同伴", "队友", "击杀", "杀人", "夜晚", "伪装", "欺骗",
            "狼群", "狼队", "狼人身份", "我是狼", "我们狼", "狼人同伴",
            "击杀目标", "杀人计划", "伪装策略", "欺骗村民", "狼人团队"
        ]
        
        for word in werewolf_forbidden_words:
            if word in filtered:
                filtered = filtered.replace(word, "")
        
        # 如果过滤后内容过短，返回安全默认内容
        if len(filtered.strip()) < 10:
            return "我觉得需要更仔细地分析局势。"
        
        return filtered.strip() 