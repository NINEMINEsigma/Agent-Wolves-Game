"""
狼人协作模块
实现狼人多智能体间的协作、讨论和群体决策机制
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
import random


class WerewolfCooperationSystem:
    """狼人协作系统"""
    
    def __init__(self, game_state, logger=None):
        """
        初始化狼人协作系统
        
        Args:
            game_state: 游戏状态
            logger: 日志记录器
        """
        self.game_state = game_state
        self.logger = logger or logging.getLogger(__name__)
        
        # 目标优先级策略
        self.target_priority = {
            "seer": 10,        # 预言家 - 最高优先级
            "witch": 8,        # 女巫 - 高优先级
            "villager": 5,     # 普通村民 - 中等优先级
        }
        
        # 威胁度评估因子
        self.threat_factors = {
            "speech_logic": 3,      # 发言逻辑性
            "suspicion_accuracy": 4, # 怀疑准确度
            "influence": 2,         # 影响力
            "survival_rounds": 1,   # 存活轮次
        }
    
    async def conduct_werewolf_discussion(self, werewolves: List, game_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        进行狼人群体讨论
        
        Args:
            werewolves: 存活狼人列表
            game_state_dict: 游戏状态
            
        Returns:
            讨论结果和击杀决定
        """
        if not werewolves:
            return {"success": False, "message": "没有存活的狼人"}
        
        if len(werewolves) == 1:
            # 只有一个狼人时，直接决定
            return await self._single_werewolf_decision(werewolves[0], game_state_dict)
        
        self.logger.info(f"开始狼人群体讨论，参与者：{[w.player_id for w in werewolves]}")
        
        # 1. 分析可选目标
        potential_targets = self._analyze_potential_targets(werewolves, game_state_dict)
        
        if not potential_targets:
            return {"success": False, "message": "没有可击杀的目标"}
        
        # 2. 狼人夜晚群体对话交流
        discussion_transcript = await self._conduct_werewolf_dialogue(werewolves, potential_targets, game_state_dict)
        
        # 3. 基于对话结果进行最终投票决定
        final_decision = await self._werewolf_final_vote_after_discussion(werewolves, discussion_transcript, potential_targets, game_state_dict)
        
        return final_decision
    
    async def _single_werewolf_decision(self, werewolf, game_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """单个狼人的决策"""
        try:
            potential_targets = self._analyze_potential_targets([werewolf], game_state_dict)
            
            if not potential_targets:
                return {"success": False, "message": "没有可击杀的目标"}
            
            # 选择最优目标
            target_id = self._select_optimal_target(potential_targets, werewolf)
            
            return {
                "success": True,
                "target": target_id,
                "decision_type": "single_werewolf",
                "reasoning": f"单独狼人选择击杀威胁最大的目标：玩家{target_id}"
            }
            
        except Exception as e:
            self.logger.error(f"单个狼人决策异常: {e}")
            return {"success": False, "message": "狼人决策失败"}
    
    def _analyze_potential_targets(self, werewolves: List, game_state_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析潜在击杀目标"""
        alive_players = game_state_dict.get("alive_players", [])
        werewolf_ids = [w.player_id for w in werewolves]
        
        targets = []
        for player in alive_players:
            player_id = player["id"]
            
            # 排除狼人自己
            if player_id in werewolf_ids:
                continue
            
            # 分析目标威胁度
            threat_score = self._calculate_threat_score(player, game_state_dict, werewolves)
            
            targets.append({
                "id": player_id,
                "name": player["name"],
                "threat_score": threat_score,
                "estimated_role": self._estimate_player_role(player, game_state_dict, werewolves),
                "analysis": self._generate_target_analysis(player, game_state_dict, werewolves)
            })
        
        # 按威胁度排序
        targets.sort(key=lambda x: x["threat_score"], reverse=True)
        return targets
    
    def _calculate_threat_score(self, player: Dict[str, Any], game_state_dict: Dict[str, Any], werewolves: List) -> float:
        """计算玩家威胁度分数"""
        base_score = 0.0
        player_id = player["id"]
        
        # 1. 基于估计角色的基础分数
        estimated_role = self._estimate_player_role(player, game_state_dict, werewolves)
        base_score += self.target_priority.get(estimated_role, 3)
        
        # 2. 分析发言逻辑性
        speech_logic_score = self._analyze_speech_logic(player_id, game_state_dict)
        base_score += speech_logic_score * self.threat_factors["speech_logic"]
        
        # 3. 分析怀疑准确度
        suspicion_score = self._analyze_suspicion_accuracy(player_id, werewolves)
        base_score += suspicion_score * self.threat_factors["suspicion_accuracy"]
        
        # 4. 影响力评估
        influence_score = self._analyze_influence(player_id, game_state_dict)
        base_score += influence_score * self.threat_factors["influence"]
        
        # 5. 存活时间
        survival_score = game_state_dict.get("current_round", 1) * self.threat_factors["survival_rounds"]
        base_score += survival_score
        
        return round(base_score, 2)
    
    def _estimate_player_role(self, player: Dict[str, Any], game_state_dict: Dict[str, Any], werewolves: List) -> str:
        """估计玩家角色"""
        # 基于行为模式和发言内容推测角色
        # 这里简化实现，实际可以更复杂的分析
        
        player_id = player["id"]
        
        # 检查是否有预言家特征
        if self._has_seer_characteristics(player_id, game_state_dict):
            return "seer"
        
        # 检查是否有女巫特征
        if self._has_witch_characteristics(player_id, game_state_dict):
            return "witch"
        
        # 默认为村民
        return "villager"
    
    def _has_seer_characteristics(self, player_id: int, game_state_dict: Dict[str, Any]) -> bool:
        """检查是否有预言家特征"""
        # 分析发言中是否有暗示查验结果的内容
        # 这里简化实现
        recent_speeches = game_state_dict.get("recent_speeches", [])
        
        for speech in recent_speeches:
            if speech.get("speaker_id") == player_id:
                content = speech.get("content", "").lower()
                # 查找预言家关键词
                seer_keywords = ["查验", "确认", "身份", "预言", "看到", "检测"]
                if any(keyword in content for keyword in seer_keywords):
                    return True
        return False
    
    def _has_witch_characteristics(self, player_id: int, game_state_dict: Dict[str, Any]) -> bool:
        """检查是否有女巫特征"""
        # 分析是否有女巫相关的发言模式
        recent_speeches = game_state_dict.get("recent_speeches", [])
        
        for speech in recent_speeches:
            if speech.get("speaker_id") == player_id:
                content = speech.get("content", "").lower()
                # 查找女巫关键词
                witch_keywords = ["救", "毒", "药", "女巫", "昨晚", "死亡"]
                if any(keyword in content for keyword in witch_keywords):
                    return True
        return False
    
    def _analyze_speech_logic(self, player_id: int, game_state_dict: Dict[str, Any]) -> float:
        """分析发言逻辑性（0-1）"""
        recent_speeches = game_state_dict.get("recent_speeches", [])
        
        player_speeches = [s for s in recent_speeches if s.get("speaker_id") == player_id]
        
        if not player_speeches:
            return 0.3  # 没有发言的默认分数
        
        # 简化的逻辑性评估
        total_logic_score = 0.0
        
        for speech in player_speeches:
            content = speech.get("content", "")
            
            # 基于关键词评估逻辑性
            logic_indicators = ["因为", "所以", "根据", "分析", "推断", "逻辑", "证据"]
            logic_score = sum(1 for indicator in logic_indicators if indicator in content)
            logic_score = min(logic_score / len(logic_indicators), 1.0)
            
            total_logic_score += logic_score
        
        return total_logic_score / len(player_speeches)
    
    def _analyze_suspicion_accuracy(self, player_id: int, werewolves: List) -> float:
        """分析怀疑准确度（0-1）"""
        # 检查该玩家是否对狼人产生了准确的怀疑
        werewolf_ids = [w.player_id for w in werewolves]
        
        # 简化实现：如果该玩家的怀疑对象中包含狼人，说明有一定准确度
        for werewolf in werewolves:
            if hasattr(werewolf, 'suspicions') and player_id in werewolf.suspicions:
                # 如果狼人对这个玩家有高怀疑，说明这个玩家可能对狼人有准确怀疑
                if werewolf.suspicions[player_id] > 0.5:
                    return 0.8
        
        return 0.3  # 默认中等准确度
    
    def _analyze_influence(self, player_id: int, game_state_dict: Dict[str, Any]) -> float:
        """分析玩家影响力（0-1）"""
        recent_speeches = game_state_dict.get("recent_speeches", [])
        
        # 基于发言频率和内容质量评估影响力
        player_speeches = [s for s in recent_speeches if s.get("speaker_id") == player_id]
        
        if not player_speeches:
            return 0.2
        
        # 发言频率
        speech_frequency = len(player_speeches) / max(len(recent_speeches), 1)
        
        # 发言长度（间接反映参与度）
        avg_speech_length = sum(len(s.get("content", "")) for s in player_speeches) / len(player_speeches)
        length_score = min(avg_speech_length / 100, 1.0)  # 归一化到0-1
        
        influence_score = (speech_frequency * 0.6 + length_score * 0.4)
        return min(influence_score, 1.0)
    
    def _generate_target_analysis(self, player: Dict[str, Any], game_state_dict: Dict[str, Any], werewolves: List) -> str:
        """生成目标分析报告"""
        player_id = player["id"]
        estimated_role = self._estimate_player_role(player, game_state_dict, werewolves)
        threat_score = self._calculate_threat_score(player, game_state_dict, werewolves)
        
        analysis = f"玩家{player_id}({player['name']}) - "
        analysis += f"估计角色：{estimated_role}, "
        analysis += f"威胁度：{threat_score:.1f}, "
        
        if estimated_role == "seer":
            analysis += "疑似预言家，优先击杀"
        elif estimated_role == "witch":
            analysis += "疑似女巫，高优先级"
        else:
            analysis += "普通村民，基于威胁度决定"
        
        return analysis
    
    async def _get_werewolf_suggestion(self, werewolf, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """获取单个狼人的建议"""
        try:
            # 为每个目标评分
            werewolf_scores = {}
            
            for target in targets[:5]:  # 只考虑前5个高威胁目标
                target_id = target["id"]
                
                # 基础威胁分数
                base_score = target["threat_score"]
                
                # 个人偏好调整（如果狼人有特定的怀疑目标）
                personal_adjustment = 0
                if hasattr(werewolf, 'suspicions') and target_id in werewolf.suspicions:
                    # 如果这个目标对狼人的怀疑度高，优先击杀
                    suspicion_level = werewolf.suspicions.get(target_id, 0)
                    if suspicion_level > 0.6:
                        personal_adjustment += 3
                
                final_score = base_score + personal_adjustment
                werewolf_scores[target_id] = final_score
            
            # 选择最高分的目标
            if werewolf_scores:
                suggested_target = max(werewolf_scores.items(), key=lambda x: x[1])
                target_id, score = suggested_target
                
                target_info = next(t for t in targets if t["id"] == target_id)
                
                return {
                    "werewolf_id": werewolf.player_id,
                    "suggested_target": target_id,
                    "score": score,
                    "reasoning": f"狼人{werewolf.player_id}建议击杀{target_info['name']}（{target_info['analysis']}）"
                }
            
            return {
                "werewolf_id": werewolf.player_id,
                "suggested_target": None,
                "score": 0,
                "reasoning": "没有合适的击杀目标"
            }
            
        except Exception as e:
            self.logger.error(f"狼人{werewolf.player_id}提出建议时出错: {e}")
            return {
                "werewolf_id": werewolf.player_id,
                "suggested_target": None,
                "score": 0,
                "reasoning": "建议生成失败"
            }
    
    async def _conduct_werewolf_dialogue(self, werewolves: List, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        进行狼人夜晚群体对话
        
        Args:
            werewolves: 狼人列表
            targets: 潜在目标列表
            game_state_dict: 游戏状态
            
        Returns:
            对话记录
        """
        dialogue_history = []
        current_round = game_state_dict.get("current_round", 1)
        
        print(f"\n💬 狼人夜晚私密对话开始...")
        print(f"🌙 月黑风高，狼人们开始密谋...")
        
        # 第一轮：每个狼人发表初步看法
        print(f"\n📢 第一轮讨论：初步分析")
        for i, werewolf in enumerate(werewolves):
            speech = await self._generate_werewolf_opening_statement(werewolf, targets, game_state_dict, dialogue_history)
            
            dialogue_entry = {
                "round": current_round,
                "discussion_round": 1,
                "speaker_id": werewolf.player_id,
                "speaker_name": werewolf.name,
                "content": speech,
                "speech_type": "opening_analysis",
                "context": "狼人夜晚群体讨论"
            }
            dialogue_history.append(dialogue_entry)
            
            # 为所有狼人更新夜晚讨论记忆
            for w in werewolves:
                w.update_night_discussion_memory(dialogue_entry)
            
            print(f"🐺 {werewolf.name}: {speech}")
            await asyncio.sleep(0.1)  # 模拟思考时间
        
        # 第二轮：针对他人观点进行回应和辩论
        if len(werewolves) > 2:  # 3个或以上狼人才进行辩论轮
            print(f"\n🔥 第二轮讨论：深入辩论")
            for werewolf in werewolves:
                response_speech = await self._generate_werewolf_response(werewolf, dialogue_history, targets, game_state_dict)
                
                dialogue_entry = {
                    "round": current_round,
                    "discussion_round": 2,
                    "speaker_id": werewolf.player_id,
                    "speaker_name": werewolf.name,
                    "content": response_speech,
                    "speech_type": "response_debate",
                    "context": "狼人夜晚群体讨论"
                }
                dialogue_history.append(dialogue_entry)
                
                # 为所有狼人更新夜晚讨论记忆
                for w in werewolves:
                    w.update_night_discussion_memory(dialogue_entry)
                
                print(f"🐺 {werewolf.name}(玩家{werewolf.player_id}): {response_speech}")
                await asyncio.sleep(0.5)
        
        # 第三轮：最终立场和建议
        print(f"\n🎯 第三轮讨论：最终决策")
        for werewolf in werewolves:
            final_speech = await self._generate_werewolf_final_statement(werewolf, dialogue_history, targets, game_state_dict)
            
            dialogue_entry = {
                "round": current_round,
                "discussion_round": 3,
                "speaker_id": werewolf.player_id,
                "speaker_name": werewolf.name,
                "content": final_speech,
                "speech_type": "final_decision",
                "context": "狼人夜晚群体讨论"
            }
            dialogue_history.append(dialogue_entry)
            
            # 为所有狼人更新夜晚讨论记忆
            for w in werewolves:
                w.update_night_discussion_memory(dialogue_entry)
            
            print(f"🐺 {werewolf.name}(玩家{werewolf.player_id}): {final_speech}")
            await asyncio.sleep(0.5)
        
        print(f"\n✅ 狼人群体对话结束，共{len(dialogue_history)}条发言")
        return dialogue_history
    
    async def _generate_werewolf_opening_statement(self, werewolf, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any], dialogue_history: List) -> str:
        """生成狼人开场发言"""
        try:
            # 选择前3个最高威胁目标进行分析
            top_targets = targets[:3]
            target_analysis = "\n".join([f"- {t['analysis']}" for t in top_targets])
            
            current_round = game_state_dict.get("current_round", 1)
            alive_count = len(game_state_dict.get("alive_players", []))
            
            prompt = f"""
            你是狼人{werewolf.player_id}({werewolf.name})，现在是第{current_round}轮的夜晚。
            你正在与其他狼人同伴进行秘密商讨今晚的击杀目标。
            
            当前游戏状况：
            - 存活玩家数：{alive_count}人
            - 当前轮次：第{current_round}轮
            
            潜在击杀目标分析：
            {target_analysis}
            
            作为狼人团队的一员，请发表你对今晚击杀目标的初步看法和分析。
            你需要：
            1. 分析当前形势对狼人的利弊
            2. 提出你认为最优的击杀目标
            3. 说明你的理由和策略考虑
            
            发言风格要像狼人在夜晚密谋，简洁而有策略性。
            """
            
            # 使用狼人的LLM接口生成发言
            if hasattr(werewolf, 'llm_interface'):
                response = await werewolf.llm_interface.generate_response(prompt, "你是一个狡猾的狼人，正在与同伴商讨击杀策略。")
                return response.strip()
            else:
                # 备用简化发言
                if top_targets:
                    return f"我建议优先考虑{top_targets[0]['name']}，威胁度最高。大家觉得如何？"
                return "当前形势下我们需要谨慎选择目标。"
                
        except Exception as e:
            self.logger.error(f"狼人{werewolf.player_id}生成开场发言时出错: {e}")
            return "我需要仔细考虑一下当前的情况..."
    
    async def _generate_werewolf_response(self, werewolf, dialogue_history: List, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any]) -> str:
        """生成狼人回应发言"""
        try:
            # 获取其他狼人的发言
            other_speeches = [entry for entry in dialogue_history 
                            if entry["speaker_id"] != werewolf.player_id and entry["round"] == 1]
            
            if not other_speeches:
                return "我赞同大家的分析。"
            
            other_opinions = "\n".join([f"- {speech['speaker_name']}: {speech['content']}" 
                                      for speech in other_speeches])
            
            prompt = f"""
            你是狼人{werewolf.player_id}({werewolf.name})，刚才听到了其他狼人同伴的看法：
            
            同伴们的观点：
            {other_opinions}
            
            现在请你回应同伴们的观点，你可以：
            1. 表示赞同某个同伴的建议
            2. 提出不同的看法或补充分析
            3. 指出某个策略的风险或优势
            4. 建议调整击杀策略
            
            保持狼人角色，发言要有逻辑且体现团队合作精神。
            """
            
            if hasattr(werewolf, 'llm_interface'):
                response = await werewolf.llm_interface.generate_response(prompt, "你是一个善于分析的狼人，正在回应同伴的策略建议。")
                return response.strip()
            else:
                # 备用回应
                return f"我觉得{other_speeches[0]['speaker_name']}的分析很有道理，我们应该考虑这个建议。"
                
        except Exception as e:
            self.logger.error(f"狼人{werewolf.player_id}生成回应发言时出错: {e}")
            return "我同意大家的看法。"
    
    async def _generate_werewolf_final_statement(self, werewolf, dialogue_history: List, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any]) -> str:
        """生成狼人最终决策发言"""
        try:
            # 分析整个对话历史
            all_previous_speeches = [entry for entry in dialogue_history 
                                   if entry["speaker_id"] != werewolf.player_id]
            
            discussion_summary = "\n".join([f"- {speech['speaker_name']}: {speech['content']}" 
                                          for speech in all_previous_speeches[-4:]])  # 最近4条发言
            
            top_targets = targets[:3]
            target_options = ", ".join([f"{t['name']}(威胁度{t['threat_score']:.1f})" for t in top_targets])
            
            prompt = f"""
            你是狼人{werewolf.player_id}({werewolf.name})，经过了充分的团队讨论，现在需要表明你的最终立场。
            
            之前的讨论要点：
            {discussion_summary}
            
            候选目标：{target_options}
            
            作为最终发言，请明确表态：
            1. 你最终支持击杀哪个目标
            2. 简述选择这个目标的核心原因
            3. 表达对团队决策的态度
            
            这是决策性发言，要明确而坚定。
            """
            
            if hasattr(werewolf, 'llm_interface'):
                response = await werewolf.llm_interface.generate_response(prompt, "你是一个果断的狼人领袖，正在做最终决策。")
                return response.strip()
            else:
                # 备用最终发言
                if top_targets:
                    return f"经过讨论，我最终支持击杀{top_targets[0]['name']}。这是我们的最佳选择。"
                return "我支持团队的集体决策。"
                
        except Exception as e:
            self.logger.error(f"狼人{werewolf.player_id}生成最终发言时出错: {e}")
            return "我支持大家的决定。"
    
    async def _werewolf_final_vote_after_discussion(self, werewolves: List, dialogue_history: List, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """基于对话历史进行最终投票"""
        print(f"\n🗳️ 狼人群体最终投票开始...")
        
        # 分析对话中提到的目标偏好
        target_mentions = self._analyze_target_preferences_from_dialogue(dialogue_history, targets)
        
        # 每个狼人基于对话历史进行最终投票
        votes = {}
        vote_details = []
        
        for werewolf in werewolves:
            vote_target = await self._get_werewolf_final_vote(werewolf, dialogue_history, targets, target_mentions)
            
            if vote_target:
                votes[vote_target] = votes.get(vote_target, 0) + 1
                target_name = next((t['name'] for t in targets if t['id'] == vote_target), f"玩家{vote_target}")
                vote_details.append(f"🐺 {werewolf.name} → {target_name}")
                print(f"🐺 {werewolf.name}(玩家{werewolf.player_id}) 投票给: {target_name}")
        
        # 确定最终结果
        if not votes:
            return {"success": False, "message": "狼人投票失败"}
        
        max_votes = max(votes.values())
        winners = [target for target, vote_count in votes.items() if vote_count == max_votes]
        
        if len(winners) == 1:
            final_target = winners[0]
        else:
            # 平票时选择威胁度最高的
            final_target = self._resolve_werewolf_tie(winners, game_state_dict)
        
        target_name = next((t['name'] for t in targets if t['id'] == final_target), f"玩家{final_target}")
        
        print(f"\n🎯 投票结果：")
        for target_id, vote_count in votes.items():
            t_name = next((t['name'] for t in targets if t['id'] == target_id), f"玩家{target_id}")
            print(f"  {t_name}: {vote_count}票")
        
        print(f"\n✅ 狼人群体决定：击杀 {target_name}！")
        
        return {
            "success": True,
            "target": final_target,
            "decision_type": "group_discussion_vote",
            "votes": votes,
            "vote_details": vote_details,
            "dialogue_history": dialogue_history,
            "reasoning": f"经过{len(dialogue_history)}轮群体讨论后，狼人投票决定击杀{target_name}"
        }
    
    def _analyze_target_preferences_from_dialogue(self, dialogue_history: List, targets: List[Dict[str, Any]]) -> Dict[int, int]:
        """分析对话中对目标的偏好提及"""
        target_mentions = {}
        
        # 创建目标名称到ID的映射
        name_to_id = {t['name']: t['id'] for t in targets}
        
        for entry in dialogue_history:
            content = entry['content'].lower()
            
            # 检查是否提到了特定目标
            for target_name, target_id in name_to_id.items():
                if target_name.lower() in content or f"玩家{target_id}" in content:
                    target_mentions[target_id] = target_mentions.get(target_id, 0) + 1
                    
                    # 分析提及的情感倾向（简化实现）
                    positive_words = ["建议", "支持", "击杀", "选择", "优先"]
                    if any(word in content for word in positive_words):
                        target_mentions[target_id] += 1  # 积极提及加权
        
        return target_mentions
    
    async def _get_werewolf_final_vote(self, werewolf, dialogue_history: List, targets: List[Dict[str, Any]], target_mentions: Dict[int, int]) -> Optional[int]:
        """获取狼人的最终投票选择"""
        try:
            # 基于对话历史和目标提及频率做决策
            
            # 1. 优先考虑在对话中被多次积极提及的目标
            if target_mentions:
                most_mentioned = max(target_mentions.items(), key=lambda x: x[1])
                if most_mentioned[1] >= 2:  # 被提及2次以上
                    return most_mentioned[0]
            
            # 2. 基于威胁度选择
            if targets:
                # 选择威胁度最高的前3个中的一个
                top_targets = targets[:3]
                
                # 加入一些随机性，避免所有狼人都选同一个
                import random
                weights = [3, 2, 1][:len(top_targets)]  # 威胁度高的权重更大
                chosen_target = random.choices(top_targets, weights=weights)[0]
                return chosen_target['id']
            
            return None
            
        except Exception as e:
            self.logger.error(f"获取狼人{werewolf.player_id}最终投票时出错: {e}")
            return targets[0]['id'] if targets else None
    
    def _resolve_werewolf_tie(self, tied_targets: List[int], game_state_dict: Dict[str, Any]) -> int:
        """解决狼人投票平票"""
        # 基于威胁度选择
        target_threats = {}
        
        for target_id in tied_targets:
            player = next((p for p in game_state_dict.get("alive_players", []) if p["id"] == target_id), None)
            if player:
                threat_score = self._calculate_threat_score(player, game_state_dict, [])
                target_threats[target_id] = threat_score
        
        if target_threats:
            return max(target_threats.items(), key=lambda x: x[1])[0]
        
        return random.choice(tied_targets)
    
    def _select_optimal_target(self, targets: List[Dict[str, Any]], werewolf) -> Optional[int]:
        """为单个狼人选择最优目标"""
        if not targets:
            return None
        
        # 选择威胁度最高的目标
        best_target = max(targets, key=lambda x: x["threat_score"])
        return best_target["id"] 