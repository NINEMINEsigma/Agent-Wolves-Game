"""
预言家Agent实现
使用LlamaIndex Agent工具调用架构进行智能查验决策
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool

from ..base_agent import BaseGameAgent
from ..tools.seer_tools import SeerTools


class SeerAgent(BaseGameAgent):
    """预言家Agent类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], 
                 identity_system=None, memory_config=None):
        super().__init__(player_id, name, "seer", llm_interface, prompts, identity_system, memory_config)
        
        # 预言家特有属性
        self.vision_results = {}  # 查验结果 {player_id: role}
        self.revealed = False  # 是否已公开身份
        
        # 预言家已知信息
        self.role_info["known_werewolves"] = []
        self.role_info["known_villagers"] = []
        
        # 初始化工具函数
        self.seer_tools = SeerTools(self)
        
        # 创建Agent Runner
        self.agent_runner = self._create_agent_runner()
        
        self.logger.info(f"预言家Agent {player_id} 初始化完成")
    
    def register_tools(self) -> None:
        """注册预言家工具函数"""
        try:
            tools = self.seer_tools.get_tools()
            for tool in tools:
                self.add_tool(tool)
            self.logger.info(f"预言家{self.player_id}工具注册完成")
        except Exception as e:
            self.logger.error(f"注册预言家工具失败: {e}")
    
    def _create_agent_runner(self) -> Optional[AgentRunner]:
        """创建预言家Agent Runner"""
        try:
            # 暂时返回None，使用传统模式
            # TODO: 后续实现完整的Agent Runner
            self.logger.info("预言家Agent Runner暂未实现，使用传统模式")
            return None
            
        except Exception as e:
            self.logger.error(f"创建预言家Agent Runner失败: {e}")
            return None
    
    async def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """预言家夜晚查验行动（Agent模式）"""
        try:
            if not self.agent_runner:
                self.logger.warning("Agent Runner未初始化，使用传统模式")
                return await self._traditional_night_action(game_state)
            
            # 构建Agent提示
            agent_prompt = self._build_seer_agent_prompt(game_state)
            
            # 使用Agent进行决策（暂时使用传统方式）
            response = await self.llm_interface.generate_response(agent_prompt)
            
            # 解析Agent响应
            action_result = self._parse_agent_response(response, game_state)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": "divine",
                "target": action_result.get("target"),
                "player_id": self.player_id,
                "agent_response": str(response),
                "mode": "agent"
            })
            
            return action_result
            
        except Exception as e:
            self.logger.error(f"预言家Agent夜晚行动失败: {e}")
            # 回退到传统模式
            return await self._traditional_night_action(game_state)
    
    def _build_seer_agent_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建预言家Agent提示"""
        game_context = self.llm_interface.format_game_context(game_state)
        vision_results = self._format_vision_results()
        suspicion_info = self.format_suspicions()
        
        prompt = f"""
        你是预言家，现在是夜晚查验时间。
        
        当前游戏情况：
        {game_context}
        
        你的查验历史：
        {vision_results}
        
        你的怀疑情况：
        {suspicion_info}
        
        你的任务：
        1. 分析可疑玩家，选择查验目标
        2. 评估查验价值
        3. 执行查验行动
        
        请使用提供的工具函数来完成查验决策。优先查验最可疑的玩家。
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
                        "action": "divine",
                        "target": target_id,
                        "success": True,
                        "message": f"预言家Agent选择查验玩家{target_id}",
                        "agent_mode": True
                    }
            
            # 如果无法解析，返回默认决策
            return self._get_default_divine_decision(game_state)
            
        except Exception as e:
            self.logger.error(f"解析Agent响应失败: {e}")
            return self._get_default_divine_decision(game_state)
    
    def _get_default_divine_decision(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """获取默认查验决策"""
        # 选择最可疑的未查验玩家
        alive_players = [p["id"] for p in game_state.get("alive_players", []) 
                        if p["id"] != self.player_id]
        unverified_players = [p for p in alive_players 
                            if p not in self.vision_results]
        
        if not unverified_players:
            return {
                "action": "divine",
                "success": False,
                "message": "所有存活玩家都已查验过"
            }
        
        # 选择最可疑的玩家
        most_suspicious = self.get_most_suspicious_players(1)
        for suspect in most_suspicious:
            if suspect in unverified_players:
                return {
                    "action": "divine",
                    "target": suspect,
                    "success": True,
                    "message": f"预言家默认选择查验玩家{suspect}"
                }
        
        # 随机选择
        import random
        target = random.choice(unverified_players)
        return {
            "action": "divine",
            "target": target,
            "success": True,
            "message": f"预言家随机选择查验玩家{target}"
        }
    
    async def _traditional_night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """传统模式的夜晚行动（备用方案）"""
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
                "message": f"预言家（传统模式）选择查验玩家{divine_target}",
                "agent_mode": False
            }
            
        except Exception as e:
            self.logger.error(f"传统模式夜晚行动失败: {e}")
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
        import random
        return random.choice(candidates)
    
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """预言家发言（保持原有逻辑）"""
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
        """预言家投票（保持原有逻辑）"""
        try:
            valid_candidates = [c for c in candidates if c != self.player_id]
            if not valid_candidates:
                import random
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
            
            import random
            return random.choice(valid_candidates)
            
        except Exception as e:
            self.logger.error(f"预言家投票时出错: {e}")
            import random
            return random.choice([c for c in candidates if c != self.player_id])
    
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