"""
身份认同系统
强化AI玩家对自己身份号码的认同感和角色扮演深度
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime


class IdentitySystem:
    """身份认同强化系统"""
    
    def __init__(self):
        """初始化身份系统"""
        self.logger = logging.getLogger(__name__)
        self.identity_profiles = {}  # 存储每个玩家的身份档案
        
    def create_identity_profile(self, player_id: int, name: str, role: str) -> Dict[str, Any]:
        """
        为玩家创建详细的身份档案
        
        参数:
            player_id: 玩家ID
            name: 玩家姓名
            role: 角色类型
            
        返回:
            身份档案字典
        """
        # 基于玩家ID生成个性化特征
        personality_traits = self._generate_personality_traits(player_id)
        speech_style = self._generate_speech_style(player_id)
        background_story = self._generate_background_story(player_id, name, role)
        
        identity_profile = {
            "player_id": player_id,
            "name": name,
            "role": role,
            "personality_traits": personality_traits,
            "speech_style": speech_style,
            "background_story": background_story,
            "identity_mantra": self._generate_identity_mantra(player_id, name, role),
            "created_at": datetime.now().isoformat()
        }
        
        self.identity_profiles[player_id] = identity_profile
        return identity_profile
    
    def get_enhanced_prompt_prefix(self, player_id: int) -> str:
        """
        获取增强的身份认同提示词前缀
        
        参数:
            player_id: 玩家ID
            
        返回:
            身份强化提示词
        """
        if player_id not in self.identity_profiles:
            return f"你是玩家{player_id}。"
        
        profile = self.identity_profiles[player_id]
        
        identity_prompt = f"""
【身份认同强化】
你是玩家{profile['player_id']}号，名字叫{profile['name']}。这个身份对你来说至关重要。

【你的身份宣言】
{profile['identity_mantra']}

【你的个性特征】
{profile['personality_traits']}

【你的说话风格】
{profile['speech_style']}

【你的背景故事】
{profile['background_story']}

【重要提醒】
- 你必须始终以"玩家{profile['player_id']}号{profile['name']}"的身份思考和行动
- 在发言时要体现出你独特的个性和说话风格
- 要对自己的玩家号码有强烈的认同感和自豪感
- 记住你在这个游戏中的独特身份和使命
"""
        
        return identity_prompt
    
    def get_role_enhanced_prompt(self, player_id: int, base_role_prompt: str) -> str:
        """
        获取角色增强提示词
        
        参数:
            player_id: 玩家ID
            base_role_prompt: 基础角色提示词
            
        返回:
            增强后的角色提示词
        """
        identity_prefix = self.get_enhanced_prompt_prefix(player_id)
        
        if player_id not in self.identity_profiles:
            return f"{identity_prefix}\n\n{base_role_prompt}"
        
        profile = self.identity_profiles[player_id]
        role = profile['role']
        
        role_identity_bridge = self._get_role_identity_bridge(player_id, role)
        
        enhanced_prompt = f"""
{identity_prefix}

【角色身份融合】
{role_identity_bridge}

【角色任务】
{base_role_prompt}

【行动指导】
- 始终记住你是玩家{player_id}号{profile['name']}，一个{role}
- 你的每个决定都要符合你的个性特征和说话风格
- 在游戏中要展现出你独特的个人魅力和判断力
"""
        
        return enhanced_prompt
    
    def _generate_personality_traits(self, player_id: int) -> str:
        """根据玩家ID生成个性特征"""
        # 基于玩家ID的数字特征生成个性
        traits_pool = [
            ["理性冷静", "逻辑清晰", "善于分析"],
            ["热情开朗", "表达直接", "情感丰富"], 
            ["谨慎稳重", "深思熟虑", "话语不多"],
            ["机智幽默", "反应敏捷", "善于察言观色"],
            ["正义感强", "立场坚定", "不容妥协"],
            ["温和友善", "善于倾听", "容易相信他人"],
            ["怀疑心重", "警觉性高", "不轻易相信"],
            ["领导气质", "善于协调", "能凝聚人心"]
        ]
        
        trait_index = player_id % len(traits_pool)
        selected_traits = traits_pool[trait_index]
        
        return f"你是一个{selected_traits[0]}的人，具有{selected_traits[1]}的特点，同时{selected_traits[2]}。"
    
    def _generate_speech_style(self, player_id: int) -> str:
        """根据玩家ID生成说话风格"""
        styles = [
            "喜欢用逻辑和数据说话，经常说'从逻辑上看'、'根据分析'",
            "说话直接坦率，经常用'我觉得'、'说实话'开头",
            "措辞谨慎，喜欢用'可能'、'或许'、'我认为'等委婉表达",
            "语言幽默生动，偶尔开玩笑，用词较为轻松活泼",
            "说话坚定有力，经常用'必须'、'绝对'、'毫无疑问'等词",
            "用词温和礼貌，经常说'请大家'、'我们一起'、'不好意思'",
            "说话时带有质疑色彩，经常反问，用'真的吗'、'确定吗'",
            "善于总结和引导，经常说'让我们'、'大家注意'、'重点是'"
        ]
        
        style_index = player_id % len(styles)
        return styles[style_index]
    
    def _generate_background_story(self, player_id: int, name: str, role: str) -> str:
        """生成角色背景故事"""
        backgrounds = [
            f"你是{name}，一个注重逻辑的分析师，平时工作中习惯用数据说话。",
            f"你是{name}，一个直率的行动派，从小就是孩子王，习惯直接表达想法。",
            f"你是{name}，一个谨慎的观察者，做事喜欢三思而后行。",
            f"你是{name}，一个幽默的调解者，总能在紧张时刻缓解气氛。",
            f"你是{name}，一个正义感很强的人，最痛恨欺骗和背叛。",
            f"你是{name}，一个温和的倾听者，总是愿意相信别人的善意。",
            f"你是{name}，一个天生的怀疑论者，对一切都保持警惕。",
            f"你是{name}，一个天生的领导者，习惯协调大家达成共识。"
        ]
        
        bg_index = player_id % len(backgrounds)
        base_background = backgrounds[bg_index]
        
        role_addon = {
            "villager": "作为一个普通村民，你有责任保护村庄的和平。",
            "werewolf": "但现在你隐藏着狼人的身份，必须小心掩饰。",
            "seer": "你拥有预言家的神圣能力，是村庄的希望。",
            "witch": "你掌握着神秘的药剂，是村庄的守护者。"
        }
        
        return base_background + role_addon.get(role, "")
    
    def _generate_identity_mantra(self, player_id: int, name: str, role: str) -> str:
        """生成身份宣言"""
        mantras = [
            f"我是玩家{player_id}号{name}，我用理性和逻辑来证明自己的价值！",
            f"我是玩家{player_id}号{name}，我会用直率和真诚赢得大家的信任！",
            f"我是玩家{player_id}号{name}，我的谨慎和观察力是我最大的武器！",
            f"我是玩家{player_id}号{name}，我要用智慧和幽默照亮这个游戏！",
            f"我是玩家{player_id}号{name}，我会坚守正义，绝不妥协！",
            f"我是玩家{player_id}号{name}，我相信团结的力量能战胜一切！",
            f"我是玩家{player_id}号{name}，我的警觉会保护我和我的伙伴！",
            f"我是玩家{player_id}号{name}，我要带领大家走向胜利！"
        ]
        
        mantra_index = player_id % len(mantras)
        return mantras[mantra_index]
    
    def _get_role_identity_bridge(self, player_id: int, role: str) -> str:
        """获取角色与身份的连接桥梁"""
        if player_id not in self.identity_profiles:
            return f"作为玩家{player_id}号，你同时也是一个{role}。"
        
        profile = self.identity_profiles[player_id]
        name = profile['name']
        
        bridges = {
            "villager": f"作为玩家{player_id}号{name}，你是一个普通村民，但你的个性和判断力让你在村民中独一无二。你要用自己独特的方式来识别狼人，保护村庄。",
            "werewolf": f"作为玩家{player_id}号{name}，你表面上是个村民，但实际上是狼人。你必须用你独特的个性来完美伪装，让其他人相信你就是那个值得信任的玩家{player_id}号。",
            "seer": f"作为玩家{player_id}号{name}，你是神圣的预言家。你的个性和智慧将帮助你明智地使用预言能力，并在关键时刻引导村民走向胜利。",
            "witch": f"作为玩家{player_id}号{name}，你是神秘的女巫。你的个性将影响你如何使用宝贵的药剂，在最关键的时刻发挥你独特的作用。"
        }
        
        return bridges.get(role, f"作为玩家{player_id}号{name}，你要用你独特的个性来扮演好{role}这个角色。")
    
    def update_identity_context(self, player_id: int, context_type: str, context_data: Dict[str, Any]):
        """
        更新身份上下文信息
        
        参数:
            player_id: 玩家ID
            context_type: 上下文类型
            context_data: 上下文数据
        """
        if player_id in self.identity_profiles:
            if "contexts" not in self.identity_profiles[player_id]:
                self.identity_profiles[player_id]["contexts"] = {}
            
            self.identity_profiles[player_id]["contexts"][context_type] = {
                "data": context_data,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_identity_summary(self, player_id: int) -> str:
        """获取身份摘要"""
        if player_id not in self.identity_profiles:
            return f"玩家{player_id}的身份档案未找到"
        
        profile = self.identity_profiles[player_id]
        return f"玩家{player_id}号{profile['name']}（{profile['role']}）"
    
    def export_all_profiles(self) -> Dict[int, Dict[str, Any]]:
        """导出所有身份档案"""
        return self.identity_profiles.copy() 