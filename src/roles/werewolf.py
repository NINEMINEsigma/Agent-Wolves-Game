"""
狼人角色实现
狼人需要在白天伪装成村民，夜晚击杀村民，与同伴配合
"""

import random
from typing import Dict, Any, List
from ..ai_agent import BaseAIAgent


class Werewolf(BaseAIAgent):
    """狼人角色类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], identity_system=None, memory_config=None):
        super().__init__(player_id, name, "werewolf", llm_interface, prompts, identity_system, memory_config)
        
        # 狼人特有属性
        self.teammates = []  # 狼人同伴列表
        self.disguise_strategy = "low_profile"  # 伪装策略：low_profile, active, leader
        self.kill_priority = []  # 击杀优先级列表
        self.fake_suspicions = {}  # 虚假怀疑（用于误导）
        
        # 狼人知道所有同伴身份
        self.role_info["known_werewolves"] = []
        self.role_info["known_villagers"] = []
    
    def set_teammates(self, teammates: List[int]):
        """设置狼人同伴"""
        self.teammates = [t for t in teammates if t != self.player_id]
        self.role_info["known_werewolves"] = self.teammates.copy()
        
        # 对同伴的怀疑度设为最低
        for teammate in self.teammates:
            self.suspicions[teammate] = -1.0
    
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """狼人伪装发言"""
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
            
            现在，请以玩家{self.player_id}号{self.name}的身份，像一个真正的村民一样发言。
            你的发言必须：
            1. 完全以村民的视角思考问题
            2. 表现出对局势的真诚关心
            3. 简洁自然
            4. 绝不包含任何策略分析或元游戏内容
            
            只返回你作为"村民"的纯净发言内容，不要包含任何括号、分析或思考过程！
            """
            
            enhanced_role_context = self.get_enhanced_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                werewolf_speech_prompt, enhanced_role_context
            )
            
            # 过滤危险内容，确保不暴露狼人身份
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
            return f"我觉得大家都在认真思考，我们需要仔细观察。"
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """狼人投票（伪装投票）"""
        try:
            # 移除自己和同伴
            valid_candidates = [c for c in candidates 
                             if c != self.player_id and c not in self.teammates]
            
            if not valid_candidates:
                # 如果只能投同伴，随机选一个
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
            
            if vote_target is None or vote_target in self.teammates:
                # 选择最威胁的村民
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
            valid_candidates = [c for c in candidates 
                             if c != self.player_id and c not in self.teammates]
            return random.choice(valid_candidates) if valid_candidates else candidates[0]
    
    async def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """狼人夜晚击杀行动"""
        try:
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.player_id and p["id"] not in self.teammates]
            
            if not alive_players:
                return {
                    "action": "kill",
                    "success": False,
                    "message": "没有可击杀的目标"
                }
            
            kill_prompt = self.get_role_prompt("kill_prompt")
            game_context = self.llm_interface.format_game_context(game_state)
            
            target_info = ", ".join([f"玩家{p}" for p in alive_players])
            
            kill_decision_prompt = f"""
            {kill_prompt}
            
            当前游戏情况：
            {game_context}
            
            可击杀的目标：{target_info}
            
            你的同伴：{self.teammates}
            
            选择今晚要击杀的村民。优先考虑：
            1. 预言家等特殊角色
            2. 发言很有逻辑的村民
            3. 对你们怀疑较高的村民
            
            格式：击杀玩家X，理由：XXXX
            """
            
            role_context = self.get_role_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                kill_decision_prompt, role_context
            )
            
            # 提取击杀目标
            kill_target = self.llm_interface.extract_vote_choice(response, alive_players)
            
            if kill_target is None:
                # 根据威胁度选择
                kill_target = self._choose_kill_target(alive_players, game_state)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": "kill",
                "target": kill_target,
                "player_id": self.player_id,
                "reason": response
            })
            
            return {
                "action": "kill",
                "target": kill_target,
                "success": True,
                "message": f"狼人{self.player_id}选择击杀玩家{kill_target}"
            }
            
        except Exception as e:
            self.logger.error(f"狼人夜晚行动时出错: {e}")
            # 随机选择一个目标
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.player_id and p["id"] not in self.teammates]
            if alive_players:
                target = random.choice(alive_players)
                return {
                    "action": "kill",
                    "target": target,
                    "success": True,
                    "message": f"狼人{self.player_id}随机选择击杀玩家{target}"
                }
            else:
                return {
                    "action": "kill",
                    "success": False,
                    "message": "没有可击杀的目标"
                }
    
    def _generate_fake_suspicions(self, game_state: Dict[str, Any]) -> str:
        """生成虚假怀疑来误导村民"""
        alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                        if p["id"] != self.player_id and p["id"] not in self.teammates]
        
        if not alive_players:
            return "暂无明确怀疑对象"
        
        # 随机选择一些村民作为虚假怀疑目标
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
        return random.choice(valid_targets) if valid_targets else random.choice(candidates)
    
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
        
        # 否则随机选择
        return random.choice(candidates)
    
    def identify_special_roles(self, speech_analysis: Dict[str, Any]):
        """通过发言分析识别特殊角色"""
        # 这里可以实现更复杂的角色识别逻辑
        # 比如预言家可能会暗示查验结果
        pass
    
    def coordinate_with_teammates(self, teammate_actions: Dict[int, str]):
        """与狼人同伴协调行动"""
        # 分析同伴的行动，调整自己的策略
        for teammate_id, action in teammate_actions.items():
            if "怀疑" in action and teammate_id in self.teammates:
                # 如果同伴怀疑某人，自己也可以跟进
                pass
    
    def analyze_risk_level(self, game_state: Dict[str, Any]) -> float:
        """分析当前风险等级"""
        # 评估暴露风险
        risk_factors = []
        
        # 检查是否有人高度怀疑自己
        suspicion_towards_me = 0
        for speech in self.game_memory["speeches"]:
            if f"玩家{self.player_id}" in speech.get("content", ""):
                if any(word in speech["content"] for word in ["怀疑", "可疑", "狼人"]):
                    suspicion_towards_me += 1
        
        risk_level = min(1.0, suspicion_towards_me * 0.2)
        return risk_level
    
    def adjust_disguise_strategy(self, risk_level: float):
        """根据风险等级调整伪装策略"""
        if risk_level > 0.7:
            self.disguise_strategy = "low_profile"  # 低调
        elif risk_level > 0.4:
            self.disguise_strategy = "active"  # 积极参与但不激进
        else:
            self.disguise_strategy = "leader"  # 可以适当引导
    
    def _filter_werewolf_speech(self, speech: str) -> str:
        """过滤狼人发言中的危险内容"""
        try:
            # 危险关键词列表
            dangerous_keywords = [
                "伪装", "策略", "误导", "同伴", "狼人", "击杀", "配合",
                "保护", "暴露", "真实身份", "计划", "目标", "威胁",
                "分析", "战术", "布局", "陷阱", "诱导"
            ]
            
            # 检查是否包含策略分析标记
            if "**" in speech or "策略分析" in speech or "伪装策略" in speech:
                # 如果包含明显的策略分析内容，返回安全的默认发言
                return f"我觉得大家的发言都很有道理，需要仔细分析一下局势。"
            
            # 检查是否包含危险关键词
            for keyword in dangerous_keywords:
                if keyword in speech:
                    # 替换危险内容为安全表达
                    safe_replacements = {
                        "伪装": "表现",
                        "策略": "想法", 
                        "误导": "提醒",
                        "同伴": "其他玩家",
                        "狼人": "可疑的人",
                        "击杀": "投票",
                        "配合": "合作",
                        "保护": "支持",
                        "暴露": "发现",
                        "真实身份": "真正想法",
                        "威胁": "危险",
                        "分析": "思考"
                    }
                    
                    for dangerous, safe in safe_replacements.items():
                        speech = speech.replace(dangerous, safe)
            
            # 移除括号内的内容（通常是策略分析）
            import re
            speech = re.sub(r'\([^)]*\)', '', speech)
            speech = re.sub(r'（[^）]*）', '', speech)
            speech = re.sub(r'\*\*[^*]*\*\*', '', speech)
            
            # 清理多余的空格和换行
            speech = ' '.join(speech.split())
            
            # 如果清理后发言过短或为空，返回默认发言
            if len(speech.strip()) < 10:
                return f"我觉得需要仔细观察每个人的行为，找出真正可疑的人。"
            
            return speech.strip()
            
        except Exception as e:
            # 如果过滤出错，返回安全的默认发言
            return f"我觉得大家都在认真思考，我们需要仔细分析局势。"

    def get_strategy_hint(self) -> str:
        """获取策略提示（用于调试）"""
        risk_level = self.analyze_risk_level({})
        
        strategy = f"狼人{self.player_id}的策略：\n"
        strategy += f"- 同伴：{self.teammates}\n"
        strategy += f"- 伪装策略：{self.disguise_strategy}\n"
        strategy += f"- 风险等级：{risk_level:.2f}\n"
        strategy += f"- 击杀优先级：{self.kill_priority[:3]}"
        
        return strategy 