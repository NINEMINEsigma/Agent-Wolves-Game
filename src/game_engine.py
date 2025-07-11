"""
核心游戏引擎
处理狼人杀游戏的主要流程和循环
"""

import asyncio
import logging
import random
from typing import Dict, List, Any, Optional
from datetime import datetime

from .ai_agent import BaseAIAgent
from .game_state import GameState, GamePhase
from .voting_system import VotingSystem
from .victory_checker import VictoryChecker
from .ui_observer import GameObserver
from .werewolf_cooperation import WerewolfCooperationSystem
from .special_roles_thinking import SpecialRolesThinkingSystem
from .day_end_system import DayEndSystem
from .agents.agent_factory import AgentFactory


class WerewolfGameEngine:
    """狼人杀游戏引擎"""
    
    def __init__(self, config: Dict[str, Any], players: List[BaseAIAgent]):
        """
        初始化游戏引擎
        
        Args:
            config: 游戏配置
            players: 玩家列表
        """
        self.config = config
        self.players = players
        
        # 日志设置（需要在其他组件初始化之前）
        self.logger = logging.getLogger(__name__)
        
        # 初始化Agent工厂
        self.agent_factory = AgentFactory(config)
        
        # 初始化核心组件
        self.game_state = GameState(config)
        self.voting_system = VotingSystem(self.game_state)
        self.victory_checker = VictoryChecker(self.game_state)
        self.ui_observer = GameObserver(config)
        self.werewolf_cooperation = WerewolfCooperationSystem(self.game_state, self.logger)
        self.special_roles_thinking = SpecialRolesThinkingSystem(self.game_state, self.logger)
        
        # 初始化白天结束系统
        # 需要LLM接口，这里使用第一个玩家的LLM接口
        llm_interface = players[0].llm_interface if players else None
        self.day_end_system = DayEndSystem(llm_interface, self.ui_observer)
        
        # 游戏控制
        self.is_running = False
        
        # 从配置文件读取观察延迟设置
        delay_config = config.get("ui_settings", {}).get("observation_delays", {})
        self.pause_between_phases = delay_config.get("phase_transition", 2.0)
        self.action_delay = delay_config.get("action_result", 1.5)
        self.death_announcement_delay = delay_config.get("death_announcement", 3.0)
        self.speech_delay = delay_config.get("speech", 2.0)
        self.voting_delay = delay_config.get("voting_result", 1.5)
        
        # 角色分组
        self.werewolves = []
        self.villagers = []
        self.special_roles: Dict[str, Optional[BaseAIAgent]] = {"seer": None, "witch": None}
    
    async def start_game(self) -> Dict[str, Any]:
        """
        开始游戏主循环
        
        Returns:
            游戏结果
        """
        try:
            self.logger.info("开始AI狼人杀游戏")
            self.is_running = True
            
            # 1. 初始化游戏
            await self._initialize_game()
            
            # 2. 显示游戏开始
            # 用户作为观察者应该看到所有角色信息
            player_info = [{"id": p.player_id, "name": p.name, "role": p.role} 
                          for p in self.players]
            self.ui_observer.display_game_start(player_info)
            
            # 3. 主游戏循环
            while self.is_running:
                # 检查胜利条件
                winner = self.victory_checker.check_victory_condition(self.game_state)
                if winner:
                    break
                
                # 检查回合数限制（仅在有配置时）
                if self.game_state.has_round_limit() and self.game_state.current_round > self.game_state.max_rounds:
                    self.logger.info(f"达到最大回合数限制: {self.game_state.max_rounds}")
                    self.ui_observer.display_round_limit_reached(self.game_state.max_rounds)
                    break
                
                # 推进游戏阶段
                current_phase = self.game_state.advance_phase()
                
                # 执行对应阶段逻辑
                if current_phase == GamePhase.NIGHT:
                    await self._run_night_phase()
                    # 夜晚阶段后检查游戏是否已结束
                    if not self.is_running:
                        break
                elif current_phase == GamePhase.DAY:
                    await self._run_day_phase()
                elif current_phase == GamePhase.DISCUSSION:
                    await self._run_discussion_phase()
                elif current_phase == GamePhase.VOTING:
                    await self._run_voting_phase()
                    # 投票阶段后检查游戏是否已结束
                    if not self.is_running:
                        break
                elif current_phase == GamePhase.GAME_END:
                    break
                
                # 阶段间暂停
                await asyncio.sleep(self.pause_between_phases)
            
            # 4. 游戏结束处理
            return await self._finalize_game()
            
        except Exception as e:
            self.logger.error(f"游戏执行异常: {e}")
            self.is_running = False
            return {"error": str(e), "success": False}
    
    async def _initialize_game(self) -> None:
        """初始化游戏状态"""
        # 添加所有玩家到游戏状态
        for player in self.players:
            self.game_state.add_player({
                "id": player.player_id,
                "name": player.name,
                "role": player.role
            })
        
        # 分组玩家
        self._group_players_by_role()
        
        # 设置狼人队友关系
        for werewolf in self.werewolves:
            teammate_ids = [w.player_id for w in self.werewolves if w != werewolf]
            werewolf.set_teammates(teammate_ids)
        
        self.logger.info(f"游戏初始化完成，{len(self.players)}名玩家")
    
    def _group_players_by_role(self) -> None:
        """按角色分组玩家"""
        for player in self.players:
            if player.role == "werewolf":
                self.werewolves.append(player)
            elif player.role in ["villager", "seer", "witch"]:
                self.villagers.append(player)
                
                # 记录特殊角色
                if player.role in self.special_roles:
                    self.special_roles[player.role] = player
    
    async def _run_night_phase(self) -> None:
        """执行夜晚阶段"""
        round_num = self.game_state.current_round
        self.ui_observer.display_phase_transition("night", round_num)
        
        # 处理夜晚行动
        night_results = await self._process_night_actions()
        
        # 显示夜晚行动结果（只显示成功的行动）
        for action_type, result in night_results.items():
            if result.get("success") and result.get("message"):
                self.ui_observer.display_night_action(result["message"])
                await asyncio.sleep(self.action_delay)  # 让用户观察行动结果
        
        self.logger.info(f"第{round_num}轮夜晚阶段完成")
    
    async def _process_night_actions(self) -> Dict[str, Any]:
        """处理所有夜晚行动"""
        night_results = {}
        
        # 1. 狼人杀人
        werewolf_result = await self._handle_werewolf_kill()
        night_results["werewolf_kill"] = werewolf_result
        
        # 2. 预言家查验
        seer_result = await self._handle_seer_divination()
        night_results["seer_divine"] = seer_result
        
        # 3. 女巫行动
        witch_result = await self._handle_witch_action(werewolf_result)
        night_results["witch_action"] = witch_result
        
        # 4. 执行死亡结果
        await self._execute_night_deaths(werewolf_result, witch_result)
        
        return night_results
    
    async def _handle_werewolf_kill(self) -> Dict[str, Any]:
        """处理狼人群体协作击杀"""
        alive_werewolves = [w for w in self.werewolves if w.is_alive]
        
        if not alive_werewolves:
            return {"success": False, "message": "没有存活的狼人"}
        
        try:
            # 使用狼人协作系统进行群体决策
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
            
            # 显示狼人讨论过程
            print(f"\n🐺 狼人夜晚协作讨论开始...")
            print(f"参与讨论的狼人：{[f'玩家{w.player_id}' for w in alive_werewolves]}")
            
            # 进行群体讨论和决策
            decision_result = await self.werewolf_cooperation.conduct_werewolf_discussion(
                alive_werewolves, game_state_dict
            )
            
            if decision_result.get("success") and decision_result.get("target"):
                target_id = decision_result["target"]
                target_player = self.game_state.get_player_by_id(target_id)
                
                if target_player and target_player["is_alive"]:
                    # 显示决策结果
                    decision_type = decision_result.get("decision_type", "unknown")
                    reasoning = decision_result.get("reasoning", "未知原因")
                    
                    print(f"🎯 狼人群体决策：{reasoning}")
                    if decision_type == "group_vote" and "votes" in decision_result:
                        print("📊 投票详情：")
                        for target, vote_count in decision_result["votes"].items():
                            target_info = self.game_state.get_player_by_id(target)
                            target_name = target_info["name"] if target_info else f"玩家{target}"
                            print(f"  玩家{target}({target_name}): {vote_count}票")
                    
                    # 记录击杀行动（代表狼人群体）
                    representative_werewolf = alive_werewolves[0]
                    self.game_state.record_night_action(
                        representative_werewolf.player_id, "kill", target_id,
                        {"decision_type": decision_type, "reasoning": reasoning}
                    )
                    
                    return {
                        "success": True,
                        "target": target_id,
                        "target_name": target_player["name"],
                        "message": f"狼人群体协作决定击杀玩家{target_id}",
                        "decision_details": decision_result
                    }
                else:
                    self.logger.warning(f"狼人选择的目标{target_id}无效或已死亡")
                    return {"success": False, "message": "狼人选择的目标无效"}
            else:
                error_msg = decision_result.get("message", "狼人协作决策失败")
                self.logger.info(f"狼人协作决策无结果: {error_msg}")
                return {"success": False, "message": error_msg}
            
        except Exception as e:
            self.logger.error(f"狼人协作击杀处理异常: {e}")
            # 备用方案：回退到原始逻辑
            return await self._fallback_werewolf_kill(alive_werewolves)
    
    async def _fallback_werewolf_kill(self, alive_werewolves: List) -> Dict[str, Any]:
        """备用狼人击杀方案（当协作系统失败时）"""
        try:
            # 简化方案：由第一个狼人决定
            main_werewolf = alive_werewolves[0]
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
            action_result = await main_werewolf.night_action(game_state_dict)
            
            if action_result.get("success") and action_result.get("target"):
                target_id = action_result["target"]
                target_player = self.game_state.get_player_by_id(target_id)
                
                if target_player and target_player["is_alive"]:
                    # 记录击杀行动
                    self.game_state.record_night_action(
                        main_werewolf.player_id, "kill", target_id
                    )
                    
                    print(f"🔄 备用方案：狼人{main_werewolf.player_id}决定击杀玩家{target_id}")
                    
                    return {
                        "success": True,
                        "target": target_id,
                        "target_name": target_player["name"],
                        "message": f"狼人（备用方案）击杀玩家{target_id}"
                    }
            
            return {"success": False, "message": "备用狼人击杀方案失败"}
            
        except Exception as e:
            self.logger.error(f"备用狼人击杀方案异常: {e}")
            return {"success": False, "message": "备用击杀方案异常"}
    
    async def _handle_seer_divination(self) -> Dict[str, Any]:
        """处理预言家查验（智能思考版本）"""
        seer = self.special_roles.get("seer")
        
        if not seer or not seer.is_alive:
            return {"success": False, "message": "预言家不存在或已死亡"}
        
        try:
            # 使用特殊角色思考系统进行智能决策
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
            
            # 进行深度思考和决策
            thinking_result = await self.special_roles_thinking.conduct_seer_divination_thinking(
                seer, game_state_dict
            )
            
            if thinking_result.get("success") and thinking_result.get("target"):
                target_id = thinking_result["target"]
                target_player = self.game_state.get_player_by_id(target_id)
                
                if target_player:
                    # 获取目标真实身份
                    target_role = target_player["role"]
                    role_category = "werewolf" if target_role == "werewolf" else "villager"
                    
                    # 告知预言家结果
                    if hasattr(seer, 'receive_vision_result'):
                        seer.receive_vision_result(target_id, role_category)
                    
                    # 记录查验行动
                    self.game_state.record_night_action(
                        seer.player_id, "divine", target_id, 
                        {"result": role_category, "reasoning": thinking_result.get("reasoning", "")}
                    )
                    
                    print(f"🔍 预言家查验结果：{target_player['name']} 是 {role_category}")
                    
                    return {
                        "success": True,
                        "target": target_id,
                        "result": role_category,
                        "message": f"预言家深度思考后查验玩家{target_id}：{role_category}",
                        "thinking_details": thinking_result
                    }
            
            return {"success": False, "message": "预言家查验失败"}
            
        except Exception as e:
            self.logger.error(f"预言家智能查验处理异常: {e}")
            # 备用方案：回退到原始逻辑
            return await self._fallback_seer_divination(seer)
    
    async def _fallback_seer_divination(self, seer) -> Dict[str, Any]:
        """预言家备用查验方案"""
        try:
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
            action_result = await seer.night_action(game_state_dict)
            
            if action_result.get("success") and action_result.get("target"):
                target_id = action_result["target"]
                target_player = self.game_state.get_player_by_id(target_id)
                
                if target_player:
                    target_role = target_player["role"]
                    role_category = "werewolf" if target_role == "werewolf" else "villager"
                    
                    if hasattr(seer, 'receive_vision_result'):
                        seer.receive_vision_result(target_id, role_category)
                    
                    self.game_state.record_night_action(
                        seer.player_id, "divine", target_id, 
                        {"result": role_category}
                    )
                    
                    print(f"🔄 备用方案：预言家查验玩家{target_id}：{role_category}")
                    
                    return {
                        "success": True,
                        "target": target_id,
                        "result": role_category,
                        "message": f"预言家（备用方案）查验玩家{target_id}：{role_category}"
                    }
            
            return {"success": False, "message": "备用预言家查验失败"}
            
        except Exception as e:
            self.logger.error(f"备用预言家查验异常: {e}")
            return {"success": False, "message": "备用查验异常"}
    
    async def _handle_witch_action(self, werewolf_result: Dict[str, Any]) -> Dict[str, Any]:
        """处理女巫行动（Agent模式）"""
        witch = self.special_roles.get("witch")
        
        if not witch or not witch.is_alive:
            return {"success": False, "message": "女巫不存在或已死亡"}
        
        # 检查女巫是否还有药剂
        has_antidote = getattr(witch, 'has_antidote', True)
        has_poison = getattr(witch, 'has_poison', True)
        
        if not has_antidote and not has_poison:
            print(f"\n💊 女巫 {witch.name} 药剂已耗尽，夜晚无法行动")
            return {
                "success": True,
                "action": "no_action",
                "message": f"女巫{witch.player_id}药剂已耗尽，夜晚无法行动"
            }
        
        try:
            # 构建死亡信息给女巫 - 只有有解药时才告知死亡信息
            death_info = None
            if werewolf_result.get("success") and has_antidote:
                death_info = {
                    "target": werewolf_result["target"],
                    "cause": "werewolf_kill"
                }
                self.logger.info(f"女巫{witch.player_id}有解药，被告知玩家{werewolf_result['target']}被狼人击杀")
            elif werewolf_result.get("success") and not has_antidote:
                self.logger.info(f"女巫{witch.player_id}无解药，不被告知死亡信息")
            
            # 使用Agent模式处理女巫行动
            return await self._handle_witch_agent_action(witch, werewolf_result, death_info or {})
                
        except Exception as e:
            self.logger.error(f"女巫行动处理异常: {e}")
            # 备用方案：回退到原始逻辑
            return await self._fallback_witch_action(witch, werewolf_result)
    

    
    def get_agent_mode_info(self) -> Dict[str, Any]:
        """获取Agent模式信息"""
        try:
            return self.agent_factory.get_mode_info()
        except Exception as e:
            self.logger.error(f"获取Agent模式信息失败: {e}")
            return {"mode": "agent", "error": str(e)}
    
    def validate_agent_config(self) -> Dict[str, Any]:
        """验证Agent配置"""
        return self.agent_factory.validate_config()
    
    async def _handle_witch_agent_action(self, witch, werewolf_result: Dict[str, Any], death_info: Dict[str, Any]) -> Dict[str, Any]:
        """处理女巫Agent行动"""
        try:
            self.logger.info(f"使用女巫Agent模式进行决策")
            
            # 构建游戏状态
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
            
            # 使用Agent进行决策
            action_result = await witch.night_action(game_state_dict, death_info)
            
            if action_result.get("success"):
                action_type = action_result.get("action")
                
                if action_type == "use_antidote" and action_result.get("target_id"):
                    # 使用解药
                    target_id = action_result["target_id"]
                    
                    self.game_state.record_night_action(
                        witch.player_id, "save", target_id,
                        {"reasoning": action_result.get("message", "")}
                    )
                    
                    # 显示女巫药剂状态
                    self._display_witch_status(witch, "使用解药后（Agent模式）")
                    
                    return {
                        "success": True,
                        "action": "save",
                        "target": target_id,
                        "message": f"女巫Agent使用解药救活玩家{target_id}",
                        "agent_details": action_result
                    }
                
                elif action_type == "use_poison" and action_result.get("target_id"):
                    # 使用毒药
                    target_id = action_result["target_id"]
                    
                    self.game_state.record_night_action(
                        witch.player_id, "poison", target_id,
                        {"reasoning": action_result.get("message", "")}
                    )
                    
                    # 显示女巫药剂状态
                    self._display_witch_status(witch, "使用毒药后（Agent模式）")
                    
                    return {
                        "success": True,
                        "action": "poison",
                        "target": target_id,
                        "message": f"女巫Agent使用毒药毒死玩家{target_id}",
                        "agent_details": action_result
                    }
                
                else:
                    # 不使用药剂
                    # 显示女巫药剂状态
                    self._display_witch_status(witch, "保留药剂（Agent模式）")
                    
                    return {
                        "success": True,
                        "action": "no_action",
                        "message": "女巫Agent选择不使用药剂",
                        "agent_details": action_result
                    }
            
            return {"success": False, "message": "女巫Agent决策失败"}
            
        except Exception as e:
            self.logger.error(f"女巫Agent行动处理异常: {e}")
            return await self._fallback_witch_action(witch, werewolf_result)
    
    async def _fallback_witch_action(self, witch, werewolf_result: Dict[str, Any]) -> Dict[str, Any]:
        """女巫备用行动方案"""
        try:
            # 检查女巫药剂状态
            has_antidote = getattr(witch, 'has_antidote', True)
            has_poison = getattr(witch, 'has_poison', True)
            
            # 构建死亡信息给女巫（备用方案）- 只有有解药时才告知死亡信息
            death_info = None
            if werewolf_result.get("success") and has_antidote:
                death_info = {
                    "target": werewolf_result["target"],
                    "cause": "werewolf_kill"
                }
                self.logger.info(f"女巫{witch.player_id}备用方案：有解药，被告知玩家{werewolf_result['target']}被狼人击杀")
            elif werewolf_result.get("success") and not has_antidote:
                self.logger.info(f"女巫{witch.player_id}备用方案：无解药，不被告知死亡信息")
            
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
            action_result = await witch.night_action(game_state_dict, death_info)
            
            if action_result.get("success"):
                action_type = action_result.get("action")
                
                if action_type == "save" and action_result.get("target"):
                    target_id = action_result["target"]
                    if hasattr(witch, 'has_antidote'):
                        witch.has_antidote = False
                    
                    self.game_state.record_night_action(
                        witch.player_id, "save", target_id
                    )
                    
                    # 显示女巫药剂状态
                    self._display_witch_status(witch, "使用解药后（备用方案）")
                    
                    return {
                        "success": True,
                        "action": "save",
                        "target": target_id,
                        "message": f"女巫（备用方案）使用解药救活玩家{target_id}"
                    }
                
                elif action_type == "poison" and action_result.get("target"):
                    target_id = action_result["target"]
                    if hasattr(witch, 'has_poison'):
                        witch.has_poison = False
                    
                    self.game_state.record_night_action(
                        witch.player_id, "poison", target_id
                    )
                    
                    # 显示女巫药剂状态
                    self._display_witch_status(witch, "使用毒药后（备用方案）")
                    
                    return {
                        "success": True,
                        "action": "poison",
                        "target": target_id,
                        "message": f"女巫（备用方案）使用毒药毒死玩家{target_id}"
                    }
                
                else:
                    # 不使用药剂
                    # 显示女巫药剂状态
                    self._display_witch_status(witch, "保留药剂（备用方案）")
                    
                    return {
                        "success": True,
                        "action": "no_action",
                        "message": "女巫（备用方案）选择不使用药剂"
                    }
            
            return {"success": False, "message": "女巫备用行动方案失败"}
            
        except Exception as e:
            self.logger.error(f"女巫备用行动方案异常: {e}")
            return {"success": False, "message": "女巫备用行动异常"}
    
    def _display_witch_status(self, witch, action_description: str) -> None:
        """显示女巫当前药剂状态"""
        try:
            # 检查女巫的药剂状态
            has_antidote = getattr(witch, 'has_antidote', True)
            has_poison = getattr(witch, 'has_poison', True)
            
            # 构建状态字符串
            antidote_status = "✅" if has_antidote else "❌"
            poison_status = "✅" if has_poison else "❌"
            
            print(f"\n💊 女巫 {witch.name} 药剂状态（{action_description}）：")
            print(f"   🌿 解药：{antidote_status} {'可用' if has_antidote else '已用'}")
            print(f"   🧪 毒药：{poison_status} {'可用' if has_poison else '已用'}")
            
            # 计算剩余药剂数量
            remaining_potions = sum([has_antidote, has_poison])
            if remaining_potions == 2:
                print(f"   📝 状态：药剂充足，可灵活应对")
            elif remaining_potions == 1:
                print(f"   📝 状态：仅剩一种药剂，需谨慎使用")
            else:
                print(f"   📝 状态：药剂耗尽，女巫变为普通村民")
                
        except Exception as e:
            self.logger.error(f"显示女巫状态时出错: {e}")
            print(f"💊 女巫 {witch.name} 完成行动（{action_description}）")
    
    async def _execute_night_deaths(self, werewolf_result: Dict[str, Any], 
                                  witch_result: Dict[str, Any]) -> None:
        """执行夜晚死亡结果"""
        deaths = []
        saves = []
        
        # 收集所有死亡和拯救
        if werewolf_result.get("success"):
            deaths.append({
                "target": werewolf_result["target"],
                "cause": "狼人击杀"
            })
        
        if witch_result.get("success"):
            if witch_result.get("action") == "save":
                saves.append(witch_result["target"])
            elif witch_result.get("action") == "poison":
                deaths.append({
                    "target": witch_result["target"],
                    "cause": "女巫毒杀"
                })
        
        # 执行拯救（移除对应死亡）
        for save_target in saves:
            deaths = [d for d in deaths if d["target"] != save_target]
        
        # 执行死亡
        for death in deaths:
            target_id = death["target"]
            cause = death["cause"]
            
            success = self.game_state.kill_player(target_id, cause)
            if success:
                # 更新AI代理状态
                for player in self.players:
                    if player.player_id == target_id:
                        player.die(cause)
                        break
                
                # 通知其他玩家观察死亡
                for player in self.players:
                    if player.player_id != target_id:
                        player.observe_death(target_id, cause)
        
        # 夜晚死亡执行后立即检查胜利条件
        winner = self.victory_checker.check_victory_condition(self.game_state)
        if winner:
            self.logger.info(f"夜晚死亡后游戏结束，获胜方: {winner}")
            self.is_running = False
    
    async def _run_day_phase(self) -> None:
        """执行白天阶段"""
        round_num = self.game_state.current_round
        
        # 公布夜晚死亡结果
        night_deaths = [p for p in self.game_state.dead_players 
                       if p.get("death_round") == round_num]
        
        death_summary = ""
        if night_deaths:
            death_info = []
            for dead_player in night_deaths:
                self.ui_observer.display_death_announcement(dead_player, dead_player["death_cause"])
                await asyncio.sleep(self.death_announcement_delay)  # 让用户充分观察死亡信息
                death_info.append(f"{dead_player['name']}")
            death_summary = f"昨晚 {', '.join(death_info)} 死亡"
        else:
            death_summary = "昨晚是平安夜，无人死亡"
        
        self.ui_observer.display_phase_transition("day", round_num, death_summary)
        
        await asyncio.sleep(2)  # 给观察者时间查看死亡信息
        
        self.logger.info(f"第{round_num}轮白天阶段完成")
    
    async def _run_discussion_phase(self) -> None:
        """执行讨论阶段"""
        round_num = self.game_state.current_round
        self.ui_observer.display_phase_transition("discussion", round_num)
        
        # 获取存活玩家并按玩家ID固定顺序发言
        alive_players = [p for p in self.players if p.is_alive]
        alive_players.sort(key=lambda x: x.player_id)  # 按玩家ID排序，确保固定顺序
        
        # 每个玩家依次发言
        for i, player in enumerate(alive_players):
            try:
                # 在玩家发言前，收集本轮中已经发言的玩家内容
                current_round_speeches = []
                for j in range(i):
                    previous_player = alive_players[j]
                    # 获取之前玩家在本轮的发言
                    previous_speeches = previous_player.get_current_round_speeches(round_num)
                    current_round_speeches.extend(previous_speeches)
                
                # 为当前玩家提供本轮已发言的上下文
                if current_round_speeches:
                    # 将本轮已发言内容添加到当前玩家的记忆中
                    for speech_data in current_round_speeches:
                        player.update_memory("speeches", speech_data)
                
                game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
                speech = await player.make_speech(game_state_dict)
                
                # 显示发言
                self.ui_observer.display_player_speech(player, speech)
                
                # 记录发言
                self.game_state.record_speech(player.player_id, speech)
                
                # 其他玩家观察发言（包括轮次信息）
                for other_player in alive_players:
                    if other_player != player:
                        other_player.update_memory("speeches", {
                            "speaker": player.name,
                            "speaker_id": player.player_id,
                            "content": speech,
                            "round": round_num,
                            "context": "正常发言"
                        })
                
                await asyncio.sleep(self.speech_delay)  # 让用户有时间阅读发言
                
            except Exception as e:
                self.logger.error(f"玩家{player.player_id}发言异常: {e}")
        
        self.logger.info(f"第{round_num}轮讨论阶段完成")
    
    async def _run_voting_phase(self) -> None:
        """执行投票阶段"""
        round_num = self.game_state.current_round
        self.ui_observer.display_phase_transition("voting", round_num)
        
        # 获取存活玩家
        alive_players = [p for p in self.players if p.is_alive]
        candidate_ids = [p.player_id for p in alive_players]
        
        if len(alive_players) <= 2:
            self.logger.info("存活玩家不足，跳过投票")
            return
        
        # 首次投票
        vote_result = await self.voting_system.conduct_full_vote(
            alive_players, candidate_ids, "elimination", is_revote=False
        )
        
        # 显示首次投票结果
        display_result = vote_result["vote_analysis"].copy()
        display_result["final_target"] = vote_result["final_target"]
        
        self.ui_observer.display_voting_process(
            vote_result["vote_counts"], 
            display_result
        )
        
        await asyncio.sleep(self.voting_delay)
        
        # 检查是否需要重新投票
        if vote_result.get("needs_revote", False):
            self.logger.info("首次投票平票，进行重新发言和投票")
            
            # 显示平票信息
            tied_players = vote_result["tie_result"]["tied_players"]
            tied_names = []
            for pid in tied_players:
                player_info = self.game_state.get_player_by_id(pid)
                if player_info:
                    tied_names.append(player_info["name"])
            
            print(f"\n⚖️ 首次投票平票！平票玩家：{', '.join(tied_names)}")
            print("📢 将进行重新发言，然后重新投票")
            
            await asyncio.sleep(2)
            
            # 重新发言阶段（仅针对平票玩家）
            print(f"\n🗣️ 平票玩家重新发言阶段")
            alive_players_sorted = [p for p in self.players if p.is_alive]
            alive_players_sorted.sort(key=lambda x: x.player_id)
            
            for player in alive_players_sorted:
                if player.player_id in tied_players:
                    try:
                        game_state_dict = self.game_state.export_state(hide_roles_from_ai=True)
                        speech = await player.make_speech(game_state_dict)
                        
                        # 显示发言（平票辩护）
                        print(f"\n🛡️ {player.name} 平票辩护发言：")
                        self.ui_observer.display_player_speech(player, speech)
                        
                        # 记录发言
                        self.game_state.record_speech(player.player_id, speech)
                        
                        # 其他玩家观察发言
                        for other_player in alive_players_sorted:
                            if other_player != player:
                                other_player.update_memory("speeches", {
                                    "speaker": player.name,
                                    "speaker_id": player.player_id,
                                    "content": speech,
                                    "context": "平票辩护",
                                    "round": round_num
                                })
                        
                        await asyncio.sleep(self.speech_delay)
                        
                    except Exception as e:
                        self.logger.error(f"玩家{player.player_id}重新发言异常: {e}")
            
            # 重新投票
            print(f"\n🗳️ 重新投票阶段")
            revote_result = await self.voting_system.conduct_full_vote(
                alive_players, tied_players, "elimination", is_revote=True
            )
            
            # 显示重新投票结果
            display_revote_result = revote_result["vote_analysis"].copy()
            display_revote_result["final_target"] = revote_result["final_target"]
            
            print(f"\n🔄 重新投票结果：")
            self.ui_observer.display_voting_process(
                revote_result["vote_counts"], 
                display_revote_result
            )
            
            await asyncio.sleep(self.voting_delay)
            
            # 使用重新投票的结果
            vote_result = revote_result
        
        # 处理最终投票结果
        eliminated_player_id = vote_result["final_target"]
        tie_result = vote_result.get("tie_result")
        
        if tie_result and tie_result["action"] == "skip_elimination":
            # 二次平票，跳过放逐
            print(f"\n❌ 二次投票仍然平票，跳过放逐环节")
            self.logger.info("二次平票，跳过放逐环节")
        elif eliminated_player_id:
            # 有明确的放逐目标
            eliminated_player_info = self.game_state.get_player_by_id(eliminated_player_id)
            if eliminated_player_info:
                # 找到被放逐的玩家代理
                exiled_player = None
                for player in self.players:
                    if player.player_id == eliminated_player_id:
                        exiled_player = player
                        break
                
                # 处理被放逐玩家的遗言
                if exiled_player:
                    game_state_dict = self.game_state.export_state(hide_roles_from_ai=False)
                    last_words_result = await self.day_end_system.handle_exile_last_words(
                        exiled_player, game_state_dict
                    )
                    
                    # 将遗言广播给其他存活玩家
                    if last_words_result:
                        alive_players = [p for p in self.players if p.is_alive and p.player_id != eliminated_player_id]
                        await self.day_end_system._broadcast_last_words_to_players(
                            exiled_player, 
                            last_words_result["content"], 
                            game_state_dict, 
                            alive_players
                        )
                
                self.ui_observer.display_death_announcement(
                    eliminated_player_info, "投票放逐"
                )
                
                await asyncio.sleep(self.death_announcement_delay)
                
                # 更新AI代理状态
                if exiled_player:
                    exiled_player.die("投票放逐")
        else:
            # 其他情况（不应该出现）
            self.logger.warning("投票结果异常，无明确处理")
        
        # 投票放逐后立即检查胜利条件
        winner = self.victory_checker.check_victory_condition(self.game_state)
        if winner:
            self.logger.info(f"投票放逐后游戏结束，获胜方: {winner}")
            self.is_running = False
            return  # 游戏结束，不需要进行后续的白天结束思考
        
        # 白天结束时的玩家独立思考（仅在游戏未结束时进行）
        alive_players = [p for p in self.players if p.is_alive]
        if alive_players and self.is_running:
            game_state_dict = self.game_state.export_state(hide_roles_from_ai=False)
            thinking_result = await self.day_end_system.conduct_end_of_day_thinking(
                alive_players, game_state_dict, round_num
            )
            
            # 将思考结果更新到玩家记忆中
            if thinking_result.get("success"):
                for player_id, thinking_data in thinking_result["thinking_results"].items():
                    if thinking_data.get("status") == "success":
                        # 找到对应的玩家
                        for player in alive_players:
                            if player.player_id == player_id:
                                player.update_memory("self_reflection", {
                                    "round": round_num,
                                    "phase": "day_end",
                                    "thinking": thinking_data["thinking"],
                                    "timestamp": thinking_data["timestamp"]
                                })
                                break
        
        self.logger.info(f"第{round_num}轮投票阶段完成")
    
    async def _finalize_game(self) -> Dict[str, Any]:
        """结束游戏并生成结果"""
        self.is_running = False
        
        # 获取游戏总结
        game_summary = self.victory_checker.get_game_summary(self.game_state)
        
        # 显示游戏结束
        winner = self.game_state.game_winner or "unknown"
        self.ui_observer.display_game_end(winner, game_summary)
        
        # 保存游戏日志
        log_file = self.ui_observer.save_game_log()
        
        # 生成最终结果
        final_result = {
            "success": True,
            "winner": winner,
            "game_summary": game_summary,
            "total_rounds": self.game_state.current_round,
            "final_players": self.game_state.export_state(),
            "log_file": log_file
        }
        
        self.logger.info(f"游戏结束，获胜方: {winner}")
        return final_result
    
    def pause_game(self) -> None:
        """暂停游戏"""
        self.logger.info("游戏暂停")
    
    def resume_game(self) -> None:
        """恢复游戏"""
        self.logger.info("游戏恢复")
    
    def stop_game(self) -> None:
        """停止游戏"""
        self.is_running = False
        self.logger.info("游戏强制停止")
    
    def get_game_status(self) -> Dict[str, Any]:
        """获取当前游戏状态"""
        victory_probs = self.victory_checker.predict_victory_probability(self.game_state)
        
        return {
            "is_running": self.is_running,
            "current_round": self.game_state.current_round,
            "current_phase": self.game_state.current_phase.value,
            "alive_players": len(self.game_state.alive_players),
            "dead_players": len(self.game_state.dead_players),
            "victory_probabilities": victory_probs,
            "faction_counts": self.game_state.get_faction_counts()
        } 