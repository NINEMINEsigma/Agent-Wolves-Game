"""
女巫角色实现
女巫拥有解药和毒药各一瓶，在夜晚可以救人或杀人
"""

import random
from typing import Dict, Any, List, Optional
from ..ai_agent import BaseAIAgent


class Witch(BaseAIAgent):
    """女巫角色类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], identity_system=None, memory_config=None):
        super().__init__(player_id, name, "witch", llm_interface, prompts, identity_system, memory_config)
        
        # 女巫特有属性
        self.has_antidote = True  # 是否还有解药
        self.has_poison = True    # 是否还有毒药
        self.saved_players = []   # 救过的玩家
        self.poisoned_players = [] # 毒过的玩家
        self.last_night_death = None  # 昨晚死亡信息
        
        # 女巫策略
        self.save_strategy = "conservative"  # 救人策略：conservative, aggressive
        self.poison_strategy = "confirmed"   # 毒人策略：confirmed, suspicious
    
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """女巫发言"""
        try:
            # 使用身份强化的提示词
            identity_context = self.get_identity_context()
            enhanced_speech_prompt = self.get_enhanced_prompt("speech_prompt")
            game_context = self.llm_interface.format_game_context(game_state)
            memory_context = self.format_memory_context()
            suspicion_info = self.format_suspicions()
            
            speech_prompt = f"""
            {identity_context}
            
            {enhanced_speech_prompt}
            
            当前游戏情况：
            {game_context}
            
            你的记忆：
            {memory_context}
            
            {suspicion_info}
            
            请以玩家{self.player_id}号{self.name}的身份发言，运用你的个性特征和智慧。
            """
            
            enhanced_role_context = self.get_enhanced_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                speech_prompt, enhanced_role_context
            )
            
            # 应用女巫专用过滤器
            filtered_response = self._filter_witch_speech(response)
            
            # 记录自己的发言
            self.update_memory("speeches", {
                "speaker": f"玩家{self.player_id}",
                "content": filtered_response,
                "speaker_id": self.player_id
            })
            
            return filtered_response
            
        except Exception as e:
            self.logger.error(f"女巫发言时出错: {e}")
            return f"我觉得需要更谨慎地分析局势。"
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """女巫投票"""
        try:
            valid_candidates = [c for c in candidates if c != self.player_id]
            if not valid_candidates:
                return random.choice(candidates)
            
            vote_prompt = self.get_role_prompt("vote_prompt")
            game_context = self.llm_interface.format_game_context(game_state)
            suspicion_info = self.format_suspicions()
            potion_info = self._format_potion_status()
            
            candidate_info = ", ".join([f"玩家{c}" for c in valid_candidates])
            
            voting_prompt = f"""
            {vote_prompt}
            
            当前游戏情况：
            {game_context}
            
            {suspicion_info}
            
            你的药剂状态：
            {potion_info}
            
            可投票的玩家：{candidate_info}
            
            作为女巫，基于你的观察和可能的药剂使用经验投票。
            格式：投票给玩家X，理由：XXXX
            """
            
            role_context = self.get_role_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                voting_prompt, role_context
            )
            
            # 提取投票目标
            vote_target = self.llm_interface.extract_vote_choice(response, valid_candidates)
            
            if vote_target is None:
                # 基于怀疑度选择
                most_suspicious = self.get_most_suspicious_players(1)
                if most_suspicious and most_suspicious[0] in valid_candidates:
                    vote_target = most_suspicious[0]
                else:
                    vote_target = random.choice(valid_candidates)
            
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
            self.logger.error(f"女巫投票时出错: {e}")
            return random.choice([c for c in candidates if c != self.player_id])
    
    async def night_action(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """女巫夜晚行动"""
        try:
            self.last_night_death = death_info
            
            # 如果没有任何药剂，无法行动
            if not self.has_antidote and not self.has_poison:
                return {
                    "action": "no_action",
                    "success": True,
                    "message": f"女巫{self.player_id}没有可用的药剂"
                }
            
            # 构建行动决策提示
            action_prompt = self._build_night_action_prompt(game_state, death_info)
            
            role_context = self.get_role_prompt("base_prompt")
            response = await self.llm_interface.generate_response(action_prompt, role_context)
            
            # 解析女巫的决策
            action_result = self._parse_witch_action(response, death_info)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": action_result["action"],
                "target": action_result.get("target"),
                "player_id": self.player_id,
                "reason": response
            })
            
            return action_result
            
        except Exception as e:
            self.logger.error(f"女巫夜晚行动时出错: {e}")
            return {
                "action": "no_action",
                "success": False,
                "message": "女巫行动失败"
            }
    
    def _build_night_action_prompt(self, game_state: Dict[str, Any], death_info: Optional[Dict[str, Any]]) -> str:
        """构建夜晚行动提示"""
        save_prompt = self.get_role_prompt("save_prompt")
        poison_prompt = self.get_role_prompt("poison_prompt")
        
        game_context = self.llm_interface.format_game_context(game_state)
        potion_status = self._format_potion_status()
        
        # 死亡信息 - 只有有解药时才显示死亡信息
        death_text = "无人死亡"
        if death_info and death_info.get("target") and self.has_antidote:
            death_text = f"玩家{death_info['target']}被狼人击杀"
        elif death_info and death_info.get("target") and not self.has_antidote:
            death_text = "死亡情况未知（你已无解药）"
        
        # 可用行动
        available_actions = []
        if self.has_antidote and death_info and death_info.get("target"):
            available_actions.append("1) 使用解药救活被杀玩家")
        if self.has_poison:
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.player_id]
            if alive_players:
                available_actions.append("2) 使用毒药毒死一名玩家")
        available_actions.append("3) 不使用任何药剂")
        
        action_list = "\n".join(available_actions)
        
        prompt = f"""
        你是女巫，现在是夜晚行动时间。
        
        【重要】你的药剂状态：
        {potion_status}
        
        当前游戏情况：
        {game_context}
        
        今晚死亡情况：{death_text}
        
        可用行动：
        {action_list}
        
        解药使用指导：{save_prompt}
        毒药使用指导：{poison_prompt}
        
        你的怀疑情况：{self.format_suspicions()}
        
        【决策要求】：
        基于你的药剂状态和当前局势，请做出明智的药剂使用决策。
        如果使用药剂，请指明目标玩家。
        格式：选择行动X，目标：玩家Y（如适用），理由：XXXX
        """
        
        return prompt
    
    def _parse_witch_action(self, response: str, death_info: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """解析女巫的行动决策"""
        response_lower = response.lower()
        
        # 检查是否使用解药
        if self.has_antidote and "解药" in response and death_info and death_info.get("target"):
            target = death_info["target"]
            self.has_antidote = False
            self.saved_players.append(target)
            return {
                "action": "save",
                "target": target,
                "success": True,
                "message": f"女巫{self.player_id}使用解药救活玩家{target}"
            }
        
        # 检查是否使用毒药
        if self.has_poison and "毒药" in response:
            # 尝试提取目标
            import re
            player_matches = re.findall(r'玩家(\d+)', response)
            if player_matches:
                target = int(player_matches[0])
                if target != self.player_id:  # 不能毒自己
                    self.has_poison = False
                    self.poisoned_players.append(target)
                    return {
                        "action": "poison",
                        "target": target,
                        "success": True,
                        "message": f"女巫{self.player_id}使用毒药毒死玩家{target}"
                    }
        
        # 默认不使用药剂
        return {
            "action": "no_action",
            "success": True,
            "message": f"女巫{self.player_id}选择不使用药剂"
        }
    
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
    
    def should_save_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该救某个玩家"""
        # 不救自己（通常女巫不会被告知自己被杀）
        if target_id == self.player_id:
            return False
        
        # 如果是可信任的玩家，倾向于救
        if target_id in self.suspicions and self.suspicions[target_id] < -0.3:
            return True
        
        # 如果是高度怀疑的玩家，不救
        if target_id in self.suspicions and self.suspicions[target_id] > 0.5:
            return False
        
        # 根据策略决定
        if self.save_strategy == "conservative":
            return random.random() < 0.3  # 保守策略，30%概率救人
        else:
            return random.random() < 0.7  # 积极策略，70%概率救人
    
    def should_poison_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该毒某个玩家"""
        # 不毒自己
        if target_id == self.player_id:
            return False
        
        # 如果高度怀疑，考虑使用毒药
        if target_id in self.suspicions and self.suspicions[target_id] > 0.7:
            return True
        
        return False
    
    def get_recommended_poison_target(self, game_state: Dict[str, Any]) -> Optional[int]:
        """获取推荐的毒杀目标"""
        alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                        if p["id"] != self.player_id]
        
        # 选择最可疑的玩家
        most_suspicious = self.get_most_suspicious_players(1)
        if most_suspicious and most_suspicious[0] in alive_players:
            if self.suspicions.get(most_suspicious[0], 0) > 0.6:
                return most_suspicious[0]
        
        return None
    
    def analyze_night_deaths(self, deaths: List[Dict[str, Any]]):
        """分析夜晚死亡情况"""
        for death in deaths:
            target_id = death.get("target")
            cause = death.get("cause", "")
            
            if cause == "werewolf_kill":
                # 狼人击杀，可能需要救人
                pass
            elif cause == "witch_poison":
                # 女巫毒杀，分析是否合理
                if target_id in self.poisoned_players:
                    self.logger.info(f"确认毒杀玩家{target_id}成功")
    
    def get_strategy_hint(self) -> str:
        """获取女巫策略提示"""
        hint = f"女巫{self.player_id}策略提示：\n"
        
        if self.has_antidote:
            hint += "- 还有解药，谨慎使用\n"
        else:
            hint += "- 解药已用完\n"
        
        if self.has_poison:
            hint += "- 还有毒药，寻找确认狼人\n"
        else:
            hint += "- 毒药已用完\n"
        
        return hint
    
    def _filter_witch_speech(self, speech: str) -> str:
        """女巫发言专用过滤器"""
        # 基础过滤
        filtered = self._filter_speech_output(speech)
        
        # 女巫特定过滤
        witch_forbidden_words = [
            "女巫", "药剂", "解药", "毒药", "救", "毒", "药", "治疗", "毒杀",
            "能力", "神职", "魔法", "神秘", "药水", "解毒", "毒死", "救活",
            "昨晚死的", "昨晚被杀", "我救了", "我毒了", "没救", "用了解药", "用了毒药"
        ]
        
        for word in witch_forbidden_words:
            if word in filtered:
                filtered = filtered.replace(word, "")
        
        # 如果过滤后内容过短，返回安全默认内容
        if len(filtered.strip()) < 10:
            return "我觉得需要更谨慎地分析局势。"
        
        return filtered.strip() 