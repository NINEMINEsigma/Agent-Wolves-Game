"""
Qwen3 LLM接口封装模块
用于与Ollama服务器通信，调用Qwen3-0.6B模型
支持thinking/non-thinking模式切换，专为狼人杀游戏优化
"""

import json
import asyncio
import logging
from typing import Dict, Any, Optional, List
import requests
from datetime import datetime


class QwenInterface:
    """Qwen3模型接口封装类，支持thinking模式的智能推理"""
    
    def __init__(self, config: Dict[str, Any]):
        """
        初始化Qwen3接口
        
        Args:
            config: 配置字典，包含AI设置
        """
        self.config = config
        self.ai_settings = config.get("ai_settings", {})
        self.model_name = self.ai_settings.get("model_name", "qwen3:0.6b")
        self.base_url = self.ai_settings.get("ollama_base_url", "http://localhost:11434")
        self.temperature = self.ai_settings.get("temperature", 1.1)
        self.max_tokens = self.ai_settings.get("max_tokens", 800)
        self.thinking_mode = self.ai_settings.get("thinking_mode", True)
        self.presence_penalty = self.ai_settings.get("presence_penalty", 1.5)
        
        # 设置日志
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # 验证Ollama连接
        self._verify_connection()
    
    def _verify_connection(self) -> bool:
        """验证与Ollama服务器的连接"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [model.get("name", "") for model in models]
                if any(self.model_name in name for name in model_names):
                    self.logger.info(f"成功连接到Ollama，模型 {self.model_name} 可用")
                    return True
                else:
                    self.logger.warning(f"模型 {self.model_name} 未找到，可用模型: {model_names}")
                    return False
            else:
                self.logger.error(f"无法连接到Ollama服务器: {response.status_code}")
                return False
        except requests.exceptions.RequestException as e:
            self.logger.error(f"连接Ollama失败: {e}")
            return False
    
    async def generate_response(self, prompt: str, role_context: str = "", 
                              system_prompt: str = "", use_thinking: Optional[bool] = None) -> str:
        """
        生成AI回复
        
        Args:
            prompt: 用户输入的提示
            role_context: 角色上下文信息
            system_prompt: 系统提示词
            use_thinking: 是否使用思考模式（None时使用默认设置）
            
        Returns:
            AI生成的回复文本
        """
        try:
            # 确定是否使用thinking模式
            thinking_enabled = use_thinking if use_thinking is not None else self.thinking_mode
            
            # 构建完整的提示
            full_prompt = self._build_full_prompt(prompt, role_context, system_prompt, thinking_enabled)
            
            # 调用Ollama API
            payload = {
                "model": self.model_name,
                "prompt": full_prompt,
                "stream": False,
                "options": {
                    "temperature": self.temperature,
                    "num_predict": self.max_tokens,
                    "presence_penalty": self.presence_penalty
                }
            }
            
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                raw_response = result.get("response", "").strip()
                
                # 如果启用thinking模式，提取最终回复部分
                if thinking_enabled and "<think>" in raw_response:
                    return self._extract_final_response(raw_response)
                
                return raw_response
            else:
                self.logger.error(f"API调用失败: {response.status_code}")
                return "抱歉，AI暂时无法回应。"
                
        except Exception as e:
            self.logger.error(f"生成回复时出错: {e}")
            return "抱歉，生成回复时出现错误。"
    
    def _build_full_prompt(self, prompt: str, role_context: str, system_prompt: str, thinking_enabled: bool) -> str:
        """构建完整的提示词，支持thinking模式"""
        parts = []
        
        if system_prompt:
            parts.append(f"系统指令: {system_prompt}")
        
        if role_context:
            parts.append(f"角色背景: {role_context}")
        
        # 根据thinking模式调整提示
        if thinking_enabled:
            parts.append("请使用 /think 模式进行深度思考和推理")
            parts.append(f"当前情况: {prompt}")
            parts.append("请先在<think></think>标签内进行思考，然后给出最终回复:")
        else:
            parts.append("请使用 /no_think 模式进行快速回复")
            parts.append(f"当前情况: {prompt}")
            parts.append("请直接回复:")
        
        return "\n\n".join(parts)
    
    def _extract_final_response(self, raw_response: str) -> str:
        """从包含thinking内容的回复中提取最终回复"""
        try:
            # 寻找</think>标签后的内容
            if "</think>" in raw_response:
                final_part = raw_response.split("</think>", 1)[1].strip()
                return final_part if final_part else raw_response
            
            # 如果没有找到结束标签，返回原始回复
            return raw_response
            
        except Exception as e:
            self.logger.warning(f"提取最终回复时出错: {e}")
            return raw_response
    
    def format_game_context(self, game_state: Dict[str, Any]) -> str:
        """
        格式化游戏状态为上下文信息
        
        Args:
            game_state: 当前游戏状态字典
            
        Returns:
            格式化的游戏上下文字符串
        """
        context_parts = []
        
        # 基本游戏信息
        round_num = game_state.get("current_round", 1)
        phase = game_state.get("phase", "未知")
        context_parts.append(f"第 {round_num} 轮 - {phase}阶段")
        
        # 存活玩家信息
        alive_players = game_state.get("alive_players", [])
        if alive_players:
            alive_info = ", ".join([f"玩家{p['id']}({p['name']})" for p in alive_players])
            context_parts.append(f"存活玩家: {alive_info}")
        
        # 死亡玩家信息
        dead_players = game_state.get("dead_players", [])
        if dead_players:
            dead_info = ", ".join([f"玩家{p['id']}({p['name']})" for p in dead_players])
            context_parts.append(f"已死亡玩家: {dead_info}")
        
        # 最近的发言
        recent_speeches = game_state.get("recent_speeches", [])
        if recent_speeches:
            speech_info = []
            for speech in recent_speeches[-3:]:  # 只显示最近3条发言
                speaker = speech.get("speaker", "未知")
                content = speech.get("content", "")[:50]  # 截取前50字符
                speech_info.append(f"{speaker}: {content}...")
            context_parts.append("最近发言: " + " | ".join(speech_info))
        
        return "\n".join(context_parts)
    
    def validate_action(self, response: str, valid_actions: List[str]) -> Dict[str, Any]:
        """
        验证AI行动的有效性
        
        Args:
            response: AI的回复
            valid_actions: 有效行动列表
            
        Returns:
            包含验证结果的字典
        """
        result = {
            "valid": False,
            "action": None,
            "target": None,
            "reason": ""
        }
        
        response_lower = response.lower()
        
        # 检查是否包含有效行动
        for action in valid_actions:
            if action.lower() in response_lower:
                result["action"] = action
                result["valid"] = True
                break
        
        # 提取目标玩家ID（如果有）
        if result["valid"]:
            import re
            player_matches = re.findall(r'玩家(\d+)', response)
            if player_matches:
                result["target"] = int(player_matches[0])
        
        # 提取原因
        result["reason"] = response.strip()
        
        return result
    
    def extract_vote_choice(self, response: str, candidate_players: List[int]) -> Optional[int]:
        """
        从AI回复中提取投票选择
        
        Args:
            response: AI的回复文本
            candidate_players: 候选玩家ID列表
            
        Returns:
            选择的玩家ID，如果无法解析则返回None
        """
        import re
        
        # 提取所有提到的玩家ID
        player_matches = re.findall(r'玩家(\d+)', response)
        
        for player_str in player_matches:
            player_id = int(player_str)
            if player_id in candidate_players:
                return player_id
        
        return None
    
    async def chat_completion(self, messages: List[Dict[str, str]], use_thinking: Optional[bool] = None) -> str:
        """
        使用聊天格式调用模型
        
        Args:
            messages: 消息列表，每个消息包含role和content
            use_thinking: 是否使用思考模式
            
        Returns:
            AI回复
        """
        try:
            # 将消息转换为单个提示
            prompt_parts = []
            for msg in messages:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if role == "system":
                    prompt_parts.append(f"系统: {content}")
                elif role == "user":
                    prompt_parts.append(f"用户: {content}")
                elif role == "assistant":
                    prompt_parts.append(f"助手: {content}")
            
            full_prompt = "\n".join(prompt_parts)
            return await self.generate_response(full_prompt, use_thinking=use_thinking)
            
        except Exception as e:
            self.logger.error(f"聊天完成时出错: {e}")
            return "抱歉，处理聊天时出现错误。"

# 为了保持向后兼容性，创建别名
DeepSeekInterface = QwenInterface 