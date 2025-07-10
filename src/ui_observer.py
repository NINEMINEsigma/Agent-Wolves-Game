"""
用户界面观察器
实时显示AI行为和游戏进程，提供用户观察体验
"""

import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

try:
    from colorama import init, Fore, Back, Style
    init(autoreset=True)
    COLORAMA_AVAILABLE = True
except ImportError:
    COLORAMA_AVAILABLE = False
    # 如果没有colorama，定义空的样式
    class DummyStyle:
        RESET_ALL = ""
        BRIGHT = ""
        DIM = ""
    
    class DummyFore:
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
        RESET = ""
    
    class DummyBack:
        BLACK = ""
        RED = ""
        GREEN = ""
        YELLOW = ""
        BLUE = ""
        MAGENTA = ""
        CYAN = ""
        WHITE = ""
    
    Fore = DummyFore()
    Back = DummyBack()
    Style = DummyStyle()

from .ai_agent import BaseAIAgent
from .game_state import GameState


class GameObserver:
    """游戏观察器界面"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化游戏观察器
        
        Args:
            config: 游戏配置
        """
        self.config = config
        self.ui_settings = config.get("ui_settings", {})
        self.display_thinking = self.ui_settings.get("display_thinking", True)
        self.auto_scroll = self.ui_settings.get("auto_scroll", True)
        self.save_logs = self.ui_settings.get("save_logs", True)
        
        # 日志设置
        self.logger = logging.getLogger(__name__)
        
        # 显示缓冲区
        self.display_buffer = []
        self.max_buffer_size = 1000
        
        # 角色颜色映射
        self.role_colors = {
            "villager": Fore.GREEN,
            "werewolf": Fore.RED,
            "seer": Fore.BLUE,
            "witch": Fore.MAGENTA,
            "unknown": Fore.WHITE
        }
        
        # 事件颜色映射
        self.event_colors = {
            "death": Fore.RED + Style.BRIGHT,
            "vote": Fore.YELLOW,
            "speech": Fore.CYAN,
            "night_action": Fore.BLUE,
            "phase_change": Fore.MAGENTA + Style.BRIGHT,
            "game_end": Fore.GREEN + Style.BRIGHT
        }
    
    def display_game_start(self, players: List[Dict[str, Any]]) -> None:
        """
        显示游戏开始信息
        
        Args:
            players: 玩家列表
        """
        self._print_header("🎮 AI狼人杀游戏开始！")
        
        print(f"{Fore.CYAN}游戏设置：")
        print(f"  总玩家数: {len(players)}")
        
        # 显示回合数限制信息
        max_rounds = self.config.get('game_settings', {}).get('max_rounds')
        if max_rounds:
            print(f"  游戏模式: 最多{max_rounds}轮，达到限制后结束")
        else:
            print(f"  游戏模式: 无轮次限制，持续到胜负分出")
            
        print(f"  AI模型: {self.config.get('ai_settings', {}).get('model_name', 'deepseek-r1:8b')}")
        
        print(f"\n{Fore.YELLOW}玩家名单：")
        show_roles_to_user = self.ui_settings.get("show_roles_to_user", True)
        for player in players:
            if show_roles_to_user:
                role_color = self.role_colors.get(player.get("role", "unknown"), Fore.WHITE)
                role_name = self._get_role_display_name(player.get("role", "unknown"))
                print(f"  {role_color}玩家{player['id']} - {player['name']} ({role_name})")
            else:
                print(f"  {Fore.WHITE}玩家{player['id']} - {player['name']}")
        
        print(f"\n{Fore.GREEN}🎯 观看AI们的智慧博弈吧！")
        self._print_separator()
        
        # 记录到缓冲区
        self._add_to_buffer("game_start", f"游戏开始，{len(players)}名玩家参与")
    
    def display_phase_transition(self, phase: str, round_num: int, additional_info: str = "") -> None:
        """
        显示阶段转换
        
        Args:
            phase: 新阶段名称
            round_num: 回合数
            additional_info: 额外信息
        """
        phase_emoji = {
            "night": "🌙",
            "day": "☀️",
            "discussion": "💬",
            "voting": "🗳️",
            "game_end": "🏁"
        }
        
        emoji = phase_emoji.get(phase, "⏰")
        phase_display = self._get_phase_display_name(phase)
        
        self._print_section_header(f"{emoji} 第{round_num}轮 - {phase_display}")
        
        if additional_info:
            print(f"{Fore.YELLOW}{additional_info}")
        
        if phase == "night":
            print(f"{Fore.BLUE}夜幕降临，特殊角色开始行动...")
        elif phase == "day":
            print(f"{Fore.YELLOW}天亮了！让我们看看昨晚发生了什么...")
        elif phase == "discussion":
            print(f"{Fore.CYAN}讨论时间开始，AI们将展开智慧的较量...")
        elif phase == "voting":
            print(f"{Fore.MAGENTA}投票时间！谁将被放逐？")
        
        print()
        
        # 记录到缓冲区
        self._add_to_buffer("phase_change", f"第{round_num}轮 {phase_display} 开始")
    
    def display_player_speech(self, player: BaseAIAgent, speech: str, context: str = "") -> None:
        """
        显示玩家发言
        
        Args:
            player: 发言玩家
            speech: 发言内容
            context: 上下文信息
        """
        show_roles_to_user = self.ui_settings.get("show_roles_to_user", True)
        
        # 格式化发言时间
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        if show_roles_to_user:
            role_color = self.role_colors.get(player.role, Fore.WHITE)
            role_display = self._get_role_display_name(player.role)
            print(f"{Fore.CYAN}[{timestamp}] {role_color}🗣️ {player.name} ({role_display}):")
        else:
            print(f"{Fore.CYAN}[{timestamp}] 🗣️ {player.name}:")
        
        # 分行显示长发言
        wrapped_speech = self._wrap_text(speech, 80)
        for line in wrapped_speech:
            print(f"    {Fore.WHITE}{line}")
        
        if context:
            # 使用更兼容的颜色方式，避免Style.DIM兼容性问题
            dim_style = getattr(Style, 'DIM', '') if COLORAMA_AVAILABLE else ''
            print(f"    {dim_style}{Fore.CYAN}💭 {context}{Style.RESET_ALL if COLORAMA_AVAILABLE else ''}")
        
        print()
        
        # 记录到缓冲区
        self._add_to_buffer("speech", f"{player.name}: {speech[:50]}...")
        
        # 自动滚动
        if self.auto_scroll:
            time.sleep(1)
    
    def display_night_action(self, action_summary: str, details: Optional[Dict[str, Any]] = None) -> None:
        """
        显示夜晚行动
        
        Args:
            action_summary: 行动摘要
            details: 详细信息
        """
        print(f"{Fore.BLUE}🌙 夜晚行动: {action_summary}")
        
        if details and self.display_thinking:
            for key, value in details.items():
                if key != "action_summary":
                    # 修复Style.DIM兼容性问题
                    dim_style = getattr(Style, 'DIM', '') if COLORAMA_AVAILABLE else ''
                    print(f"    {dim_style}{Fore.CYAN}{key}: {value}{Style.RESET_ALL if COLORAMA_AVAILABLE else ''}")
        
        print()
        
        # 记录到缓冲区
        self._add_to_buffer("night_action", action_summary)
    
    def display_voting_process(self, votes: Dict[int, int], result: Dict[str, Any]) -> None:
        """
        显示投票过程
        
        Args:
            votes: 投票统计
            result: 投票结果
        """
        print(f"{Fore.YELLOW}🗳️ 投票结果统计：")
        
        # 按得票数排序显示
        sorted_votes = sorted(votes.items(), key=lambda x: x[1], reverse=True)
        
        for player_id, vote_count in sorted_votes:
            percentage = (vote_count / max(1, sum(votes.values()))) * 100
            bar_length = int(percentage / 5)  # 每5%一个字符
            bar = "█" * bar_length + "░" * (20 - bar_length)
            
            print(f"  玩家{player_id}: {vote_count}票 {percentage:5.1f}% {Fore.GREEN}{bar}{Fore.RESET}")
        
        # 显示结果
        if result.get("is_tie"):
            tied_players = result.get("tied_players", [])
            print(f"\n{Fore.YELLOW}⚖️ 平票！涉及玩家: {', '.join(f'玩家{p}' for p in tied_players)}")
        
        final_target = result.get("final_target")
        if final_target:
            print(f"\n{Fore.RED}📤 最终结果: 玩家{final_target} 被放逐")
        else:
            print(f"\n{Fore.BLUE}📤 最终结果: 无人被放逐")
        
        print()
        
        # 记录到缓冲区
        vote_summary = f"投票完成，目标: 玩家{final_target}" if final_target else "投票完成，无人出局"
        self._add_to_buffer("vote", vote_summary)
    
    def display_death_announcement(self, player_info: Dict[str, Any], cause: str) -> None:
        """
        显示死亡公告
        
        Args:
            player_info: 死者信息
            cause: 死亡原因
        """
        reveal_roles = self.ui_settings.get("reveal_roles_on_death", True)
        
        print(f"{Fore.RED}💀 死亡公告:")
        print(f"  {Fore.WHITE}玩家{player_info['id']} - {player_info['name']}")
        
        if reveal_roles:
            role_display = self._get_role_display_name(player_info.get("role", "unknown"))
            print(f"  {Fore.YELLOW}身份: {role_display}")
            print(f"  {Fore.RED}死因: {cause}")
            # 记录到缓冲区
            self._add_to_buffer("death", f"{player_info['name']} ({role_display}) 死亡: {cause}")
        else:
            print(f"  {Fore.RED}死因: {cause}")
            # 记录到缓冲区  
            self._add_to_buffer("death", f"{player_info['name']} 死亡: {cause}")
        
        print()
    
    def display_game_end(self, winner: str, summary: Dict[str, Any]) -> None:
        """
        显示游戏结束
        
        Args:
            winner: 获胜方
            summary: 游戏总结
        """
        self._print_header("🏁 游戏结束！")
        
        # 显示获胜方
        if winner == "villagers":
            print(f"{Fore.GREEN + Style.BRIGHT}🎉 村民阵营获胜！")
        elif winner == "werewolves":
            print(f"{Fore.RED + Style.BRIGHT}🐺 狼人阵营获胜！")
        else:
            print(f"{Fore.YELLOW + Style.BRIGHT}🤝 平局！")
        
        # 显示胜利原因
        reason = summary.get("victory_reason", "未知原因")
        print(f"{Fore.CYAN}胜利原因: {reason}")
        
        # 显示游戏统计
        print(f"\n{Fore.YELLOW}📊 游戏统计:")
        print(f"  总回合数: {summary.get('total_rounds', 0)}")
        print(f"  游戏时长: {self._format_duration(summary.get('game_duration_seconds', 0))}")
        print(f"  总事件数: {summary.get('total_events', 0)}")
        print(f"  投票轮数: {summary.get('voting_rounds', 0)}")
        
        # 显示最终阵营状况
        final_counts = summary.get("final_faction_counts", {})
        print(f"\n{Fore.MAGENTA}🏛️ 最终阵营状况:")
        print(f"  存活村民: {final_counts.get('villagers', 0)}")
        print(f"  存活狼人: {final_counts.get('werewolves', 0)}")
        print(f"  总存活数: {final_counts.get('total_alive', 0)}")
        
        # 显示角色统计
        role_summary = summary.get("role_summary", {})
        if role_summary:
            print(f"\n{Fore.BLUE}👥 角色统计:")
            for role, stats in role_summary.items():
                role_display = self._get_role_display_name(role)
                print(f"  {role_display}: {stats['total']}人 (存活{stats['alive']}, 死亡{stats['dead']})")
        
        self._print_separator()
        print(f"{Fore.GREEN}感谢观看AI狼人杀！")
        
        # 记录到缓冲区
        self._add_to_buffer("game_end", f"游戏结束，{winner}获胜")
    
    def display_round_limit_reached(self, max_rounds: int) -> None:
        """
        显示达到回合数限制
        
        Args:
            max_rounds: 最大回合数
        """
        self._print_section_header(f"⏰ 达到最大回合数限制: {max_rounds}")
        print(f"{Fore.YELLOW}游戏已达到配置的最大回合数限制，游戏结束。")
        print(f"{Fore.CYAN}如果没有回合数限制，游戏将继续进行直到胜负分出。")
        print()
        
        # 记录到缓冲区
        self._add_to_buffer("round_limit", f"达到最大回合数限制: {max_rounds}")
    
    def display_thinking_process(self, player: BaseAIAgent, thinking: str) -> None:
        """
        显示AI思考过程（如果启用）
        
        Args:
            player: 思考的玩家
            thinking: 思考内容
        """
        if not self.display_thinking:
            return
        
        role_color = self.role_colors.get(player.role, Fore.WHITE)
        
        # 修复Style.DIM兼容性问题
        dim_style = getattr(Style, 'DIM', '') if COLORAMA_AVAILABLE else ''
        print(f"{dim_style}💭 {role_color}{player.name} 思考中...{Style.RESET_ALL if COLORAMA_AVAILABLE else ''}")
        
        # 简化思考内容显示
        thinking_lines = thinking.split('\n')[:3]  # 只显示前3行
        for line in thinking_lines:
            if line.strip():
                print(f"    {dim_style}> {line.strip()[:60]}...{Style.RESET_ALL if COLORAMA_AVAILABLE else ''}")
        
        print()
    
    def display_game_status(self, game_state: GameState, victory_probs: Optional[Dict[str, float]] = None) -> None:
        """
        显示当前游戏状态
        
        Args:
            game_state: 游戏状态
            victory_probs: 胜利概率（可选）
        """
        print(f"{Fore.CYAN}📊 当前状态: 第{game_state.current_round}轮 {game_state.current_phase.value}")
        
        # 显示存活玩家
        faction_counts = game_state.get_faction_counts()
        print(f"  存活: {faction_counts['total_alive']}人 (村民{faction_counts['villagers']}, 狼人{faction_counts['werewolves']})")
        
        # 显示胜利概率
        if victory_probs:
            print(f"  胜率预测: 村民{victory_probs.get('villagers', 0):.1%}, 狼人{victory_probs.get('werewolves', 0):.1%}")
        
        print()
    
    def _get_role_display_name(self, role: str) -> str:
        """获取角色显示名称"""
        role_names = {
            "villager": "村民",
            "werewolf": "狼人",
            "seer": "预言家",
            "witch": "女巫"
        }
        return role_names.get(role, role)
    
    def _get_phase_display_name(self, phase: str) -> str:
        """获取阶段显示名称"""
        phase_names = {
            "preparation": "准备阶段",
            "night": "夜晚",
            "day": "白天",
            "discussion": "讨论阶段",
            "voting": "投票阶段",
            "game_end": "游戏结束"
        }
        return phase_names.get(phase, phase)
    
    def _wrap_text(self, text: str, width: int) -> List[str]:
        """文本换行"""
        if len(text) <= width:
            return [text]
        
        lines = []
        words = text.split()
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= width:
                current_line += (" " if current_line else "") + word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
    
    def _format_duration(self, seconds: float) -> str:
        """格式化时长"""
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            minutes = seconds // 60
            secs = seconds % 60
            return f"{minutes:.0f}分{secs:.0f}秒"
        else:
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            return f"{hours:.0f}小时{minutes:.0f}分"
    
    def _print_header(self, title: str) -> None:
        """打印标题头"""
        print(f"\n{Style.BRIGHT}{Fore.YELLOW}{'=' * 60}")
        print(f"{Style.BRIGHT}{Fore.YELLOW}{title:^60}")
        print(f"{Style.BRIGHT}{Fore.YELLOW}{'=' * 60}")
    
    def _print_section_header(self, title: str) -> None:
        """打印章节头"""
        print(f"\n{Style.BRIGHT}{Fore.MAGENTA}{'-' * 40}")
        print(f"{Style.BRIGHT}{Fore.MAGENTA}{title}")
        print(f"{Style.BRIGHT}{Fore.MAGENTA}{'-' * 40}")
    
    def _print_separator(self) -> None:
        """打印分隔线"""
        # 修复Style.DIM兼容性问题
        dim_style = getattr(Style, 'DIM', '') if COLORAMA_AVAILABLE else ''
        print(f"{dim_style}{'-' * 60}{Style.RESET_ALL if COLORAMA_AVAILABLE else ''}")
    
    def _add_to_buffer(self, event_type: str, content: str) -> None:
        """添加到显示缓冲区"""
        timestamp = datetime.now().isoformat()
        self.display_buffer.append({
            "timestamp": timestamp,
            "event_type": event_type,
            "content": content
        })
        
        # 限制缓冲区大小
        if len(self.display_buffer) > self.max_buffer_size:
            self.display_buffer = self.display_buffer[-self.max_buffer_size:]
    
    def save_game_log(self, filename: Optional[str] = None) -> str:
        """
        保存游戏日志
        
        Args:
            filename: 文件名（可选）
            
        Returns:
            保存的文件路径
        """
        if not self.save_logs:
            return ""
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"logs/werewolf_game_{timestamp}.log"
        
        import os
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write("AI狼人杀游戏日志\n")
                f.write("=" * 50 + "\n\n")
                
                for entry in self.display_buffer:
                    f.write(f"[{entry['timestamp']}] {entry['event_type']}: {entry['content']}\n")
            
            self.logger.info(f"游戏日志已保存到: {filename}")
            return filename
            
        except Exception as e:
            self.logger.error(f"保存日志失败: {e}")
            return ""
    
    def clear_screen(self) -> None:
        """清除屏幕"""
        import os
        os.system('cls' if os.name == 'nt' else 'clear') 