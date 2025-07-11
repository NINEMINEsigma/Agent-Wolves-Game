# 背景
文件名：2025-01-14_1_fix-werewolf-victory-condition.md
创建于：2025-01-14_15:30:00
创建者：Claude
主分支：main
任务分支：task/fix-werewolf-victory-condition_2025-01-14_1
Yolo模式：Off

# 任务描述
修复狼人胜利条件错误：当前实现要求狼人消灭所有村民阵营成员（包括特殊角色）才能获胜，但根据标准狼人杀规则，狼人只需要消灭所有普通村民就能获胜。当最后一个普通村民被狼人在夜晚击杀时，游戏应该立即结束，狼人获胜。

# 项目概览
这是一个基于AI的狼人杀游戏，使用Python实现，包含多个AI代理扮演不同角色进行游戏。游戏引擎管理游戏流程，胜利检查器负责判断游戏结束条件。

⚠️ 警告：永远不要修改此部分 ⚠️
核心RIPER-5协议规则：
1. 必须在每个响应开头声明当前模式 [MODE: MODE_NAME]
2. 未经明确许可不能在模式间转换
3. 在EXECUTE模式中必须100%忠实遵循计划
4. 在REVIEW模式中必须标记任何偏差
5. 代码更改必须使用适当的注释格式
⚠️ 警告：永远不要修改此部分 ⚠️

# 分析
通过代码分析发现的问题：

1. **胜利检查器** (`src/victory_checker.py`) 中的 `is_game_over` 方法：
   - 当前使用 `villager_faction_count`（整个村民阵营）判断狼人胜利
   - 应该使用 `villager_count`（仅普通村民）判断狼人胜利

2. **具体问题位置**：
   - 第113行：`if villager_faction_count == 0 and werewolf_count > 0:`
   - 应该改为：`if villager_count == 0 and werewolf_count > 0:`

3. **胜利原因描述**也需要相应更新：
   - 第133行：`if faction_counts["villager_faction"] == 0:`
   - 应该改为：`if faction_counts["villagers"] == 0:`

4. **游戏引擎**中的胜利检查调用是正确的，问题在于胜利条件的判断逻辑

# 提议的解决方案
修改 `src/victory_checker.py` 文件中的胜利条件判断逻辑：
1. 将狼人胜利条件从检查整个村民阵营改为只检查普通村民
2. 更新胜利原因描述文本
3. 确保夜晚死亡后立即检查胜利条件的逻辑保持不变

# 当前执行步骤："6. 任务完成"

# 任务进度
[2025-01-14_15:30:00]
- 已修改：创建任务文件
- 更改：记录狼人胜利条件修复问题
- 原因：用户报告最后一个普通村民被杀死时游戏没有立即结束
- 阻碍因素：无
- 状态：成功

[2025-01-14_15:35:00]
- 已修改：src/victory_checker.py
- 更改：修改狼人胜利条件判断逻辑，从检查整个村民阵营改为只检查普通村民
- 原因：修复胜利条件错误，符合标准狼人杀规则
- 阻碍因素：无
- 状态：成功

[2025-01-14_15:40:00]
- 已修改：用户确认修改成功
- 更改：用户调整胜利原因描述文本
- 原因：优化胜利消息的表述
- 阻碍因素：无
- 状态：成功

# 最终审查
[2025-01-14_15:40:00]
✅ 任务成功完成！

**修复总结：**
- 问题：狼人胜利条件错误，要求消灭所有村民阵营成员而不是仅普通村民
- 解决方案：修改胜利检查器逻辑，使用 `villager_count` 替代 `villager_faction_count`
- 效果：当最后一个普通村民被杀死时，游戏立即结束，狼人获胜
- 验证：用户确认修改成功，符合标准狼人杀规则

**修改文件：**
- src/victory_checker.py：更新胜利条件判断和描述

**测试建议：**
- 验证最后一个普通村民死亡时游戏立即结束
- 验证特殊角色存活不影响狼人胜利
- 验证村民阵营胜利条件保持不变 