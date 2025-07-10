# AI狼人杀游戏 🎮

基于Qwen3-0.6B和Ollama的AI多智能体狼人杀游戏，用户作为观察者观看AI间的智慧博弈。

## 🌟 项目特色

- 🤖 **轻量高效**: 使用Qwen3-0.6B模型，仅523MB，快速响应
- 🧠 **思考模式**: 支持thinking/non-thinking双模式，深度推理能力
- 🎭 **多样角色**: 村民、狼人、预言家、女巫等经典角色
- 🌍 **中文优化**: 专为中文对话和角色扮演优化
- 👀 **观察模式**: 用户观看AI发言、投票、夜晚行动
- ⚡ **资源友好**: 低内存占用，适合各种硬件配置

## 🚀 快速开始

### 第一步：环境准备

1. **安装Python依赖**：
   ```bash
   pip install -r requirements.txt
   ```

2. **安装Ollama**：
   - Windows: 下载 https://ollama.ai/download
   - macOS: `brew install ollama`
   - Linux: `curl -fsSL https://ollama.ai/install.sh | sh`

3. **下载Qwen3模型**：
   ```bash
   ollama pull qwen3:0.6b
   ```

4. **启动Ollama服务**：
   ```bash
   ollama serve
   ```
   ⚠️ 请在新终端窗口运行，保持服务运行状态

### 第二步：验证安装

检查Ollama是否正常运行：
```bash
curl http://localhost:11434/api/tags
```

应该能看到包含qwen3:0.6b的模型列表。

### 第三步：启动游戏

```bash
python run.py
```

## 🎯 当前功能

✅ **已完成**：
- ⚡ **核心引擎**: 完整的游戏状态管理和回合控制
- 🤖 **LLM接口**: Qwen3模型集成，支持thinking模式
- 🎭 **AI智能体**: 记忆、怀疑度、角色扮演管理
- 👥 **四种角色**: 
  - 🏠 村民 - 逻辑分析和推理
  - 🐺 狼人 - 伪装和团队协作  
  - 🔮 预言家 - 身份查验和引导
  - 🧙‍♀️ 女巫 - 药剂使用决策
- 🗳️ **投票系统**: 完整的投票收集和结果处理
- 🏆 **胜利检测**: 自动判断游戏结束条件
- 🎨 **彩色界面**: 美观的终端显示界面
- 📊 **游戏日志**: 详细的游戏过程记录

## 📁 项目结构

```
AI狼人杀/
├── run.py                    # 主启动文件
├── config.json              # 游戏配置 (Qwen3设置)
├── requirements.txt         # Python依赖
├── src/                     # 源代码
│   ├── llm_interface.py     # Qwen3接口 (支持thinking模式)
│   ├── ai_agent.py          # AI智能体基类
│   ├── game_state.py        # 游戏状态管理
│   ├── voting_system.py     # 投票系统
│   ├── victory_checker.py   # 胜利条件检测
│   ├── ui_observer.py       # 用户界面观察器
│   ├── game_engine.py       # 游戏引擎
│   ├── werewolf_game.py     # 完整游戏集成
│   └── roles/               # 角色实现
│       ├── villager.py      # 村民
│       ├── werewolf.py      # 狼人
│       ├── seer.py          # 预言家
│       └── witch.py         # 女巫
├── prompts/                 # 提示词模板 (Qwen3优化)
│   ├── role_prompts.json    # 角色提示词
│   └── game_prompts.json    # 游戏流程提示词
└── logs/                    # 游戏日志目录
```

## 🔧 配置说明

### config.json 主要配置：

```json
{
  "ai_settings": {
    "model_name": "qwen3:0.6b",        # AI模型名称
    "ollama_base_url": "http://localhost:11434",  # Ollama服务器地址
    "temperature": 1.1,                 # 生成温度（0.1-2.0）
    "max_tokens": 800,                  # 最大生成令牌数
    "thinking_mode": true,              # 是否启用思考模式
    "context_length": 4096,             # 上下文长度
    "presence_penalty": 1.5             # 存在惩罚参数
  },
  "game_settings": {
    "total_players": 7,                 # 总玩家数
    "roles": {                          # 角色配置
      "villager": 3,                    # 村民数量
      "werewolf": 2,                    # 狼人数量
      "seer": 1,                        # 预言家数量
      "witch": 1                        # 女巫数量
    },
    "max_rounds": 10,                   # 最大回合数（可选，不设置则无限制）
    "discussion_time": 60               # 讨论时间（秒）
  },
  "ui_settings": {
    "display_thinking": true,           # 显示思考过程
    "auto_scroll": true,                # 自动滚动
    "save_logs": true,                  # 保存日志
    "show_reasoning": true,             # 显示推理过程
    "show_roles_to_user": true,         # 向用户显示角色
    "hide_roles_from_ai": true,         # 向AI隐藏角色
    "reveal_roles_on_death": true,      # 死亡时显示角色
    "observation_delays": {             # 观察延迟设置
      "phase_transition": 2.0,          # 阶段转换延迟
      "action_result": 1.5,             # 行动结果延迟
      "death_announcement": 3.0,        # 死亡公告延迟
      "speech": 2.0,                    # 发言延迟
      "voting_result": 1.5              # 投票结果延迟
    }
  }
}
```

**重要说明**：现在所有配置都会真正生效，修改config.json中的任何设置都会立即反映在游戏行为中。

### 🎯 回合数限制说明

- **设置max_rounds**: 游戏将在指定回合数后自动结束，无论胜负如何
- **不设置max_rounds**: 游戏将持续进行直到一方获胜（村民消灭所有狼人，或狼人数量达到或超过村民数量）
- **建议设置**: 对于快速体验，建议设置5-10轮；对于完整体验，可以不设置限制

### 🔧 配置验证和错误处理

游戏启动时会自动验证配置的有效性：

- **角色分配验证**：确保角色总数与玩家总数一致
- **必要角色检查**：验证是否包含狼人和村民角色
- **游戏平衡检查**：确保狼人数量合理
- **配置修复建议**：当发现问题时提供具体的修复建议

### 📋 配置示例

**5人局（快速游戏）**：
```json
{
  "game_settings": {
    "total_players": 5,
    "roles": {"villager": 2, "werewolf": 2, "seer": 1}
  }
}
```

**6人局（平衡体验）**：
```json
{
  "game_settings": {
    "total_players": 6,
    "roles": {"villager": 3, "werewolf": 2, "seer": 1}
  }
}
```

**8人局（复杂推理）**：
```json
{
  "game_settings": {
    "total_players": 8,
    "roles": {"villager": 4, "werewolf": 2, "seer": 1, "witch": 1}
  }
}
```

## 🎮 使用说明

启动程序后，可以选择：

1. **🧪 基础AI连接测试** - 验证Qwen3模型是否正常工作
2. **🎭 AI角色演示** - 观看单个AI角色的发言演示  
3. **🎮 启动完整游戏** - 完整的7人狼人杀游戏
4. **📋 查看设置指南** - 详细的环境配置说明

### 游戏模式选择：

- **🎮 完整游戏**: 完整体验
- **⚡ 快速演示**: 快速体验

## 📊 系统要求

- **最低要求**: 4GB RAM, 2GB 硬盘空间
- **推荐配置**: 8GB RAM (更流畅的多智能体运行)
- **Python版本**: 3.8+
- **操作系统**: Windows/macOS/Linux
- **模型大小**: 仅523MB (比之前减少90%)

## 🤝 贡献

这是一个AI辅助开发的项目，现已完成核心功能，欢迎提出建议和改进意见！

## 📄 开源协议

MIT License

---

🎯 **开始你的AI狼人杀之旅吧！** 