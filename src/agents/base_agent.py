"""
基础游戏Agent类
基于LlamaIndex的Agent框架，提供工具注册、状态管理和决策链执行功能
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from abc import ABC, abstractmethod
from datetime import datetime

from llama_index.core.tools import FunctionTool, BaseTool
from llama_index.core.agent import AgentRunner, ReActAgent
from llama_index.llms.ollama import Ollama

from ..ai_agent import BaseAIAgent
from ..llm_interface import LLMInterface


class BaseGameAgent(BaseAIAgent):
    """基于LlamaIndex的游戏Agent基类"""
    
    def __init__(self, player_id: int, name: str, role: str, 
                 llm_interface: LLMInterface, prompts: Dict[str, Any], 
                 identity_system=None, memory_config=None):
        super().__init__(player_id, name, role, llm_interface, prompts, identity_system, memory_config)
        
        # Agent特有属性
        self.tools: List[FunctionTool] = []
        self.agent_runner: Optional[ReActAgent] = None # 将在_initialize_agent被立刻赋值
        self.decision_history: List[Dict[str, Any]] = []
        
        # 注意：不在这里初始化Agent，让子类先完成工具实例化
    
    def initialize_agent(self):
        """初始化LlamaIndex Agent"""
        try:
            # 注册工具
            self.register_tools()
            
            # 创建Agent Runner
            self.agent_runner = self._create_agent_runner()
            
            if self.agent_runner:
                self.logger.info(f"Agent {self.name}({self.role}) 初始化成功")
            else:
                self.logger.warning(f"Agent {self.name}({self.role}) Agent Runner创建失败，使用基础模式")
            
        except Exception as e:
            self.logger.error(f"Agent初始化失败: {e}")
            self.agent_runner = None
    
    @abstractmethod
    def register_tools(self) -> None:
        """注册角色特定的工具函数"""
        pass
    
    def _create_agent_runner(self) -> Optional[ReActAgent]:
        """创建Agent Runner的默认实现"""
        try:
            # 创建Ollama LLM实例
            llm = Ollama(
                model=self.llm_interface.model_name,
                base_url=self.llm_interface.base_url,
                temperature=self.llm_interface.temperature
            )
            
            # 创建Agent Runner - 使用正确的API
            if self.tools:
                return ReActAgent.from_tools(
                    tools=self.tools,  # type: ignore
                    llm=llm,
                    verbose=True
                )
            else:
                self.logger.warning(f"Agent {self.name}({self.role}) 没有可用工具")
                return None
                
        except Exception as e:
            self.logger.error(f"创建Agent Runner失败: {e}")
            return None
    
    def add_tool(self, tool: FunctionTool):
        """添加工具到Agent"""
        self.tools.append(tool)
    
    async def make_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """使用Agent进行决策"""
        try:
            if self.agent_runner is None:
                # 回退到基础决策模式
                return await self._fallback_decision(context)
            
            # 构建决策提示
            decision_prompt = self._build_decision_prompt(context)
            
            # 使用Agent Runner进行决策
            response = await self.agent_runner.achat(decision_prompt)
            
            # 解析决策结果
            decision_result = self._parse_agent_response(response, context)
            
            # 记录决策历史
            self.decision_history.append({
                "timestamp": datetime.now().isoformat(),
                "context": context,
                "decision": decision_result,
                "response": str(response)
            })
            
            return decision_result
            
        except Exception as e:
            self.logger.error(f"Agent决策失败: {e}")
            return await self._fallback_decision(context)
    
    async def execute_decision_chain(self, initial_context: Dict[str, Any]) -> Dict[str, Any]:
        """执行多步骤决策链"""
        try:
            current_context = initial_context.copy()
            max_steps = 5  # 最大决策步骤数
            
            for step in range(max_steps):
                # 执行单步决策
                step_result = await self.make_decision(current_context)
                
                # 更新上下文
                current_context.update(step_result)
                
                # 检查是否需要继续决策
                if step_result.get("final_decision", False):
                    return step_result
                
                # 防止无限循环
                if step >= max_steps - 1:
                    step_result["final_decision"] = True
                    return step_result
            
            return current_context
            
        except Exception as e:
            self.logger.error(f"决策链执行失败: {e}")
            return await self._fallback_decision(initial_context)
    
    def _build_decision_prompt(self, context: Dict[str, Any]) -> str:
        """构建决策提示"""
        role_context = self.get_role_prompt("base_prompt")
        game_context = self.llm_interface.format_game_context(context.get("game_state", {}))
        
        prompt = f"""
        你是{self.role}角色，玩家{self.player_id}号{self.name}。
        
        角色背景：{role_context}
        
        当前游戏情况：{game_context}
        
        可用工具：{', '.join([getattr(tool, 'name', str(tool)) for tool in self.tools])}
        
        请根据当前情况，使用合适的工具进行决策。
        如果需要多步决策，请逐步执行。
        
        当前上下文：{context}
        """
        
        return prompt
    
    def _parse_agent_response(self, response, context: Dict[str, Any]) -> Dict[str, Any]:
        """解析Agent响应"""
        try:
            # 尝试从响应中提取工具调用结果
            if hasattr(response, 'message') and hasattr(response.message, 'content'):
                content = response.message.content
                
                # 解析工具调用结果
                result = self._extract_tool_results(content)
                
                # 更新Agent状态
                self.update_state(result)
                
                return result
            else:
                # 如果无法解析，返回基础结果
                return {
                    "action": "unknown",
                    "success": False,
                    "message": "无法解析Agent响应",
                    "final_decision": True
                }
                
        except Exception as e:
            self.logger.error(f"解析Agent响应失败: {e}")
            return {
                "action": "error",
                "success": False,
                "message": f"解析失败: {e}",
                "final_decision": True
            }
    
    def _extract_tool_results(self, content: str) -> Dict[str, Any]:
        """从响应内容中提取工具调用结果"""
        # 这里需要根据实际的工具调用格式进行解析
        # 暂时返回基础格式
        return {
            "action": "tool_call",
            "content": content,
            "success": True,
            "final_decision": True
        }
    
    def update_state(self, action_result: Dict[str, Any]):
        """更新Agent状态"""
        # 子类可以重写此方法来更新特定状态
        pass
    
    async def _fallback_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """回退决策机制"""
        self.logger.warning(f"使用回退决策机制")
        
        # 调用原有的决策逻辑
        if hasattr(self, 'night_action'):
            return await self.night_action(context.get("game_state", {}))
        else:
            return {
                "action": "fallback",
                "success": False,
                "message": "无可用决策机制",
                "final_decision": True
            }
    
    def get_decision_history(self) -> List[Dict[str, Any]]:
        """获取决策历史"""
        return self.decision_history.copy()
    
    def clear_decision_history(self):
        """清空决策历史"""
        self.decision_history.clear() 