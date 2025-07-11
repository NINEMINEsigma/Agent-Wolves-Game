# Agent系统使用指南

## 概述

Agent系统是基于LlamaIndex的智能Agent架构，为狼人杀游戏提供了更智能的决策机制。系统支持传统模式和Agent模式的双重运行，实现了工具函数调用、多步骤决策链和智能推理。

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
3. **双重模式**: 支持传统模式和Agent模式
4. **渐进迁移**: 平滑切换，不影响现有功能
5. **扩展性**: 易于添加新角色和工具函数

## 配置指南

### 基础配置

在 `config.json` 中添加Agent设置：

```json
{
  "agent_settings": {
    "mode": "traditional",           // "agent" | "traditional"
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

### 模式说明

- **traditional**: 传统模式，直接使用LLM生成回复
- **agent**: Agent模式，使用工具函数进行智能决策

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

#### 模式管理

```python
# 切换模式
factory.switch_mode("agent")

# 获取模式信息
mode_info = factory.get_mode_info()
print(f"当前模式: {mode_info['mode']}")
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
analysis = common_tools.analyze_game_situation(game_state)

# 获取玩家信息
player_info = common_tools.get_player_info(player_id, game_state)

# 更新怀疑度
result = common_tools.update_suspicion(target_id, change, reason)

# 分析发言模式
speech_analysis = common_tools.analyze_speech_patterns(target_id)

# 评估投票策略
voting_strategy = common_tools.evaluate_voting_strategy(candidates)

# 获取记忆摘要
memory_summary = common_tools.get_memory_summary(memory_type, limit)

# 分析行为一致性
consistency = common_tools.analyze_behavior_consistency(target_id)
```

#### 女巫工具 (WitchTools)

```python
# 检查药剂状态
potion_status = witch_tools.check_potion_status()

# 分析死亡情况
death_analysis = witch_tools.analyze_death_situation(death_info)

# 评估解药使用
antidote_evaluation = witch_tools.evaluate_antidote_usage(death_info)

# 评估毒药使用
poison_evaluation = witch_tools.evaluate_poison_usage(game_state)

# 执行解药行动
antidote_result = witch_tools.use_antidote(target_id)

# 执行毒药行动
poison_result = witch_tools.use_poison(target_id)

# 不操作
no_action_result = witch_tools.no_action()
```

#### 预言家工具 (SeerTools)

```python
# 分析可疑玩家
suspicious_analysis = seer_tools.analyze_suspicious_players(game_state)

# 评估查验价值
divine_value = seer_tools.evaluate_divine_value(target_id, game_state)

# 执行查验
divine_result = seer_tools.divine_player(target_id)
```

#### 狼人工具 (WerewolfTools)

```python
# 分析威胁等级
threat_analysis = werewolf_tools.analyze_threat_level(game_state)

# 协调同伴行动
coordination = werewolf_tools.coordinate_with_teammates(game_state)

# 选择击杀目标
kill_target = werewolf_tools.select_kill_target(candidates, game_state)

# 执行击杀
kill_result = werewolf_tools.execute_kill(target_id)
```

## 使用示例

### 基础使用

```python
import asyncio
from src.agents.agent_factory import AgentFactory
from src.llm_interface import LLMInterface
from src.config_validator import ConfigValidator

async def basic_example():
    # 加载配置
    validator = ConfigValidator()
    config = validator.load_config()
    
    # 创建LLM接口
    llm_interface = LLMInterface(config)
    
    # 创建Agent工厂
    factory = AgentFactory(config)
    
    # 加载提示词
    with open('prompts/role_prompts.json', 'r', encoding='utf-8') as f:
        role_prompts = json.load(f)
    
    # 创建女巫Agent
    witch_agent = factory.create_agent(
        player_id=1,
        name="测试女巫",
        role="witch",
        llm_interface=llm_interface,
        prompts=role_prompts
    )
    
    # 测试夜晚行动
    game_state = {
        "current_round": 1,
        "phase": "夜晚",
        "alive_players": [{"id": 1, "name": "测试女巫"}],
        "dead_players": []
    }
    
    action_result = await witch_agent.night_action(game_state)
    print(f"夜晚行动结果: {action_result}")

# 运行示例
asyncio.run(basic_example())
```

### 游戏引擎集成

```python
from src.game_engine import GameEngine
from src.agents.agent_factory import AgentFactory

# 在游戏引擎中使用Agent工厂
class EnhancedGameEngine(GameEngine):
    def __init__(self, config, players):
        super().__init__(config, players)
        self.agent_factory = AgentFactory(config)
    
    def get_agent_mode_info(self):
        return self.agent_factory.get_mode_info()
    
    def switch_agent_mode(self, new_mode):
        self.agent_factory.switch_mode(new_mode)
    
    def validate_agent_config(self):
        return self.agent_factory.validate_config()
```

### 自定义工具函数

```python
from llama_index.core.tools import FunctionTool
from src.agents.base_agent import BaseGameAgent

class CustomAgent(BaseGameAgent):
    def register_tools(self):
        # 注册自定义工具
        custom_tool = FunctionTool.from_defaults(
            fn=self.custom_analysis,
            name="custom_analysis",
            description="自定义分析工具"
        )
        self.add_tool(custom_tool)
    
    def custom_analysis(self, data):
        # 自定义分析逻辑
        return {
            "action": "custom_analysis",
            "success": True,
            "result": "分析结果"
        }
```

## 测试指南

### 运行测试套件

```bash
python test_agent_system.py
```

### 测试内容

1. **Agent创建测试**: 验证各角色Agent的创建
2. **工具函数测试**: 验证工具函数的调用
3. **决策功能测试**: 验证Agent的决策能力
4. **发言功能测试**: 验证Agent的发言生成
5. **性能基准测试**: 测试响应时间和性能

### 测试报告

测试完成后会生成 `test_report.json` 文件，包含详细的测试结果和性能数据。

## 故障排除

### 常见问题

1. **Agent创建失败**
   - 检查配置文件中的Agent设置
   - 验证LLM接口连接
   - 确认提示词文件存在

2. **工具函数调用失败**
   - 检查工具函数是否正确注册
   - 验证输入参数格式
   - 查看错误日志

3. **性能问题**
   - 调整Agent超时设置
   - 启用工具缓存
   - 优化LLM模型配置

### 调试模式

启用调试模式获取详细信息：

```json
{
  "agent_settings": {
    "debug_mode": true
  }
}
```

### 日志查看

```python
import logging

# 设置日志级别
logging.basicConfig(level=logging.DEBUG)

# 查看Agent日志
logger = logging.getLogger("AgentFactory")
```

## 扩展开发

### 添加新角色

1. 创建角色Agent类
2. 实现工具函数
3. 在工厂中注册
4. 更新配置文件

### 添加新工具

1. 定义工具函数
2. 在Agent中注册
3. 更新文档

### 自定义决策逻辑

1. 继承BaseGameAgent
2. 重写决策方法
3. 实现自定义逻辑

## 性能优化

### 配置优化

```json
{
  "agent_settings": {
    "max_agent_iterations": 2,    // 减少迭代次数
    "agent_timeout": 15,          // 缩短超时时间
    "enable_tool_caching": true,  // 启用缓存
    "debug_mode": false           // 关闭调试模式
  }
}
```

### 代码优化

1. 使用异步操作
2. 实现结果缓存
3. 优化工具函数逻辑
4. 减少不必要的API调用

## 版本历史

- **v1.0.0**: 初始版本，支持基础Agent功能
- **v1.1.0**: 添加工具函数系统
- **v1.2.0**: 完善角色Agent实现
- **v1.3.0**: 添加测试套件和文档

## 贡献指南

1. Fork项目
2. 创建功能分支
3. 编写测试
4. 提交Pull Request

## 许可证

本项目采用MIT许可证，详见LICENSE文件。 