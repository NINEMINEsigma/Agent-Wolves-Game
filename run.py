#!/usr/bin/env python3
"""
AI狼人杀游戏主启动文件
基于DeepSeek和LlamaIndex的AI多智能体狼人杀游戏
"""

import asyncio
import json
import sys
import os
from pathlib import Path

def print_welcome():
    """打印欢迎信息"""
    print("=" * 60)
    print("🎮 Agent-Wolves 狼人杀游戏")
    print("=" * 60)
    print("🤖 基于AI多智能体对战")
    print("👀 作为观察者，观看AI们的博弈")
    print("🔧 支持Agent模式")
    print("=" * 60)

def check_environment():
    """检查环境配置"""
    print("\n🔍 检查环境配置...")
    
    # 检查必要文件
    required_files = [
        'config.json',
        'prompts/role_prompts.json',
        'prompts/game_prompts.json',
    ]
    
    missing_files = []
    for file_path in required_files:
        if not Path(file_path).exists():
            missing_files.append(file_path)
    
    if missing_files:
        print("❌ 缺少以下必要文件:")
        for file in missing_files:
            print(f"   - {file}")
        return False
    
    print("✅ 所有必要文件检查通过")
    
    # 检查配置文件有效性
    try:
        from src.config_validator import ConfigValidator
        validator = ConfigValidator()
        config = validator.load_config()
        
        # 验证游戏设置
        game_validation = validator.validate_game_settings(config)
        role_validation = validator.validate_role_distribution(config)
        
        print("\n📋 游戏配置检查:")
        
        # 显示配置信息
        game_settings = config.get("game_settings", {})
        print(f"   总玩家数: {game_settings.get('total_players', '未设置')}")
        
        # 显示回合数限制信息
        max_rounds = game_settings.get('max_rounds')
        if max_rounds:
            print(f"   最大回合数: {max_rounds}")
        else:
            print(f"   最大回合数: 无限制")
            
        print(f"   角色分配: {game_settings.get('roles', {})}")
        
        # 检查验证结果
        all_valid = all(game_validation.values()) and role_validation["is_valid"]
        
        if all_valid:
            print("✅ 游戏配置验证通过")
        else:
            print("⚠️ 游戏配置存在问题:")
            
            # 显示游戏设置问题
            for setting, is_valid in game_validation.items():
                if not is_valid:
                    print(f"   - {setting}: 配置无效")
            
            # 显示角色分配问题
            if not role_validation["is_valid"]:
                print("   - 角色分配问题:")
                for issue in role_validation["issues"]:
                    print(f"     * {issue}")
            
            # 提供修复建议
            suggestions = validator.suggest_config_fixes({
                "role_distribution": role_validation
            })
            if suggestions:
                print("   - 修复建议:")
                for suggestion in suggestions:
                    print(f"     * {suggestion}")
            
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ 配置检查失败: {e}")
        return False

def check_ollama_connection():
    """检查Ollama连接"""
    print("\n🔗 检查Ollama连接...")
    
    try:
        import requests
        import json
        
        # 从配置文件读取设置
        try:
            with open('config.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
            ollama_url = config.get("ai_settings").get("ollama_base_url", "http://localhost:11434")
            model_name = config.get("ai_settings").get("model_name")
        except Exception as e:
            print(f"❌ 配置文件读取失败: {e}")
            return False
        
        response = requests.get(f"{ollama_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get("models", [])
            model_names = [model.get("name", "") for model in models]
            
            # 检查是否有配置的模型
            has_model = any(model_name in name for name in model_names)
            
            if has_model:
                print(f"✅ Ollama连接成功，{model_name}模型可用")
                return True
            else:
                print(f"⚠️ Ollama连接成功，但未找到{model_name}模型")
                print("   可用模型:", model_names)
                return False
        else:
            print(f"❌ Ollama服务器响应异常: {response.status_code}")
            return False
    except ImportError:
        print("❌ 缺少requests库，请运行: pip install requests")
        return False
    except Exception as e:
        print(f"❌ 无法连接到Ollama: {e}")
        return False

def print_setup_guide():
    """打印设置指南"""
    print("\n" + "=" * 60)
    print("📋 环境设置指南")
    print("=" * 60)
    
    # 从配置文件读取设置
    try:
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        model_name = config.get("ai_settings", {}).get("model_name", "qwen3:0.6b")
        ollama_url = config.get("ai_settings", {}).get("ollama_base_url", "http://localhost:11434")
    except:
        model_name = "qwen3:0.6b"
        ollama_url = "http://localhost:11434"
    
    print("\n1️⃣ 安装Python依赖包：")
    print("   pip install -r requirements.txt")
    
    print("\n2️⃣ 安装Ollama (如未安装)：")
    print("   - Windows: 下载 https://ollama.ai/download")
    print("   - macOS: brew install ollama")
    print("   - Linux: curl -fsSL https://ollama.ai/install.sh | sh")
    
    print(f"\n3️⃣ 下载{model_name}模型：")
    print(f"   ollama pull {model_name}")
    
    print("\n4️⃣ 启动Ollama服务：")
    print("   ollama serve")
    print("   (在新终端窗口中运行，保持运行状态)")
    
    print("\n5️⃣ 验证安装：")
    print(f"   curl {ollama_url}/api/tags")
    
    print("\n6️⃣ 重新运行此脚本：")
    print("   python run.py")
    
    print("\n" + "=" * 60)

async def test_basic_ai():
    """测试基础AI功能"""
    print("\n🧪 进行基础AI测试...")
    
    try:
        from src.llm_interface import LLMInterface
        from src.config_validator import ConfigValidator
        
        # 使用配置验证器加载配置
        validator = ConfigValidator()
        config = validator.load_config()
        
        # 创建LLM接口
        llm = LLMInterface(config)
        
        # 简单测试
        response = await llm.generate_response(
            "请简单回复：AI狼人杀游戏测试成功！",
            "你是一个友好的AI助手。"
        )
        
        print(f"✅ AI测试成功!")
        print(f"🤖 AI回复: {response}")
        return True
        
    except Exception as e:
        print(f"❌ AI测试失败: {e}")
        return False

async def start_simple_demo():
    """启动简单演示"""
    print("\n🎭 启动AI角色演示...")
    
    try:
        # 添加src目录到路径
        src_path = os.path.join(os.path.dirname(__file__), 'src')
        if src_path not in sys.path:
            sys.path.insert(0, src_path)
        
        from src.llm_interface import LLMInterface
        
        from src.config_validator import ConfigValidator
        
        # 使用配置验证器加载配置
        validator = ConfigValidator()
        config = validator.load_config()
        
        with open('prompts/role_prompts.json', 'r', encoding='utf-8') as f:
            role_prompts = json.load(f)
        
        # 创建LLM接口和Agent工厂
        llm = LLMInterface(config)
        from src.agents.agent_factory import AgentFactory
        factory = AgentFactory(config)
        
        # 创建村民Agent
        villager = factory.create_agent(1, "演示村民", "villager", llm, role_prompts)
        
        print(f"✅ 成功创建Agent: {villager}")
        
        # 简单的发言测试
        game_state = {
            "current_round": 1,
            "phase": "讨论",
            "alive_players": [{"id": 1, "name": "演示村民"}],
            "dead_players": []
        }
        
        print("\n💬 AI发言演示:")
        speech = await villager.make_speech(game_state)
        print(f"🏠 {villager.name}: {speech}")
        
        print("\n🎉 基础演示完成！")
        return True
        
    except Exception as e:
        print(f"❌ 演示失败: {e}")
        print(f"错误详情: {str(e)}")
        return False

async def start_full_game():
    """启动完整游戏"""
    print("\n🎮 启动完整AI狼人杀游戏...")
    
    try:
        # 添加src目录到路径
        # src_path = os.path.join(os.path.dirname(__file__), 'src')
        # if src_path not in sys.path:
        #     sys.path.insert(0, src_path)
        
        from src.werewolf_game import WerewolfGame
        
        # 创建游戏实例
        game = WerewolfGame("config.json")
        
        # 环境检查
        print("\n🔍 进行环境检查...")
        print(game.get_environment_report())
        
        # 询问是否继续
        if not all(game.validate_environment().values()):
            response = input("\n⚠️ 检测到环境问题，是否继续启动游戏？(y/N): ").strip().lower()
            if response != 'y':
                print("游戏启动已取消")
                return
        
        # 初始化游戏
        print("\n⚙️ 初始化游戏组件...")
        init_success = await game.initialize()
        
        if not init_success:
            print("❌ 游戏初始化失败")
            return
        
        print("✅ 游戏初始化成功")
        
        # 显示玩家信息
        players = game.get_player_info()
        print(f"\n👥 已创建 {len(players)} 名AI玩家：")
        for player in players:
            print(f"  🤖 {player['name']} - {player['role']}")
        
        # 询问游戏模式
        print("\n📋 选择游戏模式：")
        print("1. 🎮 完整游戏")
        print("2. ⚡ 快速演示")
        
        mode_choice = input("\n👉 请选择模式 (1-2): ").strip()
        
        if mode_choice == '2':
            print("\n⚡ 启动快速演示模式...")
            result = await game.quick_demo()
        else:
            print("\n🎮 启动完整游戏...")
            result = await game.start()
        
        # 显示结果
        if result.get("success"):
            print(f"\n🎊 游戏成功完成！")
            print(f"🏆 获胜方: {result.get('winner', 'unknown')}")
            print(f"🔢 总回合数: {result.get('total_rounds', 0)}")
            
            if result.get("log_file"):
                print(f"📄 游戏日志: {result['log_file']}")
        else:
            print(f"\n❌ 游戏执行失败: {result.get('error', '未知错误')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 完整游戏启动失败: {e}")
        print(f"错误详情: {str(e)}")
        return False

def show_menu():
    """显示主菜单"""
    print("\n" + "=" * 40)
    print("📋 选择操作:")
    print("=" * 40)
    print("1. 🧪 基础AI连接测试")
    print("2. 🎭 AI角色演示")
    print("3. 🎮 启动完整游戏")
    print("4. 📋 查看设置指南")
    print("5. 🚪 退出")
    print("=" * 40)

async def main():
    """主函数"""
    print_welcome()
    
    # 检查环境
    if not check_environment():
        print("\n❌ 环境检查失败，请完成文件配置")
        return
    
    # 检查Ollama
    ollama_ok = check_ollama_connection()
    
    if not ollama_ok:
        print_setup_guide()
        return
    
    # 主循环
    while True:
        show_menu()
        
        try:
            choice = input("\n👉 请选择操作 (1-5): ").strip()
            
            if choice == '1':
                await test_basic_ai()
            elif choice == '2':
                await start_simple_demo()
            elif choice == '3':
                await start_full_game()
            elif choice == '4':
                print_setup_guide()
            elif choice == '5':
                print("\n👋 感谢使用AI狼人杀游戏！")
                break
            else:
                print("\n❌ 无效选择，请输入1-5")
                
        except KeyboardInterrupt:
            print("\n\n👋 游戏已退出")
            break
        except Exception as e:
            print(f"\n❌ 操作出错: {e}")

if __name__ == "__main__":
    asyncio.run(main())
