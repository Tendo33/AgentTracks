# -*- coding: utf-8 -*-
"""Configuration management for Meta Planner Agent.

This module centralizes all configuration parameters for the Meta Planner Agent,
loading values from environment variables with sensible defaults.

Environment Variables:
    # Required API Keys
    OPENAI_API_KEY: OpenAI API key for model access
    TAVILY_API_KEY: Tavily API key for search functionality

    # Optional Model Configuration
    OPENAI_BASE_URL: Base URL for OpenAI API (default: https://api.openai.com/v1)
    CHAT_MODEL: Model name to use (default: gpt-4-turbo)
    MODEL_TEMPERATURE: Model temperature (default: 0.7)
    MODEL_MAX_TOKENS: Maximum tokens per generation (default: 32000)
    MODEL_STREAM: Enable streaming responses (default: true)

    # Optional Agent Configuration
    AGENT_OPERATION_DIR: Custom working directory for agent operations
    AGENT_STATE_SAVING_DIR: Directory to save agent states (default: ./agent-states)
    AGENT_MAX_ITERS: Maximum reasoning-action iterations (default: 100)
    AGENT_WORKER_MAX_ITERS: Maximum worker iterations (default: 20)

    # Optional Planner Configuration
    PLANNER_MODE: Planning mode (default: dynamic)
                  Options: disable, dynamic, enforced

    # Optional Tool Configuration
    TOOL_RESPONSE_BUDGET: Maximum characters in tool responses (default: 40970)

    # Optional Logging Configuration
    LOG_LEVEL: Logging level (default: DEBUG)
               Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
    ENABLE_LOGFIRE: Enable logfire logging (default: false)

    # Optional MCP Configuration
    MCP_NPX_COMMAND: NPX command for MCP clients (default: npx)
    MCP_TAVILY_PACKAGE: Tavily MCP package (default: tavily-mcp@latest)
    MCP_FILESYSTEM_PACKAGE: Filesystem MCP package
                            (default: @modelcontextprotocol/server-filesystem)

Usage:
    from config import config

    # Access configuration values
    api_key = config.openai_api_key
    model_name = config.chat_model

    # Get agent working directory
    working_dir = config.get_agent_working_dir()
"""

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Optional

import dotenv

# Load environment variables from .env file
dotenv.load_dotenv()


@dataclass
class MetaPlannerConfig:
    """Configuration dataclass for Meta Planner Agent.

    This class provides a centralized configuration interface with type hints
    and validation. All values are loaded from environment variables with
    sensible defaults.
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
        """Validate configuration after initialization."""
        if not self.tavily_api_key:
            raise ValueError(
                "TAVILY_API_KEY environment variable is required. "
                "Please set it in your .env file or environment."
            )

        # Validate planner mode
        valid_modes = ["disable", "dynamic", "enforced"]
        if self.planner_mode not in valid_modes:
            raise ValueError(
                f"Invalid planner_mode: {self.planner_mode}. "
                f"Must be one of: {', '.join(valid_modes)}"
            )

        # Validate log level
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(
                f"Invalid log_level: {self.log_level}. "
                f"Must be one of: {', '.join(valid_log_levels)}"
            )
        self.log_level = self.log_level.upper()

    def get_agent_working_dir(self) -> str:
        """Get the agent working directory path.

        Returns the configured agent operation directory, or defaults to
        'meta_agent_demo_env' in the current module's directory.

        Returns:
            str: Absolute path to the agent working directory
        """
        if self.agent_operation_dir:
            return os.path.abspath(self.agent_operation_dir)

        # Default to meta_agent_demo_env in the same directory as this config
        default_dir = Path(__file__).parent / "meta_agent_demo_env"
        return str(default_dir.absolute())

    def get_state_saving_dir(self, time_str: str) -> str:
        """Get the state saving directory for a specific run.

        Args:
            time_str: Timestamp string to identify the run

        Returns:
            str: Path to the state saving directory for this run
        """
        return os.path.join(self.agent_state_saving_dir, f"run-{time_str}")

    def to_dict(self) -> dict:
        """Convert configuration to dictionary.

        Returns:
            dict: Configuration as a dictionary
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
    """Parse a boolean value from environment variable string.

    Args:
        value: String value from environment variable
        default: Default value if parsing fails

    Returns:
        bool: Parsed boolean value
    """
    if value is None:
        return default
    return value.lower() in ("true", "1", "yes", "on", "t")


def _parse_int(value: Optional[str], default: int) -> int:
    """Parse an integer value from environment variable string.

    Args:
        value: String value from environment variable
        default: Default value if parsing fails

    Returns:
        int: Parsed integer value
    """
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def _parse_float(value: Optional[str], default: float) -> float:
    """Parse a float value from environment variable string.

    Args:
        value: String value from environment variable
        default: Default value if parsing fails

    Returns:
        float: Parsed float value
    """
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


def load_config() -> MetaPlannerConfig:
    """Load configuration from environment variables.

    This function reads all configuration values from environment variables
    and constructs a MetaPlannerConfig object with proper type conversion
    and validation.

    Returns:
        MetaPlannerConfig: Validated configuration object

    Raises:
        ValueError: If required environment variables are missing or invalid
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


# Global configuration instance
config = load_config()


# Export commonly used values for convenience
__all__ = [
    "config",
    "MetaPlannerConfig",
    "load_config",
]
