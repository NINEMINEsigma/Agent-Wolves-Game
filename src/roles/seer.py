"""
预言家角色实现
预言家可以在夜晚查验玩家身份，是村民阵营的核心角色
"""

import random
from typing import Dict, Any, List
from ..ai_agent import BaseAIAgent


class Seer(BaseAIAgent):
    """预言家角色类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], identity_system=None, memory_config=None):
        super().__init__(player_id, name, "seer", llm_interface, prompts, identity_system, memory_config)
        
        # 预言家特有属性
        self.vision_results = {}  # 查验结果 {player_id: role}
        self.revealed = False  # 是否已公开身份
        
        # 预言家已知信息
        self.role_info["known_werewolves"] = []
        self.role_info["known_villagers"] = []
    
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """预言家发言"""
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
            
            请以玩家{self.player_id}号{self.name}的身份发言，运用你的个性特征和洞察力。
            """
            
            enhanced_role_context = self.get_enhanced_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                speech_prompt, enhanced_role_context
            )
            
            # 应用预言家专用过滤器
            filtered_response = self._filter_seer_speech(response)
            
            # 记录自己的发言
            self.update_memory("speeches", {
                "speaker": f"玩家{self.player_id}",
                "content": filtered_response,
                "speaker_id": self.player_id
            })
            
            return filtered_response
            
        except Exception as e:
            self.logger.error(f"预言家发言时出错: {e}")
            return f"我觉得需要仔细观察大家的行为模式。"
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """预言家投票"""
        try:
            valid_candidates = [c for c in candidates if c != self.player_id]
            if not valid_candidates:
                return random.choice(candidates)
            
            # 优先投票给已确认的狼人
            confirmed_werewolves = [p for p in valid_candidates 
                                  if self.vision_results.get(p) == "werewolf"]
            
            if confirmed_werewolves:
                return confirmed_werewolves[0]
            
            # 否则选择最可疑的玩家
            most_suspicious = self.get_most_suspicious_players(1)
            if most_suspicious and most_suspicious[0] in valid_candidates:
                return most_suspicious[0]
            
            return random.choice(valid_candidates)
            
        except Exception as e:
            self.logger.error(f"预言家投票时出错: {e}")
            return random.choice([c for c in candidates if c != self.player_id])
    
    async def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """预言家夜晚查验行动"""
        try:
            alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                           if p["id"] != self.player_id]
            
            # 排除已经查验过的玩家
            unverified_players = [p for p in alive_players 
                                if p not in self.vision_results]
            
            if not unverified_players:
                return {
                    "action": "divine",
                    "success": False,
                    "message": "所有存活玩家都已查验过"
                }
            
            # 选择查验目标
            divine_target = self._choose_divine_target(unverified_players, game_state)
            
            return {
                "action": "divine",
                "target": divine_target,
                "success": True,
                "message": f"预言家{self.player_id}选择查验玩家{divine_target}"
            }
            
        except Exception as e:
            self.logger.error(f"预言家夜晚行动时出错: {e}")
            return {
                "action": "divine",
                "success": False,
                "message": "查验行动失败"
            }
    
    def receive_vision_result(self, target_id: int, target_role: str):
        """接收查验结果"""
        self.vision_results[target_id] = target_role
        
        if target_role == "werewolf":
            self.role_info["known_werewolves"].append(target_id)
            self.update_suspicion(target_id, 1.0, f"查验确认为狼人")
        else:
            self.role_info["known_villagers"].append(target_id)
            self.update_suspicion(target_id, -1.0, f"查验确认为村民")
        
        self.logger.info(f"预言家{self.player_id}查验玩家{target_id}：{target_role}")
    
    def _format_vision_results(self) -> str:
        """格式化查验结果为文本"""
        if not self.vision_results:
            return "尚未进行查验"
        
        results = []
        for player_id, role in self.vision_results.items():
            role_desc = "狼人" if role == "werewolf" else "好人"
            results.append(f"玩家{player_id}({role_desc})")
        
        return "查验结果: " + ", ".join(results)
    
    def _choose_divine_target(self, candidates: List[int], game_state: Dict[str, Any]) -> int:
        """智能选择查验目标"""
        # 获取最可疑的玩家
        most_suspicious = self.get_most_suspicious_players(3)
        for suspect in most_suspicious:
            if suspect in candidates:
                return suspect
        
        # 如果没有明显可疑的，随机选择
        return random.choice(candidates) 

    def _filter_seer_speech(self, speech: str) -> str:
        """预言家发言专用过滤器"""
        # 基础过滤
        filtered = self._filter_speech_output(speech)
        
        # 预言家特定过滤
        seer_forbidden_words = [
            "预言家", "查验", "神", "预言", "天启", "洞察", "神职", "能力",
            "确认身份", "查明身份", "神圣", "启示", "真相", "探查", "验证",
            "狼人身份", "村民身份", "确定是", "我知道", "我看出", "发现了"
        ]
        
        for word in seer_forbidden_words:
            if word in filtered:
                filtered = filtered.replace(word, "")
        
        # 如果过滤后内容过短，返回安全默认内容
        if len(filtered.strip()) < 10:
            return "我觉得需要更仔细地观察大家的行为。"
        
        return filtered.strip() 