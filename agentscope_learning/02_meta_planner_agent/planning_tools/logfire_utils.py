import os

import dotenv
import logfire

# 加载环境变量
dotenv.load_dotenv()
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")


def configure_logfire():
    """配置 logfire 日志记录"""
    logfire.configure(token=LOGFIRE_TOKEN)
    logfire.instrument_openai()
