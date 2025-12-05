# -*- coding: utf-8 -*-
"""Meta Planner Agent 的配置管理模块。

本模块集中了 Meta Planner Agent 的所有配置参数，
从环境变量加载值，并提供合理的默认值。

环境变量：
    # 必需的 API 密钥
    OPENAI_API_KEY: OpenAI API 密钥用于模型访问
    TAVILY_API_KEY: Tavily API 密钥用于搜索功能

    # 可选的模型配置
    OPENAI_BASE_URL: OpenAI API 的基础 URL（默认：https://api.openai.com/v1）
    CHAT_MODEL: 要使用的模型名称（默认：gpt-4-turbo）
    MODEL_TEMPERATURE: 模型温度（默认：0.7）
    MODEL_MAX_TOKENS: 每次生成的最大 token 数（默认：32000）
    MODEL_STREAM: 启用流式响应（默认：true）

    # 可选的 Agent 配置
    AGENT_OPERATION_DIR: agent 操作的自定义工作目录
    AGENT_STATE_SAVING_DIR: 保存 agent 状态的目录（默认：./agent-states）
    AGENT_MAX_ITERS: 推理-行动迭代的最大次数（默认：100）
    AGENT_WORKER_MAX_ITERS: 工作器迭代的最大次数（默认：20）

    # 可选的规划器配置
    PLANNER_MODE: 规划模式（默认：dynamic）
                  选项：disable, dynamic, enforced

    # 可选的工具配置
    TOOL_RESPONSE_BUDGET: 工具响应中的最大字符数（默认：40970）

    # 可选的日志配置
    LOG_LEVEL: 日志级别（默认：DEBUG）
               选项：DEBUG, INFO, WARNING, ERROR, CRITICAL
    ENABLE_LOGFIRE: 启用 logfire 日志（默认：false）

    # 可选的 MCP 配置
    MCP_NPX_COMMAND: MCP 客户端的 NPX 命令（默认：npx）
    MCP_TAVILY_PACKAGE: Tavily MCP 包（默认：tavily-mcp@latest）
    MCP_FILESYSTEM_PACKAGE: 文件系统 MCP 包
                            （默认：@modelcontextprotocol/server-filesystem）

使用方法：
    from config import config

    # 访问配置值
    api_key = config.openai_api_key
    model_name = config.chat_model

    # 获取 agent 工作目录
    working_dir = config.get_agent_working_dir()
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import dotenv

# 从 .env 文件加载环境变量
dotenv.load_dotenv()


@dataclass
class MetaPlannerConfig:
    """Meta Planner Agent 的配置数据类。

    此类提供了一个集中的配置接口，带有类型提示和验证。
    所有值都从环境变量加载，并带有合理的默认值。
    """

    # ============================================================================
    # Required API Keys
    # ============================================================================
    openai_api_key: str
    tavily_api_key: str

    # ============================================================================
    # Model Configuration
    # ============================================================================
    openai_base_url: str = "https://api.openai.com/v1"
    chat_model: str = "gpt-4-turbo"
    model_temperature: float = 0.7
    model_max_tokens: int = 32000
    model_stream: bool = True

    # ============================================================================
    # Agent Configuration
    # ============================================================================
    agent_name: str = "Task-Meta-Planner"
    agent_operation_dir: Optional[str] = (
        "agentscope_learning/02_meta_planner_agent/agent_outputs/meta_planner_agent"  # Defaults to meta_agent_demo_env
    )
    agent_state_saving_dir: str = (
        "agentscope_learning/02_meta_planner_agent/agent_outputs/agent-states"
    )
    agent_max_iters: int = 100
    agent_worker_max_iters: int = 20

    # ============================================================================
    # Planner Configuration
    # ============================================================================
    planner_mode: Literal["disable", "dynamic", "enforced"] = "dynamic"

    # ============================================================================
    # Tool Configuration
    # ============================================================================
    tool_response_budget: int = 8194 * 5  # Approximately 40KB

    # ============================================================================
    # Logging Configuration
    # ============================================================================
    log_level: str = "DEBUG"
    enable_logfire: bool = False

    # ============================================================================
    # MCP Configuration
    # ============================================================================
    mcp_npx_command: str = "npx"
    mcp_tavily_package: str = "tavily-mcp@latest"
    mcp_filesystem_package: str = "@modelcontextprotocol/server-filesystem"

    def __post_init__(self):
        """初始化后验证配置。"""
        if not self.tavily_api_key:
            raise ValueError(
                "TAVILY_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        # 验证规划器模式
        valid_modes = ["disable", "dynamic", "enforced"]
        if self.planner_mode not in valid_modes:
            raise ValueError(
                f"Invalid planner_mode: {self.planner_mode}. "
                f"Must be one of: {', '.join(valid_modes)}"
            )

        # 验证日志级别
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: {self.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        self.log_level = self.log_level.upper()

    def get_agent_working_dir(self) -> str:
        """获取 agent 工作目录路径。

        返回配置的 agent 操作目录，或默认为当前模块目录中的 'meta_agent_demo_env'。

        返回：
            str: agent 工作目录的绝对路径
        """
        if self.agent_operation_dir:
            return os.path.abspath(self.agent_operation_dir)

        # 默认为与此配置相同目录中的 meta_agent_demo_env
        default_dir = Path(__file__).parent / "meta_agent_demo_env"
        return str(default_dir.absolute())

    def get_state_saving_dir(self, time_str: str) -> str:
        """获取特定运行的状态保存目录。

        参数：
            time_str: 用于标识运行的时间戳字符串

        返回：
            str: 此运行的状态保存目录路径
        """
        return os.path.join(self.agent_state_saving_dir, f"run-{time_str}")

    def to_dict(self) -> dict:
        """将配置转换为字典。

        返回：
            dict: 配置作为字典
        """
        return {
            "openai_api_key": "***" if self.openai_api_key else None,
            "tavily_api_key": "***" if self.tavily_api_key else None,
            "openai_base_url": self.openai_base_url,
            "chat_model": self.chat_model,
            "model_temperature": self.model_temperature,
            "model_max_tokens": self.model_max_tokens,
            "model_stream": self.model_stream,
            "agent_name": self.agent_name,
            "agent_operation_dir": self.get_agent_working_dir(),
            "agent_state_saving_dir": self.agent_state_saving_dir,
            "agent_max_iters": self.agent_max_iters,
            "agent_worker_max_iters": self.agent_worker_max_iters,
            "planner_mode": self.planner_mode,
            "tool_response_budget": self.tool_response_budget,
            "log_level": self.log_level,
            "enable_logfire": self.enable_logfire,
            "mcp_npx_command": self.mcp_npx_command,
            "mcp_tavily_package": self.mcp_tavily_package,
            "mcp_filesystem_package": self.mcp_filesystem_package,
        }


def _parse_bool(value: Optional[str], default: bool = False) -> bool:
    """从环境变量字符串解析布尔值。

    参数：
        value: 来自环境变量的字符串值
        default: 解析失败时的默认值

    返回：
        bool: 解析的布尔值
    """
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on", "t")


def _parse_int(value: Optional[str], default: int) -> int:
    """从环境变量字符串解析整数值。

    参数：
        value: 来自环境变量的字符串值
        default: 解析失败时的默认值

    返回：
        int: 解析的整数值
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_float(value: Optional[str], default: float) -> float:
    """从环境变量字符串解析浮点值。

    参数：
        value: 来自环境变量的字符串值
        default: 解析失败时的默认值

    返回：
        float: 解析的浮点值
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_config() -> MetaPlannerConfig:
    """从环境变量加载配置。

    此函数从环境变量读取所有配置值，
    并构造一个带有适当类型转换和验证的 MetaPlannerConfig 对象。

    返回：
        MetaPlannerConfig: 验证过的配置对象

    异常：
        ValueError: 如果缺少必需的环境变量或无效
    """
    return MetaPlannerConfig(
        # Required API Keys
        openai_api_key=os.getenv("OPENAI_API_KEY", ""),
        tavily_api_key=os.getenv("TAVILY_API_KEY", ""),
        # Model Configuration
        openai_base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        chat_model=os.getenv("CHAT_MODEL", "gpt-4-turbo"),
        model_temperature=_parse_float(os.getenv("MODEL_TEMPERATURE"), 0.7),
        model_max_tokens=_parse_int(os.getenv("MODEL_MAX_TOKENS"), 32000),
        model_stream=_parse_bool(os.getenv("MODEL_STREAM"), True),
        # Agent Configuration
        agent_name=os.getenv("AGENT_NAME", "Task-Meta-Planner"),
        agent_operation_dir=os.getenv("AGENT_OPERATION_DIR"),
        agent_state_saving_dir=os.getenv("AGENT_STATE_SAVING_DIR", "./agent-states"),
        agent_max_iters=_parse_int(os.getenv("AGENT_MAX_ITERS"), 100),
        agent_worker_max_iters=_parse_int(os.getenv("AGENT_WORKER_MAX_ITERS"), 20),
        # Planner Configuration
        planner_mode=os.getenv("PLANNER_MODE", "dynamic"),  # type: ignore
        # Tool Configuration
        tool_response_budget=_parse_int(os.getenv("TOOL_RESPONSE_BUDGET"), 8194 * 5),
        # Logging Configuration
        log_level=os.getenv("LOG_LEVEL", "DEBUG"),
        enable_logfire=_parse_bool(os.getenv("ENABLE_LOGFIRE"), False),
        # MCP Configuration
        mcp_npx_command=os.getenv("MCP_NPX_COMMAND", "npx"),
        mcp_tavily_package=os.getenv("MCP_TAVILY_PACKAGE", "tavily-mcp@latest"),
        mcp_filesystem_package=os.getenv(
            "MCP_FILESYSTEM_PACKAGE", "@modelcontextprotocol/server-filesystem"
        ),
    )


# 全局配置实例
config = load_config()


# 为方便起见导出常用值
__all__ = [
    "config",
    "MetaPlannerConfig",
    "load_config",
]
