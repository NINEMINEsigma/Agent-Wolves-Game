#!/usr/bin/env python3
"""
夜晚记忆改进功能测试脚本

测试内容：
1. 夜晚讨论记忆的完整记录
2. 夜晚思考记忆的存储和访问
3. 记忆上下文的正确格式化
4. 狼人能够记住群体讨论内容
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# 添加src目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from ai_agent import BaseAIAgent
from qwen_interface import QwenInterface
from identity_system import IdentitySystem

class MockAIAgent(BaseAIAgent):
    """模拟AI代理用于测试"""
    
    async def make_speech(self, game_state):
        return "测试发言"
    
    async def vote(self, game_state, candidates):
        return candidates[0] if candidates else 1
    
    async def night_action(self, game_state):
        return {"success": True, "action": "test"}

class NightMemoryTester:
    """夜晚记忆测试器"""
    
    def __init__(self):
        self.test_results = []
        
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """记录测试结果"""
        result = {
            "test_name": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} {test_name}: {details}")
    
    def test_memory_initialization(self):
        """测试记忆系统初始化"""
        print("\n🧪 测试1: 记忆系统初始化")
        
        # 创建模拟LLM接口
        llm_interface = QwenInterface("test_model", "http://localhost:11434")
        
        # 创建记忆配置
        memory_config = {
            "max_memory_events": 50,
            "night_discussion_memory_limit": 20,
            "night_thinking_memory_limit": 15,
            "include_night_context_in_speech": True
        }
        
        # 创建AI代理
        agent = MockAIAgent(
            player_id=1,
            name="测试玩家",
            role="werewolf",
            llm_interface=llm_interface,
            prompts={},
            memory_config=memory_config
        )
        
        # 验证记忆类型是否正确初始化
        expected_memory_types = ["speeches", "votes", "night_actions", "observations", "night_discussions", "night_thinking"]
        actual_memory_types = list(agent.game_memory.keys())
        
        success = all(memory_type in actual_memory_types for memory_type in expected_memory_types)
        self.log_test(
            "记忆类型初始化",
            success,
            f"期望: {expected_memory_types}, 实际: {actual_memory_types}"
        )
        
        # 验证配置是否正确应用
        success = (
            agent.night_discussion_memory_limit == 20 and
            agent.night_thinking_memory_limit == 15 and
            agent.include_night_context_in_speech == True
        )
        self.log_test(
            "记忆配置应用",
            success,
            f"夜晚讨论限制: {agent.night_discussion_memory_limit}, 夜晚思考限制: {agent.night_thinking_memory_limit}"
        )
        
        return agent
    
    def test_night_discussion_memory(self, agent):
        """测试夜晚讨论记忆"""
        print("\n🧪 测试2: 夜晚讨论记忆")
        
        # 模拟夜晚讨论数据
        discussion_data = {
            "round": 1,
            "discussion_round": 1,
            "speaker_id": 2,
            "speaker_name": "狼人2",
            "content": "我建议今晚击杀玩家3，他的发言很可疑。",
            "speech_type": "opening_analysis",
            "context": "狼人夜晚群体讨论"
        }
        
        # 更新夜晚讨论记忆
        agent.update_night_discussion_memory(discussion_data)
        
        # 验证记忆是否正确存储
        discussions = agent.get_night_discussions_by_round(1)
        success = len(discussions) == 1 and discussions[0]["content"] == discussion_data["content"]
        self.log_test(
            "夜晚讨论记忆存储",
            success,
            f"存储了 {len(discussions)} 条讨论记录"
        )
        
        # 测试记忆格式化
        formatted_context = agent.format_night_discussion_context(discussions)
        success = "夜晚讨论记录:" in formatted_context and "狼人2" in formatted_context
        self.log_test(
            "夜晚讨论记忆格式化",
            success,
            f"格式化结果长度: {len(formatted_context)}"
        )
        
        return discussions
    
    def test_night_thinking_memory(self, agent):
        """测试夜晚思考记忆"""
        print("\n🧪 测试3: 夜晚思考记忆")
        
        # 模拟夜晚思考数据
        thinking_data = {
            "round": 1,
            "role": "预言家",
            "thinking_content": "我需要查验玩家2的身份，他的行为很可疑。",
            "decision_factors": {
                "game_phase": 1,
                "player_count": 8,
                "priority": "identity_confirmation"
            },
            "context": "预言家夜晚查验思考"
        }
        
        # 更新夜晚思考记忆
        agent.update_night_thinking_memory(thinking_data)
        
        # 验证记忆是否正确存储
        thinking_records = agent.get_night_thinking_by_round(1)
        success = len(thinking_records) == 1 and thinking_records[0]["thinking_content"] == thinking_data["thinking_content"]
        self.log_test(
            "夜晚思考记忆存储",
            success,
            f"存储了 {len(thinking_records)} 条思考记录"
        )
        
        # 测试记忆格式化
        formatted_context = agent.format_night_thinking_context(thinking_records)
        success = "夜晚思考记录:" in formatted_context and "预言家" in formatted_context
        self.log_test(
            "夜晚思考记忆格式化",
            success,
            f"格式化结果长度: {len(formatted_context)}"
        )
        
        return thinking_records
    
    def test_memory_context_integration(self, agent):
        """测试记忆上下文整合"""
        print("\n🧪 测试4: 记忆上下文整合")
        
        # 添加一些发言记忆
        agent.update_memory("speeches", {
            "round": 1,
            "speaker": "玩家1",
            "content": "我是好人，请大家相信我。",
            "context": "白天讨论"
        })
        
        # 测试完整记忆上下文格式化
        full_context = agent.format_memory_context()
        
        # 验证是否包含夜晚记忆
        success = (
            "最近发言:" in full_context and
            "夜晚讨论记录:" in full_context and
            "夜晚思考记录:" in full_context
        )
        self.log_test(
            "记忆上下文整合",
            success,
            f"完整上下文长度: {len(full_context)}"
        )
        
        # 测试夜晚记忆上下文获取
        night_context = agent.get_night_memory_context(1)
        success = len(night_context) > 0 and ("夜晚讨论记录:" in night_context or "夜晚思考记录:" in night_context)
        self.log_test(
            "夜晚记忆上下文获取",
            success,
            f"夜晚上下文长度: {len(night_context)}"
        )
        
        return full_context
    
    def test_memory_limits(self, agent):
        """测试记忆限制功能"""
        print("\n🧪 测试5: 记忆限制功能")
        
        # 添加超过限制的夜晚讨论记录
        for i in range(25):  # 超过限制20条
            discussion_data = {
                "round": 1,
                "discussion_round": 1,
                "speaker_id": i,
                "speaker_name": f"狼人{i}",
                "content": f"讨论内容{i}",
                "speech_type": "opening_analysis",
                "context": "狼人夜晚群体讨论"
            }
            agent.update_night_discussion_memory(discussion_data)
        
        # 验证记忆是否被正确限制
        discussions = agent.get_night_discussions_by_round(1)
        success = len(discussions) <= agent.night_discussion_memory_limit
        self.log_test(
            "夜晚讨论记忆限制",
            success,
            f"实际记录数: {len(discussions)}, 限制: {agent.night_discussion_memory_limit}"
        )
        
        # 添加超过限制的夜晚思考记录
        for i in range(20):  # 超过限制15条
            thinking_data = {
                "round": 1,
                "role": "预言家",
                "thinking_content": f"思考内容{i}",
                "decision_factors": {"priority": "test"},
                "context": "预言家夜晚查验思考"
            }
            agent.update_night_thinking_memory(thinking_data)
        
        # 验证思考记忆是否被正确限制
        thinking_records = agent.get_night_thinking_by_round(1)
        success = len(thinking_records) <= agent.night_thinking_memory_limit
        self.log_test(
            "夜晚思考记忆限制",
            success,
            f"实际记录数: {len(thinking_records)}, 限制: {agent.night_thinking_memory_limit}"
        )
    
    def test_config_validation(self):
        """测试配置验证"""
        print("\n🧪 测试6: 配置验证")
        
        # 测试有效配置
        valid_config = {
            "memory_settings": {
                "night_discussion_memory_limit": 20,
                "night_thinking_memory_limit": 15,
                "include_night_context_in_speech": True
            }
        }
        
        try:
            from config_validator import ConfigValidator
            validator = ConfigValidator()
            validated_config = validator._validate_and_merge_config(valid_config)
            
            memory_settings = validated_config["memory_settings"]
            success = (
                memory_settings["night_discussion_memory_limit"] == 20 and
                memory_settings["night_thinking_memory_limit"] == 15 and
                memory_settings["include_night_context_in_speech"] == True
            )
            self.log_test(
                "有效配置验证",
                success,
                "配置验证通过"
            )
        except Exception as e:
            self.log_test(
                "有效配置验证",
                False,
                f"配置验证失败: {e}"
            )
    
    def run_all_tests(self):
        """运行所有测试"""
        print("🚀 开始夜晚记忆改进功能测试")
        print("=" * 50)
        
        # 测试1: 记忆系统初始化
        agent = self.test_memory_initialization()
        
        # 测试2: 夜晚讨论记忆
        self.test_night_discussion_memory(agent)
        
        # 测试3: 夜晚思考记忆
        self.test_night_thinking_memory(agent)
        
        # 测试4: 记忆上下文整合
        self.test_memory_context_integration(agent)
        
        # 测试5: 记忆限制功能
        self.test_memory_limits(agent)
        
        # 测试6: 配置验证
        self.test_config_validation()
        
        # 输出测试总结
        print("\n" + "=" * 50)
        print("📊 测试总结")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过: {passed_tests}")
        print(f"失败: {failed_tests}")
        print(f"成功率: {passed_tests/total_tests*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ 失败的测试:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test_name']}: {result['details']}")
        
        # 保存测试结果
        with open("night_memory_test_results.json", "w", encoding="utf-8") as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 测试结果已保存到: night_memory_test_results.json")
        
        return failed_tests == 0

async def main():
    """主函数"""
    tester = NightMemoryTester()
    success = tester.run_all_tests()
    
    if success:
        print("\n🎉 所有测试通过！夜晚记忆改进功能正常工作。")
        return 0
    else:
        print("\n⚠️ 部分测试失败，请检查相关功能。")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code) 