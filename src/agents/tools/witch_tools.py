"""
女巫工具函数集
定义女巫角色的所有工具函数
"""

import logging
from typing import Dict, Any, List, Optional
from llama_index.core.tools import FunctionTool

from ...ai_agent import BaseAIAgent


class WitchTools:
    """女巫工具函数集合"""
    
    def __init__(self, witch_agent: BaseAIAgent):
        self.witch = witch_agent
        self.logger = logging.getLogger(f"WitchTools_{witch_agent.player_id}")
    
    def get_tools(self) -> List[FunctionTool]:
        """获取所有女巫工具"""
        return [
            FunctionTool.from_defaults(
                fn=self.analyze_death_situation,
                name="analyze_death_situation",
                description="分析今晚的死亡情况，评估是否需要使用解药"
            ),
            FunctionTool.from_defaults(
                fn=self.evaluate_save_target,
                name="evaluate_save_target", 
                description="评估是否应该救活某个玩家"
            ),
            FunctionTool.from_defaults(
                fn=self.evaluate_poison_target,
                name="evaluate_poison_target",
                description="评估是否应该毒死某个玩家"
            ),
            FunctionTool.from_defaults(
                fn=self.use_antidote,
                name="use_antidote",
                description="使用解药救活指定玩家"
            ),
            FunctionTool.from_defaults(
                fn=self.use_poison,
                name="use_poison", 
                description="使用毒药毒死指定玩家"
            ),
            FunctionTool.from_defaults(
                fn=self.no_action,
                name="no_action",
                description="不使用任何药剂"
            )
        ]
    
    def analyze_death_situation(self, death_info: Dict[str, Any], game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        分析今晚的死亡情况
        
        Args:
            death_info: 死亡信息
            game_state: 游戏状态
            
        Returns:
            分析结果
        """
        try:
            if not self.witch.has_antidote:
                return {
                    "action": "analyze_death",
                    "success": True,
                    "message": "已无解药，无法救人",
                    "recommendation": "no_save",
                    "reason": "解药已用完"
                }
            
            if not death_info or not death_info.get("target"):
                return {
                    "action": "analyze_death",
                    "success": True,
                    "message": "今晚无人死亡",
                    "recommendation": "no_save",
                    "reason": "无人死亡"
                }
            
            target_id = death_info["target"]
            
            # 分析是否应该救人
            should_save = self._should_save_player(target_id, game_state)
            
            return {
                "action": "analyze_death",
                "success": True,
                "target_id": target_id,
                "recommendation": "save" if should_save else "no_save",
                "reason": self._get_save_reason(target_id, should_save, game_state)
            }
            
        except Exception as e:
            self.logger.error(f"分析死亡情况失败: {e}")
            return {
                "action": "analyze_death",
                "success": False,
                "message": f"分析失败: {e}"
            }
    
    def evaluate_save_target(self, target_id: int, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估是否应该救活某个玩家
        
        Args:
            target_id: 目标玩家ID
            game_state: 游戏状态
            
        Returns:
            评估结果
        """
        try:
            if not self.witch.has_antidote:
                return {
                    "action": "evaluate_save",
                    "success": False,
                    "message": "已无解药"
                }
            
            should_save = self._should_save_player(target_id, game_state)
            reason = self._get_save_reason(target_id, should_save, game_state)
            
            return {
                "action": "evaluate_save",
                "success": True,
                "target_id": target_id,
                "should_save": should_save,
                "reason": reason,
                "confidence": self._get_save_confidence(target_id, game_state)
            }
            
        except Exception as e:
            self.logger.error(f"评估救人目标失败: {e}")
            return {
                "action": "evaluate_save",
                "success": False,
                "message": f"评估失败: {e}"
            }
    
    def evaluate_poison_target(self, target_id: int, game_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        评估是否应该毒死某个玩家
        
        Args:
            target_id: 目标玩家ID
            game_state: 游戏状态
            
        Returns:
            评估结果
        """
        try:
            if not self.witch.has_poison:
                return {
                    "action": "evaluate_poison",
                    "success": False,
                    "message": "已无毒药"
                }
            
            if target_id == self.witch.player_id:
                return {
                    "action": "evaluate_poison",
                    "success": False,
                    "message": "不能毒死自己"
                }
            
            should_poison = self._should_poison_player(target_id, game_state)
            reason = self._get_poison_reason(target_id, should_poison, game_state)
            
            return {
                "action": "evaluate_poison",
                "success": True,
                "target_id": target_id,
                "should_poison": should_poison,
                "reason": reason,
                "confidence": self._get_poison_confidence(target_id, game_state)
            }
            
        except Exception as e:
            self.logger.error(f"评估毒人目标失败: {e}")
            return {
                "action": "evaluate_poison",
                "success": False,
                "message": f"评估失败: {e}"
            }
    
    def use_antidote(self, target_id: int) -> Dict[str, Any]:
        """
        使用解药救活指定玩家
        
        Args:
            target_id: 目标玩家ID
            
        Returns:
            使用结果
        """
        try:
            if not self.witch.has_antidote:
                return {
                    "action": "use_antidote",
                    "success": False,
                    "message": "已无解药"
                }
            
            # 更新女巫状态
            self.witch.has_antidote = False
            self.witch.saved_players.append(target_id)
            
            self.logger.info(f"女巫{self.witch.player_id}使用解药救活玩家{target_id}")
            
            return {
                "action": "use_antidote",
                "success": True,
                "target_id": target_id,
                "message": f"成功使用解药救活玩家{target_id}",
                "final_decision": True
            }
            
        except Exception as e:
            self.logger.error(f"使用解药失败: {e}")
            return {
                "action": "use_antidote",
                "success": False,
                "message": f"使用失败: {e}"
            }
    
    def use_poison(self, target_id: int) -> Dict[str, Any]:
        """
        使用毒药毒死指定玩家
        
        Args:
            target_id: 目标玩家ID
            
        Returns:
            使用结果
        """
        try:
            if not self.witch.has_poison:
                return {
                    "action": "use_poison",
                    "success": False,
                    "message": "已无毒药"
                }
            
            if target_id == self.witch.player_id:
                return {
                    "action": "use_poison",
                    "success": False,
                    "message": "不能毒死自己"
                }
            
            # 更新女巫状态
            self.witch.has_poison = False
            self.witch.poisoned_players.append(target_id)
            
            self.logger.info(f"女巫{self.witch.player_id}使用毒药毒死玩家{target_id}")
            
            return {
                "action": "use_poison",
                "success": True,
                "target_id": target_id,
                "message": f"成功使用毒药毒死玩家{target_id}",
                "final_decision": True
            }
            
        except Exception as e:
            self.logger.error(f"使用毒药失败: {e}")
            return {
                "action": "use_poison",
                "success": False,
                "message": f"使用失败: {e}"
            }
    
    def no_action(self) -> Dict[str, Any]:
        """
        不使用任何药剂
        
        Returns:
            决策结果
        """
        try:
            self.logger.info(f"女巫{self.witch.player_id}选择不使用药剂")
            
            return {
                "action": "no_action",
                "success": True,
                "message": "选择不使用任何药剂",
                "final_decision": True
            }
            
        except Exception as e:
            self.logger.error(f"无操作决策失败: {e}")
            return {
                "action": "no_action",
                "success": False,
                "message": f"决策失败: {e}"
            }
    
    def _should_save_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该救某个玩家"""
        # 不救自己
        if target_id == self.witch.player_id:
            return False
        
        # 如果是可信任的玩家，倾向于救
        if target_id in self.witch.suspicions and self.witch.suspicions[target_id] < -0.3:
            return True
        
        # 如果是高度怀疑的玩家，不救
        if target_id in self.witch.suspicions and self.witch.suspicions[target_id] > 0.5:
            return False
        
        # 根据策略决定
        if self.witch.save_strategy == "conservative":
            return False  # 保守策略，不轻易救人
        else:
            return True  # 积极策略，倾向于救人
    
    def _should_poison_player(self, target_id: int, game_state: Dict[str, Any]) -> bool:
        """判断是否应该毒某个玩家"""
        # 不毒自己
        if target_id == self.witch.player_id:
            return False
        
        # 如果高度怀疑，考虑使用毒药
        if target_id in self.witch.suspicions and self.witch.suspicions[target_id] > 0.7:
            return True
        
        return False
    
    def _get_save_reason(self, target_id: int, should_save: bool, game_state: Dict[str, Any]) -> str:
        """获取救人的理由"""
        if should_save:
            if target_id in self.witch.suspicions and self.witch.suspicions[target_id] < -0.3:
                return f"玩家{target_id}是可信的好人"
            else:
                return f"玩家{target_id}可能是好人，值得拯救"
        else:
            if target_id in self.witch.suspicions and self.witch.suspicions[target_id] > 0.5:
                return f"玩家{target_id}高度可疑，不值得救"
            else:
                return f"解药珍贵，需要谨慎使用"
    
    def _get_poison_reason(self, target_id: int, should_poison: bool, game_state: Dict[str, Any]) -> str:
        """获取毒人的理由"""
        if should_poison:
            if target_id in self.witch.suspicions and self.witch.suspicions[target_id] > 0.7:
                return f"玩家{target_id}高度可疑，很可能是狼人"
            else:
                return f"玩家{target_id}行为可疑，值得毒杀"
        else:
            return f"玩家{target_id}不够可疑，不值得使用毒药"
    
    def _get_save_confidence(self, target_id: int, game_state: Dict[str, Any]) -> float:
        """获取救人的信心度"""
        if target_id in self.witch.suspicions:
            suspicion = self.witch.suspicions[target_id]
            if suspicion < -0.3:
                return 0.8  # 高信心
            elif suspicion > 0.5:
                return 0.2  # 低信心
            else:
                return 0.5  # 中等信心
        return 0.5
    
    def _get_poison_confidence(self, target_id: int, game_state: Dict[str, Any]) -> float:
        """获取毒人的信心度"""
        if target_id in self.witch.suspicions:
            suspicion = self.witch.suspicions[target_id]
            if suspicion > 0.7:
                return 0.8  # 高信心
            elif suspicion < 0.3:
                return 0.2  # 低信心
            else:
                return 0.5  # 中等信心
        return 0.3 