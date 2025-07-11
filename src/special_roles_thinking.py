"""
特殊角色思考决策模块
为预言家、女巫等特殊角色提供深度思考和策略分析能力
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
import random


class SpecialRolesThinkingSystem:
    """特殊角色思考决策系统"""
    
    def __init__(self, game_state, logger=None):
        """
        初始化特殊角色思考系统
        
        Args:
            game_state: 游戏状态
            logger: 日志记录器
        """
        self.game_state = game_state
        self.logger = logger or logging.getLogger(__name__)
        
        # 分析因子权重
        self.seer_analysis_factors = {
            "suspicion_level": 0.4,      # 怀疑度
            "speech_inconsistency": 0.3,  # 发言不一致性
            "behavior_pattern": 0.2,      # 行为模式
            "strategic_value": 0.1        # 策略价值
        }
        
        self.witch_decision_factors = {
            "game_phase": 0.3,           # 游戏阶段
            "team_balance": 0.3,         # 队伍平衡
            "strategic_timing": 0.2,     # 策略时机
            "target_importance": 0.2     # 目标重要性
        }
    
    async def conduct_seer_divination_thinking(self, seer, game_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """
        进行预言家查验决策思考
        
        Args:
            seer: 预言家对象
            game_state_dict: 游戏状态
            
        Returns:
            查验决策结果
        """
        print(f"\n🔮 预言家 {seer.name} 开始深度思考查验目标...")
        
        # 1. 分析可查验目标
        potential_targets = self._analyze_divination_targets(seer, game_state_dict)
        
        if not potential_targets:
            return {"success": False, "message": "没有可查验的目标"}
        
        # 2. 预言家思考过程
        thinking_process = await self._seer_thinking_process(seer, potential_targets, game_state_dict)
        
        # 3. 最终决策
        final_decision = self._make_seer_final_decision(thinking_process, potential_targets)
        
        return final_decision
    
    async def conduct_witch_action_thinking(self, witch, game_state_dict: Dict[str, Any], death_info: Optional[Dict] = None) -> Dict[str, Any]:
        """
        进行女巫行动决策思考
        
        Args:
            witch: 女巫对象
            game_state_dict: 游戏状态
            death_info: 死亡信息（如果有人被狼人击杀）
            
        Returns:
            女巫行动决策结果
        """
        print(f"\n🧙‍♀️ 女巫 {witch.name} 开始深度思考行动策略...")
        
        # 1. 分析当前形势
        situation_analysis = self._analyze_witch_situation(witch, game_state_dict, death_info)
        
        # 2. 女巫思考过程
        thinking_process = await self._witch_thinking_process(witch, situation_analysis, game_state_dict, death_info)
        
        # 3. 最终决策
        final_decision = self._make_witch_final_decision(thinking_process, situation_analysis)
        
        return final_decision
    
    def _analyze_divination_targets(self, seer, game_state_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析预言家可查验的目标"""
        alive_players = game_state_dict.get("alive_players", [])
        seer_id = seer.player_id
        
        targets = []
        for player in alive_players:
            player_id = player["id"]
            
            # 排除自己
            if player_id == seer_id:
                continue
            
            # 分析目标的查验价值
            divination_value = self._calculate_divination_value(player, game_state_dict, seer)
            
            targets.append({
                "id": player_id,
                "name": player["name"],
                "divination_value": divination_value,
                "analysis": self._generate_divination_target_analysis(player, game_state_dict, seer)
            })
        
        # 按查验价值排序
        targets.sort(key=lambda x: x["divination_value"], reverse=True)
        return targets
    
    def _calculate_divination_value(self, player: Dict[str, Any], game_state_dict: Dict[str, Any], seer) -> float:
        """计算目标的查验价值"""
        base_value = 0.0
        player_id = player["id"]
        
        # 1. 怀疑度分析
        suspicion_score = self._analyze_player_suspicion(player_id, game_state_dict, seer)
        base_value += suspicion_score * self.seer_analysis_factors["suspicion_level"] * 10
        
        # 2. 发言不一致性
        inconsistency_score = self._analyze_speech_inconsistency(player_id, game_state_dict)
        base_value += inconsistency_score * self.seer_analysis_factors["speech_inconsistency"] * 10
        
        # 3. 行为模式分析
        behavior_score = self._analyze_behavior_pattern(player_id, game_state_dict)
        base_value += behavior_score * self.seer_analysis_factors["behavior_pattern"] * 10
        
        # 4. 策略价值
        strategic_score = self._analyze_strategic_value(player_id, game_state_dict)
        base_value += strategic_score * self.seer_analysis_factors["strategic_value"] * 10
        
        return round(base_value, 2)
    
    def _analyze_player_suspicion(self, player_id: int, game_state_dict: Dict[str, Any], seer) -> float:
        """分析玩家的怀疑度（0-1）"""
        # 如果预言家有怀疑记录
        if hasattr(seer, 'suspicions') and player_id in seer.suspicions:
            return min(seer.suspicions[player_id], 1.0)
        
        # 基于发言内容的简单怀疑度评估
        recent_speeches = game_state_dict.get("recent_speeches", [])
        player_speeches = [s for s in recent_speeches if s.get("speaker_id") == player_id]
        
        if not player_speeches:
            return 0.5  # 默认中等怀疑度
        
        # 分析发言中的可疑关键词
        suspicious_keywords = ["我觉得", "可能", "不确定", "随便", "都行"]
        confident_keywords = ["确定", "肯定", "相信", "知道", "看到"]
        
        suspicious_count = 0
        confident_count = 0
        
        for speech in player_speeches:
            content = speech.get("content", "").lower()
            suspicious_count += sum(1 for word in suspicious_keywords if word in content)
            confident_count += sum(1 for word in confident_keywords if word in content)
        
        # 可疑发言多则怀疑度高
        if suspicious_count > confident_count:
            return 0.7
        elif confident_count > suspicious_count:
            return 0.3
        else:
            return 0.5
    
    def _analyze_speech_inconsistency(self, player_id: int, game_state_dict: Dict[str, Any]) -> float:
        """分析发言不一致性（0-1）"""
        recent_speeches = game_state_dict.get("recent_speeches", [])
        player_speeches = [s for s in recent_speeches if s.get("speaker_id") == player_id]
        
        if len(player_speeches) < 2:
            return 0.3  # 发言太少，默认低不一致性
        
        # 简化的不一致性检测：检查前后态度变化
        attitude_changes = 0
        previous_attitude = None
        
        for speech in player_speeches:
            content = speech.get("content", "").lower()
            
            # 简单的态度分析
            if any(word in content for word in ["支持", "赞同", "同意"]):
                current_attitude = "positive"
            elif any(word in content for word in ["反对", "怀疑", "不同意"]):
                current_attitude = "negative"
            else:
                current_attitude = "neutral"
            
            if previous_attitude and previous_attitude != current_attitude:
                attitude_changes += 1
            
            previous_attitude = current_attitude
        
        # 态度变化多则不一致性高
        inconsistency_rate = min(attitude_changes / len(player_speeches), 1.0)
        return inconsistency_rate
    
    def _analyze_behavior_pattern(self, player_id: int, game_state_dict: Dict[str, Any]) -> float:
        """分析行为模式（0-1）"""
        # 分析投票行为、发言频率等
        recent_speeches = game_state_dict.get("recent_speeches", [])
        player_speeches = [s for s in recent_speeches if s.get("speaker_id") == player_id]
        
        # 发言频率分析
        total_speeches = len(recent_speeches)
        player_speech_count = len(player_speeches)
        
        if total_speeches == 0:
            speech_frequency = 0
        else:
            speech_frequency = player_speech_count / total_speeches
        
        # 异常行为模式：过于沉默或过于活跃
        if speech_frequency < 0.1 or speech_frequency > 0.4:
            return 0.7  # 异常行为模式
        else:
            return 0.3  # 正常行为模式
    
    def _analyze_strategic_value(self, player_id: int, game_state_dict: Dict[str, Any]) -> float:
        """分析策略价值（0-1）"""
        current_round = game_state_dict.get("current_round", 1)
        alive_count = len(game_state_dict.get("alive_players", []))
        
        # 游戏后期查验的策略价值更高
        late_game_bonus = min(current_round / 5, 0.5)
        
        # 剩余玩家较少时查验价值更高
        scarcity_bonus = max(0, (7 - alive_count) / 7 * 0.3)
        
        return late_game_bonus + scarcity_bonus
    
    def _generate_divination_target_analysis(self, player: Dict[str, Any], game_state_dict: Dict[str, Any], seer) -> str:
        """生成查验目标分析报告"""
        player_id = player["id"]
        divination_value = self._calculate_divination_value(player, game_state_dict, seer)
        
        analysis = f"玩家{player_id}({player['name']}) - "
        analysis += f"查验价值：{divination_value:.1f}, "
        
        if divination_value >= 7:
            analysis += "高度可疑，强烈建议查验"
        elif divination_value >= 5:
            analysis += "中等可疑，值得查验"
        else:
            analysis += "低度可疑，可考虑查验"
        
        return analysis
    
    async def _seer_thinking_process(self, seer, targets: List[Dict[str, Any]], game_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """预言家思考过程"""
        print(f"🤔 {seer.name} 正在分析各个目标...")
        
        current_round = game_state_dict.get("current_round", 1)
        alive_count = len(game_state_dict.get("alive_players", []))
        
        # 显示目标分析
        print(f"📊 查验目标分析（第{current_round}轮，剩余{alive_count}人）：")
        for i, target in enumerate(targets[:3]):  # 显示前3个目标
            print(f"  {i+1}. {target['analysis']}")
        
        # 生成预言家的思考内容
        top_targets = targets[:3]
        target_info = "\n".join([f"- {t['analysis']}" for t in top_targets])
        
        thinking_prompt = f"""
        你是预言家{seer.player_id}({seer.name})，现在是第{current_round}轮的夜晚。
        你需要决定查验哪个玩家的身份。
        
        当前游戏状况：
        - 存活玩家数：{alive_count}人
        - 当前轮次：第{current_round}轮
        
        可查验目标分析：
        {target_info}
        
        作为预言家，请分析：
        1. 当前最需要确认身份的玩家是谁？
        2. 查验结果对游戏走向的影响
        3. 你的查验策略和优先级考虑
        
        请表达你的思考过程和最终决策。
        """
        
        try:
            if hasattr(seer, 'llm_interface'):
                thinking_response = await seer.llm_interface.generate_response(
                    thinking_prompt, 
                    "你是一个谨慎的预言家，正在思考查验策略。"
                )
                print(f"💭 {seer.name} 的思考：{thinking_response}")
                
                thinking_result = {
                    "thinking_content": thinking_response,
                    "analyzed_targets": top_targets,
                    "decision_factors": {
                        "game_phase": current_round,
                        "player_count": alive_count,
                        "priority": "identity_confirmation"
                    }
                }
                
                # 更新预言家的夜晚思考记忆
                seer.update_night_thinking_memory({
                    "round": current_round,
                    "role": "预言家",
                    "thinking_content": thinking_response,
                    "decision_factors": thinking_result["decision_factors"],
                    "context": "预言家夜晚查验思考"
                })
                
                return thinking_result
            else:
                # 备用思考内容
                default_thinking = f"我需要确认最可疑的玩家身份。{top_targets[0]['name']}的行为最值得关注。"
                print(f"💭 {seer.name} 的思考：{default_thinking}")
                
                thinking_result = {
                    "thinking_content": default_thinking,
                    "analyzed_targets": top_targets,
                    "decision_factors": {
                        "game_phase": current_round,
                        "player_count": alive_count,
                        "priority": "identity_confirmation"
                    }
                }
                
                # 更新预言家的夜晚思考记忆
                seer.update_night_thinking_memory({
                    "round": current_round,
                    "role": "预言家",
                    "thinking_content": default_thinking,
                    "decision_factors": thinking_result["decision_factors"],
                    "context": "预言家夜晚查验思考"
                })
                
                return thinking_result
                
        except Exception as e:
            self.logger.error(f"预言家思考过程出错: {e}")
            return {
                "thinking_content": "我需要仔细考虑查验目标...",
                "analyzed_targets": top_targets,
                "decision_factors": {"priority": "default"}
            }
    
    def _make_seer_final_decision(self, thinking_process: Dict[str, Any], targets: List[Dict[str, Any]]) -> Dict[str, Any]:
        """预言家最终决策"""
        if not targets:
            return {"success": False, "message": "没有可查验的目标"}
        
        # 选择查验价值最高的目标
        chosen_target = targets[0]
        
        print(f"🎯 {thinking_process.get('thinking_content', '')} 决定查验 {chosen_target['name']}！")
        
        return {
            "success": True,
            "target": chosen_target["id"],
            "reasoning": f"基于深度分析，选择查验{chosen_target['name']}（{chosen_target['analysis']}）",
            "thinking_process": thinking_process
        }
    
    def _analyze_witch_situation(self, witch, game_state_dict: Dict[str, Any], death_info: Optional[Dict]) -> Dict[str, Any]:
        """分析女巫当前形势"""
        current_round = game_state_dict.get("current_round", 1)
        alive_count = len(game_state_dict.get("alive_players", []))
        
        # 检查女巫的药剂状态
        has_antidote = getattr(witch, 'has_antidote', True)
        has_poison = getattr(witch, 'has_poison', True)
        
        # 分析死亡信息 - 只有有解药时才分析死亡信息
        death_analysis = None
        if death_info and has_antidote:
            target_id = death_info.get("target")
            target_player = self.game_state.get_player_by_id(target_id)
            if target_player:
                death_analysis = {
                    "victim_id": target_id,
                    "victim_name": target_player["name"],
                    "save_value": self._calculate_save_value(target_player, game_state_dict)
                }
                self.logger.info(f"女巫思考系统：分析玩家{target_id}的死亡信息，救人价值：{death_analysis['save_value']}")
        elif death_info and not has_antidote:
            self.logger.info(f"女巫思考系统：女巫无解药，不分析死亡信息")
        
        # 分析投毒目标
        poison_targets = self._analyze_poison_targets(witch, game_state_dict)
        
        return {
            "current_round": current_round,
            "alive_count": alive_count,
            "has_antidote": has_antidote,
            "has_poison": has_poison,
            "death_info": death_analysis,
            "poison_targets": poison_targets,
            "game_phase": "early" if current_round <= 2 else "late"
        }
    
    def _calculate_save_value(self, victim: Dict[str, Any], game_state_dict: Dict[str, Any]) -> float:
        """计算救人的价值"""
        # 基于玩家的重要性和游戏贡献
        save_value = 5.0  # 基础救人价值
        
        # 如果是活跃发言者，价值更高
        recent_speeches = game_state_dict.get("recent_speeches", [])
        victim_speeches = [s for s in recent_speeches if s.get("speaker_id") == victim["id"]]
        
        if len(victim_speeches) > len(recent_speeches) * 0.2:  # 发言较多
            save_value += 2.0
        
        # 游戏后期救人价值更高
        current_round = game_state_dict.get("current_round", 1)
        if current_round >= 3:
            save_value += 1.5
        
        return round(save_value, 1)
    
    def _analyze_poison_targets(self, witch, game_state_dict: Dict[str, Any]) -> List[Dict[str, Any]]:
        """分析投毒目标"""
        alive_players = game_state_dict.get("alive_players", [])
        witch_id = witch.player_id
        
        poison_targets = []
        for player in alive_players:
            if player["id"] == witch_id:
                continue
            
            poison_value = self._calculate_poison_value(player, game_state_dict, witch)
            
            poison_targets.append({
                "id": player["id"],
                "name": player["name"],
                "poison_value": poison_value,
                "analysis": f"玩家{player['id']}({player['name']}) - 投毒价值：{poison_value:.1f}"
            })
        
        # 按投毒价值排序
        poison_targets.sort(key=lambda x: x["poison_value"], reverse=True)
        return poison_targets[:3]  # 返回前3个目标
    
    def _calculate_poison_value(self, player: Dict[str, Any], game_state_dict: Dict[str, Any], witch) -> float:
        """计算投毒价值"""
        base_value = 3.0
        player_id = player["id"]
        
        # 如果女巫有怀疑记录
        if hasattr(witch, 'suspicions') and player_id in witch.suspicions:
            suspicion_level = witch.suspicions.get(player_id, 0)
            base_value += suspicion_level * 4  # 怀疑度越高，投毒价值越高
        
        # 分析发言活跃度（过于活跃可能是狼人）
        recent_speeches = game_state_dict.get("recent_speeches", [])
        player_speeches = [s for s in recent_speeches if s.get("speaker_id") == player_id]
        
        if len(player_speeches) > len(recent_speeches) * 0.3:  # 发言过多
            base_value += 1.5
        
        return round(base_value, 1)
    
    async def _witch_thinking_process(self, witch, situation: Dict[str, Any], game_state_dict: Dict[str, Any], death_info: Optional[Dict]) -> Dict[str, Any]:
        """女巫思考过程"""
        print(f"🤔 {witch.name} 正在分析当前形势...")
        
        # 获取女巫药剂状态
        has_antidote = situation.get('has_antidote', True)
        has_poison = situation.get('has_poison', True)
        
        # 显示形势分析
        print(f"📊 当前形势分析：")
        print(f"  🔮 第{situation['current_round']}轮，剩余{situation['alive_count']}人")
        print(f"  💊 解药：{'有' if has_antidote else '无'}，毒药：{'有' if has_poison else '无'}")
        
        if death_info and situation['death_info'] and has_antidote:
            death_analysis = situation['death_info']
            print(f"  ☠️ {death_analysis['victim_name']} 被狼人击杀，救人价值：{death_analysis['save_value']}")
        elif death_info and not has_antidote:
            print(f"  ☠️ 死亡情况未知（女巫无解药）")
        
        if situation['poison_targets']:
            print(f"  🧪 可投毒目标：")
            for target in situation['poison_targets']:
                print(f"    - {target['analysis']}")
        
        # 生成女巫的思考内容
        thinking_prompt = self._generate_witch_thinking_prompt(witch, situation, death_info)
        
        try:
            if hasattr(witch, 'llm_interface'):
                thinking_response = await witch.llm_interface.generate_response(
                    thinking_prompt,
                    "你是一个智慧的女巫，正在权衡使用药剂的时机。"
                )
                print(f"💭 {witch.name} 的思考：{thinking_response}")
                
                thinking_result = {
                    "thinking_content": thinking_response,
                    "situation_analysis": situation,
                    "decision_factors": self._extract_decision_factors(thinking_response, situation)
                }
                
                # 更新女巫的夜晚思考记忆
                witch.update_night_thinking_memory({
                    "round": situation['current_round'],
                    "role": "女巫",
                    "thinking_content": thinking_response,
                    "decision_factors": thinking_result["decision_factors"],
                    "context": "女巫夜晚药剂使用思考"
                })
                
                return thinking_result
            else:
                # 备用思考内容
                default_thinking = self._generate_default_witch_thinking(situation, death_info)
                print(f"💭 {witch.name} 的思考：{default_thinking}")
                
                thinking_result = {
                    "thinking_content": default_thinking,
                    "situation_analysis": situation,
                    "decision_factors": {"priority": "default"}
                }
                
                # 更新女巫的夜晚思考记忆
                witch.update_night_thinking_memory({
                    "round": situation['current_round'],
                    "role": "女巫",
                    "thinking_content": default_thinking,
                    "decision_factors": thinking_result["decision_factors"],
                    "context": "女巫夜晚药剂使用思考"
                })
                
                return thinking_result
                
        except Exception as e:
            self.logger.error(f"女巫思考过程出错: {e}")
            return {
                "thinking_content": "我需要仔细权衡使用药剂的时机...",
                "situation_analysis": situation,
                "decision_factors": {"priority": "default"}
            }
    
    def _generate_witch_thinking_prompt(self, witch, situation: Dict[str, Any], death_info: Optional[Dict]) -> str:
        """生成女巫思考提示词"""
        current_round = situation['current_round']
        alive_count = situation['alive_count']
        has_antidote = situation['has_antidote']
        has_poison = situation['has_poison']
        
        prompt = f"""
        你是女巫{witch.player_id}({witch.name})，现在是第{current_round}轮的夜晚。
        你需要决定是否使用药剂。
        
        【关键信息】你的药剂状态：
        - 解药：{'✅ 可用' if has_antidote else '❌ 已用'}
        - 毒药：{'✅ 可用' if has_poison else '❌ 已用'}
        
        当前游戏状况：
        - 存活玩家数：{alive_count}人
        - 游戏阶段：{situation['game_phase']}期
        """
        
        if death_info and situation['death_info'] and has_antidote:
            death_analysis = situation['death_info']
            prompt += f"""
        
        死亡信息：
        - {death_analysis['victim_name']} 被狼人击杀
        - 救人价值：{death_analysis['save_value']}/10
        """
        elif death_info and not has_antidote:
            prompt += f"""
        
        死亡信息：未知（你已无解药，无法得知今晚死亡情况）
        """
        
        if situation['poison_targets']:
            targets_info = "\n".join([f"- {t['analysis']}" for t in situation['poison_targets']])
            prompt += f"""
        
        可投毒目标分析：
        {targets_info}
        """
        
        prompt += """
        
        作为女巫，请考虑：
        1. 是否使用解药救人？考虑救人的价值和时机
        2. 是否使用毒药杀人？考虑目标的威胁度
        3. 保留药剂的策略价值
        
        请表达你的策略思考和最终决定。
        """
        
        return prompt
    
    def _generate_default_witch_thinking(self, situation: Dict[str, Any], death_info: Optional[Dict]) -> str:
        """生成默认女巫思考内容"""
        if death_info and situation['death_info'] and situation['has_antidote']:
            death_analysis = situation['death_info']
            if death_analysis['save_value'] >= 6:
                return f"我应该救活{death_analysis['victim_name']}，这个玩家对村民阵营很重要。"
        
        if situation['poison_targets'] and situation['has_poison']:
            target = situation['poison_targets'][0]
            return f"我考虑投毒{target['name']}，这个玩家的行为比较可疑。"
        
        return "当前情况下我选择保留药剂，等待更好的时机。"
    
    def _extract_decision_factors(self, thinking_content: str, situation: Dict[str, Any]) -> Dict[str, Any]:
        """从思考内容中提取决策因子"""
        factors = {"priority": "strategic"}
        
        content_lower = thinking_content.lower()
        
        # 检测倾向
        if any(word in content_lower for word in ["救", "解药", "保护"]):
            factors["action_tendency"] = "save"
        elif any(word in content_lower for word in ["毒", "杀", "除掉"]):
            factors["action_tendency"] = "poison"
        else:
            factors["action_tendency"] = "wait"
        
        # 检测紧迫性
        if any(word in content_lower for word in ["立即", "马上", "现在", "必须"]):
            factors["urgency"] = "high"
        elif any(word in content_lower for word in ["等待", "保留", "稍后"]):
            factors["urgency"] = "low"
        else:
            factors["urgency"] = "medium"
        
        return factors
    
    def _make_witch_final_decision(self, thinking_process: Dict[str, Any], situation: Dict[str, Any]) -> Dict[str, Any]:
        """女巫最终决策"""
        decision_factors = thinking_process.get("decision_factors", {})
        action_tendency = decision_factors.get("action_tendency", "wait")
        
        # 基于思考内容做决策
        if action_tendency == "save" and situation.get('has_antidote') and situation.get('death_info'):
            # 使用解药
            victim_id = situation['death_info']['victim_id']
            victim_name = situation['death_info']['victim_name']
            
            print(f"💊 决定使用解药救活 {victim_name}！")
            
            return {
                "success": True,
                "action": "save",
                "target": victim_id,
                "reasoning": f"基于策略分析，使用解药救活{victim_name}",
                "thinking_process": thinking_process
            }
            
        elif action_tendency == "poison" and situation.get('has_poison') and situation.get('poison_targets'):
            # 使用毒药
            target = situation['poison_targets'][0]
            target_id = target['id']
            target_name = target['name']
            
            print(f"🧪 决定使用毒药毒死 {target_name}！")
            
            return {
                "success": True,
                "action": "poison",
                "target": target_id,
                "reasoning": f"基于策略分析，使用毒药毒死{target_name}",
                "thinking_process": thinking_process
            }
        
        else:
            # 不使用药剂
            print(f"🤐 决定保留药剂，等待更好的时机。")
            
            return {
                "success": True,
                "action": "no_action",
                "reasoning": "基于策略考虑，选择保留药剂",
                "thinking_process": thinking_process
            } 