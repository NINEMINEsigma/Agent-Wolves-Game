#!/usr/bin/env python3
"""
测试记忆改进功能
验证玩家发言记忆和上下文管理的改进
"""

import asyncio
import json
import sys
from pathlib import Path

# 添加src目录到路径
sys.path.append(str(Path(__file__).parent / "src"))

from src.ai_agent import BaseAIAgent
from src.llm_interface import QwenInterface
from src.identity_system import IdentitySystem


async def test_memory_improvements():
    """测试记忆改进功能"""
    print("🧪 测试记忆改进功能")
    print("=" * 50)
    
    # 加载配置
    with open("config.json", "r", encoding="utf-8") as f:
        config = json.load(f)
    
    # 创建LLM接口
    llm_interface = QwenInterface(config["ai_settings"])
    
    # 创建身份系统
    identity_system = IdentitySystem()
    
    # 获取记忆配置
    memory_config = config.get("memory_settings", {})
    
    # 创建测试玩家
    test_player = TestPlayer(
        player_id=1,
        name="测试玩家",
        role="villager",
        llm_interface=llm_interface,
        prompts={},
        identity_system=identity_system,
        memory_config=memory_config
    )
    
    print(f"✅ 创建测试玩家: {test_player.name}")
    print(f"📋 记忆配置: {memory_config}")
    
    # 测试记忆更新
    print("\n📝 测试记忆更新功能...")
    
    # 添加一些测试发言
    test_speeches = [
        {
            "speaker": "玩家2",
            "speaker_id": 2,
            "content": "我觉得玩家3的行为很可疑，他一直在转移话题，没有正面回答我的问题。",
            "round": 1,
            "context": "正常发言"
        },
        {
            "speaker": "玩家3", 
            "speaker_id": 3,
            "content": "我不同意玩家2的说法，我只是在分析局势，没有转移话题。",
            "round": 1,
            "context": "正常发言"
        },
        {
            "speaker": "玩家4",
            "speaker_id": 4,
            "content": "我觉得我们需要更仔细地观察每个人的发言逻辑，不能轻易下结论。",
            "round": 1,
            "context": "正常发言"
        }
    ]
    
    for speech in test_speeches:
        test_player.update_memory("speeches", speech)
        print(f"   ✅ 添加发言: {speech['speaker']} - {speech['content'][:30]}...")
    
    # 测试记忆格式化
    print("\n📋 测试记忆格式化功能...")
    memory_context = test_player.format_memory_context()
    print(f"记忆上下文长度: {len(memory_context)} 字符")
    print(f"记忆内容预览:\n{memory_context[:200]}...")
    
    # 测试获取当前轮次发言
    print("\n🔄 测试获取当前轮次发言...")
    current_round_speeches = test_player.get_current_round_speeches(1)
    print(f"第1轮发言数量: {len(current_round_speeches)}")
    
    # 测试获取指定玩家之前的发言
    print("\n👥 测试获取指定玩家之前的发言...")
    previous_speeches = test_player.get_speeches_before_player(3, 1)
    print(f"玩家3之前的发言数量: {len(previous_speeches)}")
    
    # 测试配置参数
    print("\n⚙️ 测试配置参数...")
    print(f"最大发言长度: {test_player.max_speech_length}")
    print(f"最大记忆事件数: {test_player.max_memory_events}")
    print(f"发言内容截断: {test_player.speech_content_truncate}")
    print(f"上下文长度限制: {test_player.context_length_limit}")
    
    print("\n✅ 记忆改进功能测试完成！")


class TestPlayer(BaseAIAgent):
    """测试用的玩家类"""
    
    async def make_speech(self, game_state):
        return "测试发言"
    
    async def vote(self, game_state, candidates):
        return candidates[0] if candidates else 1
    
    async def night_action(self, game_state):
        return {"action": "test", "success": True}


if __name__ == "__main__":
    asyncio.run(test_memory_improvements()) 