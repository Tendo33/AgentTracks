from abc import ABC, abstractmethod

from dotenv import load_dotenv
from langchain_openai import ChatOpenAI


class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

        load_dotenv()
        self.llm = ChatOpenAI(model="o4-mini")

    @abstractmethod
    def run(self, input: str) -> str:
        pass

    def invoke(self, input: str) -> str:
        return self.llm.invoke(input)
