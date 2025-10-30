import os

import dotenv
import logfire

dotenv.load_dotenv()
LOGFIRE_TOKEN = os.getenv("LOGFIRE_TOKEN")


def configure_logfire():
    logfire.configure(token=LOGFIRE_TOKEN)
    logfire.instrument_openai()
