#!/usr/bin/env python3
"""
翻译系统测试脚本
验证翻译配置加载和翻译方法功能
"""

import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.translation_manager import TranslationManager

def test_translation_system():
    """测试翻译系统"""
    print("🔍 翻译系统测试")
    print("=" * 50)
    
    # 创建翻译管理器
    tm = TranslationManager()
    
    # 测试角色翻译
    print("\n📋 角色翻译测试:")
    roles = ["villager", "werewolf", "seer", "witch", "hunter", "guard", "unknown_role"]
    for role in roles:
        translated = tm.get_role_name(role)
        print(f"  {role} -> {translated}")
    
    # 测试阶段翻译
    print("\n⏰ 阶段翻译测试:")
    phases = ["preparation", "night", "day", "discussion", "voting", "game_end", "unknown_phase"]
    for phase in phases:
        translated = tm.get_phase_name(phase)
        print(f"  {phase} -> {translated}")
    
    # 测试游戏术语翻译
    print("\n🎮 游戏术语测试:")
    terms = ["victory", "defeat", "alive", "dead", "round", "player", "unknown_term"]
    for term in terms:
        translated = tm.get_game_term(term)
        print(f"  {term} -> {translated}")
    
    # 测试UI消息翻译
    print("\n💬 UI消息测试:")
    messages = ["game_start", "game_settings", "player_list_title", "unknown_message"]
    for message in messages:
        translated = tm.get_ui_message(message)
        print(f"  {message} -> {translated}")
    
    # 测试嵌套路径翻译
    print("\n🔗 嵌套路径测试:")
    nested_keys = ["roles.villager", "phases.night", "game_terms.victory", "ui_messages.game_start"]
    for key in nested_keys:
        translated = tm.get_translation(key)
        print(f"  {key} -> {translated}")
    
    # 测试错误处理
    print("\n⚠️ 错误处理测试:")
    error_cases = ["", "invalid.key.path", "roles.nonexistent"]
    for case in error_cases:
        translated = tm.get_translation(case, "默认值")
        print(f"  '{case}' -> {translated}")
    
    print("\n✅ 翻译系统测试完成！")

if __name__ == "__main__":
    test_translation_system() 