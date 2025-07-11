"""
村民Agent实现
使用LlamaIndex Agent工具调用架构进行智能推理决策
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.agent import AgentRunner
from llama_index.core.tools import FunctionTool

from ..base_agent import BaseGameAgent
from ..tools.common_tools import CommonTools


class VillagerAgent(BaseGameAgent):
    """村民Agent类"""
    
    def __init__(self, player_id: int, name: str, llm_interface, prompts: Dict[str, Any], 
                 identity_system=None, memory_config=None):
        super().__init__(player_id, name, "villager", llm_interface, prompts, identity_system, memory_config)
        
        # 村民特有属性
        self.confidence_level = 0.5  # 发言自信度
        self.voting_tendency = "logical"  # 投票倾向：logical, emotional, random
        
        # 初始化工具函数
        self.common_tools = CommonTools(self)
        
        # 在工具实例化完成后初始化Agent
        self.initialize_agent()
        
        self.logger.info(f"村民Agent {player_id} 初始化完成")
    
    def register_tools(self) -> None:
        """注册村民工具函数"""
        try:
            tools = self.common_tools.get_tools()
            for tool in tools:
                self.add_tool(tool)
            self.logger.info(f"村民{self.player_id}工具注册完成")
        except Exception as e:
            self.logger.error(f"注册村民工具失败: {e}")
    
    def _create_agent_runner(self) -> Optional[AgentRunner]:
        """创建村民Agent Runner"""
        try:
            # 使用父类的默认实现
            return super()._create_agent_runner()
            
        except Exception as e:
            self.logger.error(f"创建村民Agent Runner失败: {e}")
            return None
    
    async def night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """村民夜晚行动（Agent模式）"""
        try:
            if not self.agent_runner:
                self.logger.warning("Agent Runner未初始化，使用基础决策")
                return await self._basic_night_action(game_state)
            
            # 构建Agent提示
            agent_prompt = self._build_villager_agent_prompt(game_state)
            
            # 使用Agent进行决策（暂时使用传统方式）
            response = await self.llm_interface.generate_response(agent_prompt)
            
            # 解析Agent响应
            action_result = self._parse_agent_response(response, game_state)
            
            # 记录夜晚行动
            self.update_memory("night_actions", {
                "action": "reflect",
                "content": response,
                "player_id": self.player_id,
                "agent_response": str(response),
                "mode": "agent"
            })
            
            return action_result
            
        except Exception as e:
            self.logger.error(f"村民Agent夜晚行动失败: {e}")
            # 回退到基础决策
            return await self._basic_night_action(game_state)
    
    def _build_villager_agent_prompt(self, game_state: Dict[str, Any]) -> str:
        """构建村民Agent提示"""
        game_context = self.llm_interface.format_game_context(game_state)
        suspicion_info = self.format_suspicions()
        memory_context = self.format_memory_context()
        
        prompt = f"""
        你是村民，现在是夜晚反思时间。
        
        当前游戏情况：
        {game_context}
        
        你的怀疑情况：
        {suspicion_info}
        
        你的记忆：
        {memory_context}
        
        你的任务：
        1. 分析当天的情况
        2. 收集信息并推理
        3. 制定明天的策略
        4. 进行夜晚反思
        
        请使用提供的工具函数来进行深度分析和推理。作为村民，你需要通过逻辑推理找出狼人。
        """
        
        return prompt
    
    def _parse_agent_response(self, response, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """解析Agent响应"""
        try:
            # 从Agent响应中提取决策信息
            response_text = str(response)
            
            # 村民的夜晚行动主要是反思和分析
            return {
                "action": "reflect",
                "success": True,
                "message": f"村民Agent进行了夜晚反思和分析",
                "content": response_text,
                "agent_mode": True
            }
            
        except Exception as e:
            self.logger.error(f"解析Agent响应失败: {e}")
            return {
                "action": "reflect",
                "success": False,
                "message": "夜晚反思失败"
            }
    
    async def _basic_night_action(self, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """基础夜晚行动（备用方案）"""
        try:
            # 分析当天的情况
            analysis_prompt = f"""
            回顾今天的讨论和投票，作为村民，你有什么新的想法？
            
            当前游戏情况：
            {self.llm_interface.format_game_context(game_state)}
            
            你的怀疑情况：
            {self.format_suspicions()}
            
            今天的记忆：
            {self.format_memory_context(3)}
            
            请简短分析，对明天的策略有什么想法？
            """
            
            role_context = self.get_role_prompt("base_prompt")
            reflection = await self.llm_interface.generate_response(
                analysis_prompt, role_context
            )
            
            # 记录夜晚思考
            self.update_memory("night_actions", {
                "action": "reflection",
                "content": reflection,
                "player_id": self.player_id
            })
            
            # 基于反思调整怀疑度
            await self._adjust_suspicions_based_on_reflection(reflection)
            
            return {
                "action": "reflect",
                "success": True,
                "message": f"玩家{self.player_id}进行了夜晚反思"
            }
            
        except Exception as e:
            self.logger.error(f"基础夜晚行动失败: {e}")
            return {
                "action": "reflect",
                "success": False,
                "message": "夜晚反思失败"
            }
    
    async def _adjust_suspicions_based_on_reflection(self, reflection: str):
        """基于反思调整怀疑度"""
        try:
            # 这里可以实现更复杂的逻辑来解析反思内容并调整怀疑度
            import re
            
            # 寻找提到的玩家和情感词汇
            player_mentions = re.findall(r'玩家(\d+)', reflection)
            
            positive_words = ['相信', '信任', '无辜', '可靠', '真实']
            negative_words = ['怀疑', '可疑', '狡猾', '撒谎', '奇怪']
            
            for player_id_str in player_mentions:
                player_id = int(player_id_str)
                if player_id == self.player_id:
                    continue
                
                # 检查周围的词汇
                player_context = reflection.lower()
                
                # 简单的情感分析
                positive_score = sum(1 for word in positive_words if word in player_context)
                negative_score = sum(1 for word in negative_words if word in player_context)
                
                if positive_score > negative_score:
                    self.update_suspicion(player_id, -0.1, "夜晚反思 - 正面评价")
                elif negative_score > positive_score:
                    self.update_suspicion(player_id, 0.1, "夜晚反思 - 负面评价")
                    
        except Exception as e:
            self.logger.error(f"调整怀疑度时出错: {e}")
    
    async def make_speech(self, game_state: Dict[str, Any]) -> str:
        """村民发言（保持原有逻辑）"""
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
            
            请以玩家{self.player_id}号{self.name}的身份发表观点，体现你的个性特征和说话风格。
            表达怀疑或支持某些玩家时要保持逻辑性，不要过于冲动。
            """
            
            # 使用身份强化的角色上下文
            enhanced_role_context = self.get_enhanced_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                speech_prompt, enhanced_role_context
            )
            
            # 过滤输出内容
            filtered_response = self._filter_speech_output(response)
            
            # 记录自己的发言
            self.update_memory("speeches", {
                "speaker": f"玩家{self.player_id}",
                "content": filtered_response,
                "speaker_id": self.player_id
            })
            
            return filtered_response
            
        except Exception as e:
            self.logger.error(f"村民发言时出错: {e}")
            return f"我觉得需要更仔细地观察大家的行为。"
    
    async def vote(self, game_state: Dict[str, Any], candidates: List[int]) -> int:
        """村民投票（保持原有逻辑）"""
        try:
            # 移除自己
            valid_candidates = [c for c in candidates if c != self.player_id]
            if not valid_candidates:
                import random
                return random.choice(candidates)
            
            # 使用身份强化的投票提示
            identity_context = self.get_identity_context()
            enhanced_vote_prompt = self.get_enhanced_prompt("vote_prompt")
            game_context = self.llm_interface.format_game_context(game_state)
            suspicion_info = self.format_suspicions()
            
            candidate_info = ", ".join([f"玩家{c}" for c in valid_candidates])
            
            voting_prompt = f"""
            {identity_context}
            
            {enhanced_vote_prompt}
            
            当前游戏情况：
            {game_context}
            
            {suspicion_info}
            
            可投票的玩家：{candidate_info}
            
            请以玩家{self.player_id}号{self.name}的身份选择投票，体现你的个性和判断风格。
            选择一个玩家投票，并简单说明理由。
            格式：投票给玩家X，理由：XXXX
            """
            
            enhanced_role_context = self.get_enhanced_prompt("base_prompt")
            response = await self.llm_interface.generate_response(
                voting_prompt, enhanced_role_context
            )
            
            # 提取投票目标
            vote_target = self.llm_interface.extract_vote_choice(response, valid_candidates)
            
            if vote_target is None:
                # 基于怀疑度选择
                most_suspicious = self.get_most_suspicious_players(1)
                if most_suspicious and most_suspicious[0] in valid_candidates:
                    vote_target = most_suspicious[0]
                else:
                    import random
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
            self.logger.error(f"村民投票时出错: {e}")
            import random
            return random.choice([c for c in candidates if c != self.player_id]) if candidates else candidates[0]
    
    def analyze_voting_pattern(self, voting_results: Dict[int, int]):
        """分析投票模式"""
        # 分析谁投票给了谁，更新怀疑度
        for voter_id, target_id in voting_results.items():
            if voter_id == self.player_id:
                continue
            
            # 如果有人投票给自己怀疑的人，降低对投票者的怀疑
            if target_id in self.suspicions and self.suspicions[target_id] > 0.2:
                self.update_suspicion(voter_id, -0.05, "投票一致")
            
            # 如果有人投票给自己不怀疑的人，增加对投票者的怀疑
            elif target_id in self.suspicions and self.suspicions[target_id] < -0.1:
                self.update_suspicion(voter_id, 0.05, "投票不一致")
    
    def get_strategy_hint(self) -> str:
        """获取策略提示（用于调试）"""
        most_suspicious = self.get_most_suspicious_players(2)
        least_suspicious = self.get_least_suspicious_players(2)
        
        strategy = f"村民{self.player_id}的策略：\n"
        strategy += f"- 最怀疑：{most_suspicious}\n"
        strategy += f"- 最信任：{least_suspicious}\n"
        strategy += f"- 当前怀疑度分布：{dict(list(self.suspicions.items())[:5])}"
        
        return strategy 