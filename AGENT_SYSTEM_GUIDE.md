# Agent系统使用指南

## 概述

Agent系统是基于LlamaIndex的智能Agent架构，为狼人杀游戏提供了更智能的决策机制。系统采用工具函数调用、多步骤决策链和智能推理，实现了高度智能化的游戏体验。

## 架构设计

### 核心组件

```
src/agents/
├── base_agent.py          # 基础Agent类
├── agent_factory.py       # Agent工厂系统
├── tools/                 # 工具函数集合
│   ├── witch_tools.py     # 女巫工具函数
│   ├── seer_tools.py      # 预言家工具函数
│   ├── werewolf_tools.py  # 狼人工具函数
│   └── common_tools.py    # 通用工具函数
└── role_agents/           # 角色Agent实现
    ├── witch_agent.py     # 女巫Agent
    ├── seer_agent.py      # 预言家Agent
    ├── werewolf_agent.py  # 狼人Agent
    └── villager_agent.py  # 村民Agent
```

### 设计原则

1. **分层架构**: 基础Agent → 角色Agent → 工具函数
2. **工具驱动**: 通过工具函数实现智能决策
3. **智能推理**: 使用LlamaIndex Agent进行多步骤决策
4. **扩展性**: 易于添加新角色和工具函数
5. **高可用性**: 具备备用方案和错误处理机制

## 配置指南

### 基础配置

在 `config.json` 中添加Agent设置：

```json
{
  "agent_settings": {
    "llm_backend": "ollama",         // LLM后端类型
    "tools_enabled": true,           // 是否启用工具函数
    "fallback_enabled": true,        // 是否启用备用方案
    "max_agent_iterations": 3,       // 最大Agent迭代次数
    "agent_timeout": 30,             // Agent超时时间(秒)
    "enable_tool_caching": true,     // 是否启用工具缓存
    "debug_mode": false              // 调试模式
  }
}
```

### 配置说明

- **llm_backend**: 支持的LLM后端类型（openai, ollama, custom）
- **tools_enabled**: 启用工具函数以获得更好的Agent性能
- **fallback_enabled**: 启用备用方案确保系统稳定性
- **max_agent_iterations**: 控制Agent决策的最大迭代次数
- **agent_timeout**: 设置Agent决策的超时时间
- **enable_tool_caching**: 启用工具函数缓存提高性能
- **debug_mode**: 调试模式，输出详细的决策过程

### 配置验证

```python
from src.agents.agent_factory import AgentFactory

factory = AgentFactory(config)
validation = factory.validate_config()

if validation["valid"]:
    print("配置有效")
else:
    print("配置错误:", validation["errors"])
```

## API文档

### AgentFactory

#### 创建Agent

```python
from src.agents.agent_factory import AgentFactory

# 创建工厂
factory = AgentFactory(config)

# 创建单个Agent
agent = factory.create_agent(
    player_id=1,
    name="测试玩家",
    role="witch",
    llm_interface=llm_interface,
    prompts=role_prompts
)

# 批量创建玩家
player_configs = [
    {"id": 1, "name": "玩家1", "role": "witch"},
    {"id": 2, "name": "玩家2", "role": "seer"}
]
agents = factory.create_players(player_configs, llm_interface, prompts)
```

#### 系统信息

```python
# 获取系统信息
mode_info = factory.get_mode_info()
print(f"当前模式: {mode_info['mode']}")
print(f"LLM后端: {mode_info['llm_backend']}")
print(f"工具启用: {mode_info['tools_enabled']}")
```

### BaseGameAgent

#### 基础功能

```python
# 夜晚行动
action_result = await agent.night_action(game_state)

# 发言
speech = await agent.make_speech(game_state)

# 投票
vote_target = await agent.vote(game_state, candidates)

# 记忆管理
agent.update_memory("speeches", speech_data)
memory_context = agent.format_memory_context()

# 怀疑度管理
agent.update_suspicion(target_id, change, reason)
suspicious_players = agent.get_most_suspicious_players(3)
```

#### 工具函数

```python
# 注册工具
agent.register_tools()

# 添加工具
agent.add_tool(tool_function)

# 执行决策链
result = await agent.execute_decision_chain(context)
```

### 工具函数API

#### 通用工具 (CommonTools)

```python
# 分析游戏局势
analysis = await common_tools.analyze_game_situation(game_state)

# 评估投票策略
strategy = await common_tools.evaluate_voting_strategy(candidates, game_state)

# 生成记忆摘要
summary = await common_tools.generate_memory_summary(memory_data)

# 分析行为一致性
consistency = await common_tools.analyze_behavior_consistency(player_data)
```

#### 角色专用工具

```python
# 女巫工具
witch_tools = WitchTools(agent)
potion_decision = await witch_tools.decide_potion_usage(death_info, game_state)

# 预言家工具
seer_tools = SeerTools(agent)
divine_target = await seer_tools.choose_divine_target(candidates, game_state)

# 狼人工具
werewolf_tools = WerewolfTools(agent)
kill_target = await werewolf_tools.choose_kill_target(candidates, game_state)
```

## 使用示例

### 基础使用

```python
import asyncio
from src.agents.agent_factory import AgentFactory
from src.llm_interface import LLMInterface

async def main():
    # 加载配置
    config = load_config()
    
    # 创建LLM接口
    llm_interface = LLMInterface(config)
    
    # 创建Agent工厂
    factory = AgentFactory(config)
    
    # 创建女巫Agent
    witch = factory.create_agent(
        player_id=1,
        name="女巫玩家",
        role="witch",
        llm_interface=llm_interface,
        prompts=role_prompts
    )
    
    # 执行夜晚行动
    game_state = {"alive_players": [...], "current_round": 1}
    death_info = {"target": 2, "cause": "werewolf_kill"}
    
    result = await witch.night_action(game_state, death_info)
    print(f"女巫决策: {result}")

if __name__ == "__main__":
    asyncio.run(main())
```

### 高级功能

```python
# 多步骤决策链
context = {
    "game_state": game_state,
    "memory": agent.get_memory_context(),
    "suspicions": agent.get_suspicions()
}

decision_chain = await agent.execute_decision_chain(context)

# 工具函数调用
tools = agent.get_tools()
for tool in tools:
    if tool.name == "analyze_situation":
        result = await tool.function(game_state)
        break
```

## 测试指南

### 运行测试

```bash
# 运行所有测试
python -m pytest tests/test_agent_system.py -v

# 运行特定测试
python -m pytest tests/test_agent_system.py::test_witch_agent -v

# 运行性能测试
python -m pytest tests/test_agent_system.py::test_performance -v
```

### 测试覆盖

- Agent创建和初始化
- 工具函数调用
- 决策功能测试
- 发言功能测试
- 投票功能测试
- 性能基准测试
- 错误处理测试

## 故障排除

### 常见问题

1. **Agent创建失败**
   - 检查LLM接口配置
   - 验证角色类型是否正确
   - 确认依赖包已安装

2. **工具函数调用失败**
   - 检查工具函数注册
   - 验证参数格式
   - 查看错误日志

3. **决策超时**
   - 调整agent_timeout设置
   - 检查LLM响应速度
   - 优化决策逻辑

### 调试模式

启用调试模式获取详细信息：

```json
{
  "agent_settings": {
    "debug_mode": true
  }
}
```

## 性能优化

### 建议配置

```json
{
  "agent_settings": {
    "tools_enabled": true,
    "enable_tool_caching": true,
    "max_agent_iterations": 3,
    "agent_timeout": 30
  }
}
```

### 最佳实践

1. 启用工具缓存提高响应速度
2. 合理设置迭代次数避免过度计算
3. 使用适当的超时时间
4. 定期清理内存数据

## 更新日志

### v2.0.0
- 移除传统模式，只保留Agent模式
- 优化工具函数系统
- 改进错误处理机制
- 增强性能监控

### v1.0.0
- 初始版本发布
- 支持基础Agent功能
- 实现工具函数调用
- 提供双重模式支持 