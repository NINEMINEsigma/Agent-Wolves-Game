"""
白天结束系统
处理白天结束时的玩家独立思考和被放逐玩家遗言
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime


class DayEndSystem:
    """白天结束系统"""
    
    def __init__(self, llm_interface, ui_observer):
        """
        初始化白天结束系统
        
        参数:
            llm_interface: LLM接口
            ui_observer: UI观察者
        """
        self.llm_interface = llm_interface
        self.ui_observer = ui_observer
        self.logger = logging.getLogger(__name__)
    
    async def handle_exile_last_words(self, exiled_player, game_state_dict: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        处理被放逐玩家的遗言
        
        参数:
            exiled_player: 被放逐的玩家
            game_state_dict: 游戏状态
            
        返回:
            遗言内容
        """
        try:
            print(f"\n💬 {exiled_player.name} 的遗言时刻...")
            print("=" * 50)
            
            # 构建遗言提示
            prompt = self._build_last_words_prompt(exiled_player, game_state_dict)
            
            # 获取AI生成的遗言
            last_words = await self.llm_interface.generate_response(prompt, "你正在以真实身份留下最后的遗言。")
            
            if last_words:
                # 显示遗言
                print(f"\n🕊️ {exiled_player.name} 的遗言：")
                print(f"「{last_words}」")
                print()
                
                # 添加时间戳和上下文
                formatted_last_words = {
                    "player_id": exiled_player.player_id,
                    "player_name": exiled_player.name,
                    "content": last_words,
                    "timestamp": datetime.now().isoformat(),
                    "context": "放逐遗言"
                }
                
                # 让其他存活玩家观察遗言
                await self._broadcast_last_words_to_players(exiled_player, last_words, game_state_dict)
                
                return formatted_last_words
            
        except Exception as e:
            self.logger.error(f"处理被放逐玩家{exiled_player.player_id}遗言时出错: {e}")
            print(f"💬 {exiled_player.name} 因为情况紧急，没有留下遗言")
            
        return None
    
    async def conduct_end_of_day_thinking(self, alive_players: List, game_state_dict: Dict[str, Any], round_num: int) -> Dict[str, Any]:
        """
        进行白天结束时的玩家独立思考
        
        参数:
            alive_players: 存活玩家列表
            game_state_dict: 游戏状态
            round_num: 当前轮次
            
        返回:
            思考结果汇总
        """
        try:
            print(f"\n🧠 第{round_num}轮白天结束 - 玩家独立思考时间")
            print("=" * 60)
            print("📝 每个玩家正在独立思考今日的游戏情况...")
            
            thinking_results = {}
            
            # 对每个存活玩家进行并发思考
            thinking_tasks = []
            for player in alive_players:
                task = self._conduct_individual_thinking(player, game_state_dict, round_num)
                thinking_tasks.append(task)
            
            # 等待所有思考完成
            thinking_responses = await asyncio.gather(*thinking_tasks, return_exceptions=True)
            
            # 处理思考结果
            for i, response in enumerate(thinking_responses):
                player = alive_players[i]
                
                if isinstance(response, Exception):
                    self.logger.error(f"玩家{player.player_id}思考时出错: {response}")
                    thinking_results[player.player_id] = {
                        "player_name": player.name,
                        "thinking": "思考被打断，无法形成清晰想法",
                        "status": "error"
                    }
                else:
                    thinking_results[player.player_id] = response
            
            # 显示思考汇总
            self._display_thinking_summary(thinking_results, round_num)
            
            return {
                "success": True,
                "round_num": round_num,
                "thinking_results": thinking_results,
                "participants": len(alive_players),
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"白天结束思考阶段出错: {e}")
            return {"success": False, "error": str(e)}
    
    def _build_last_words_prompt(self, exiled_player, game_state_dict: Dict[str, Any]) -> str:
        """构建遗言提示"""
        role_name = getattr(exiled_player, 'role', '未知')
        current_round = game_state_dict.get('current_round', 1)
        
        # 获取游戏信息
        alive_count = len([p for p in game_state_dict.get('players', []) if p.get('is_alive', False)])
        
        # 使用身份强化提示词
        identity_context = ""
        if hasattr(exiled_player, 'get_identity_context'):
            identity_context = exiled_player.get_identity_context()
        else:
            identity_context = f"你是玩家{exiled_player.player_id}号{exiled_player.name}。"
        
        prompt = f"""{identity_context}

你刚刚在第{current_round}轮的投票中被放逐，即将离开游戏。这是你最后发声的机会！

当前游戏情况：
- 当前轮次：第{current_round}轮
- 剩余存活玩家：{alive_count}人
- 你的真实身份：{role_name}

请以玩家{exiled_player.player_id}号{exiled_player.name}的身份留下你的遗言，充分体现你的个性特征和最后的尊严。
你的遗言应该：
1. 体现你作为玩家{exiled_player.player_id}号的独特个性和风格
2. 根据你的真实身份考虑是否透露身份信息
3. 分享你对其他玩家的看法和分析
4. 给存活玩家一些建议或提醒
5. 表达你对游戏局势的最后判断

这是你最后的发言机会！
遗言要简洁有力。直接返回遗言内容，不要加任何额外的格式。"""

        return prompt
    
    async def _broadcast_last_words_to_players(self, exiled_player, last_words: str, game_state_dict: Dict[str, Any], alive_players: Optional[List] = None):
        """向其他存活玩家广播遗言"""
        try:
            # 记录遗言到游戏记忆中
            last_words_info = {
                "speaker": exiled_player.name,
                "speaker_id": exiled_player.player_id,
                "content": last_words,
                "context": "放逐遗言",
                "round": game_state_dict.get('current_round', 1)
            }
            
            # 如果提供了存活玩家列表，直接更新他们的记忆
            if alive_players:
                for other_player in alive_players:
                    if other_player.player_id != exiled_player.player_id:
                        other_player.update_memory("speeches", last_words_info)
                        self.logger.info(f"遗言已广播给玩家{other_player.player_id}")
            
            return last_words_info
            
        except Exception as e:
            self.logger.error(f"广播遗言时出错: {e}")
            return None
    
    async def _conduct_individual_thinking(self, player, game_state_dict: Dict[str, Any], round_num: int) -> Dict[str, Any]:
        """进行单个玩家的独立思考"""
        try:
            # 构建思考提示
            prompt = self._build_thinking_prompt(player, game_state_dict, round_num)
            
            # 获取AI思考
            thinking_content = await self.llm_interface.generate_response(prompt, "你正在独自进行深度思考和反思。")
            
            if thinking_content:
                return {
                    "player_id": player.player_id,
                    "player_name": player.name,
                    "thinking": thinking_content,
                    "status": "success",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return {
                    "player_id": player.player_id,
                    "player_name": player.name,
                    "thinking": "思绪混乱，无法整理出清晰的想法",
                    "status": "empty"
                }
                
        except Exception as e:
            self.logger.error(f"玩家{player.player_id}独立思考时出错: {e}")
            raise e
    
    def _build_thinking_prompt(self, player, game_state_dict: Dict[str, Any], round_num: int) -> str:
        """构建独立思考提示"""
        role_name = getattr(player, 'role', '未知')
        current_round = game_state_dict.get('current_round', 1)
        
        # 获取今日发生的事件
        alive_count = len([p for p in game_state_dict.get('players', []) if p.get('is_alive', False)])
        
        # 使用身份强化提示词
        identity_context = ""
        if hasattr(player, 'get_identity_context'):
            identity_context = player.get_identity_context()
        else:
            identity_context = f"你是玩家{player.player_id}号{player.name}。"
        
        prompt = f"""{identity_context}

第{round_num}轮的白天阶段刚刚结束，现在是深夜时分，你独自一人思考今天发生的一切。

当前情况：
- 轮次：第{round_num}轮白天结束
- 剩余存活玩家：{alive_count}人
- 你的身份：{role_name}

请以玩家{player.player_id}号{player.name}的身份进行深度独立思考，充分体现你的个性特征和思维方式：

1. 以你独特的个性风格分析今天的投票结果
2. 用你的判断方式重新评估其他玩家的行为和发言
3. 基于你的视角判断游戏当前局势
4. 规划符合你个性特点的明天行动策略
5. 结合你的身份（{role_name}）进行深层思考

要充分展现玩家{player.player_id}号{player.name}独特的思维深度、个人风格和内心想法。
思考要深入细致，表达你内心最真实的想法。
直接返回思考内容，不要加任何额外的格式。"""

        return prompt
    
    def _display_thinking_summary(self, thinking_results: Dict[str, Any], round_num: int):
        """显示思考结果汇总"""
        try:
            print(f"\n💭 第{round_num}轮白天结束思考汇总：")
            print("-" * 50)
            
            successful_thinking = 0
            
            for player_id, result in thinking_results.items():
                if result.get("status") == "success":
                    successful_thinking += 1
                    print(f"\n🤔 {result['player_name']} 的思考：")
                    print(f"   「{result['thinking']}」")
                elif result.get("status") == "error":
                    print(f"\n❌ {result['player_name']}：思考被打断")
                else:
                    print(f"\n😶 {result['player_name']}：思绪混乱")
            
            print(f"\n📊 思考统计：{successful_thinking}/{len(thinking_results)} 位玩家完成深度思考")
            print("=" * 50)
            
        except Exception as e:
            self.logger.error(f"显示思考汇总时出错: {e}") 