import json, re

from langgraph.prebuilt import create_react_agent
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_core.messages import AIMessage

from typing import List
from pprint import pprint
from loguru import logger


class PlotAgent:
    """
    A class that initializes a plotting agent capable of executing Python and R code
    """
    def __init__(self, model: dict, mcp_server_infos: dict, system_prompt: str, parameters: dict):
        """

        """
        self.mcp_client = None
        self.agent = None

        self.model = model["name"]
        self.mcp_server_infos = mcp_server_infos
        self.system_prompt = system_prompt
        self.parameters = parameters

    async def create(self) -> None:
        """
        Connects to the MCP server and initializes the agent with the provided model and tools.
        """
        # Step 1: Connect to the FastMCP server
        self.mcp_client = MultiServerMCPClient(self.mcp_server_infos)
        tools = await self.mcp_client.get_tools()

        # Step 2: Build LangChain agent with loaded tools
        self.agent = create_react_agent(self.model, tools)

    @staticmethod
    def extract_first_json(text: str) -> dict:
        """
        Extract the first valid JSON object from a mixed string.
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            json_match = re.search(r"```json\s*[\s\S]*?```", text, re.DOTALL)
            if not json_match:
                raise ValueError("No JSON object found in text.")

            json_str = json_match.group(0).replace("```json", "").replace("```", "").strip()
            return json.loads(json_str)

    def get_infos(self, response: dict) -> dict:
        """
        Extracts the plot path from the response.
        :param response: Response dictionary from the agent
        :return: Path to the generated plot
        """
        for message in reversed(response["messages"]):
            if isinstance(message, AIMessage):
                logger.info(message)
                return self.extract_first_json(message.content)
            else:
                continue

        raise ValueError("plot_path not found in response")

    async def predict(self, user_input: str, file_path: str, col_names: List[str]) -> dict:
        """
        Predicts the plot path based on user input.
        :param user_input: User input string
        :param file_path: Path to the uploaded file
        :param col_names: List of column names from the file
        :return: Path to the generated plot and the tool used
        """
        prompt = self.system_prompt.format(
            file_path=file_path,
            col_names=col_names,
            user_prompt=user_input

        )
        response = await self.agent.ainvoke({
            "messages": [
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            "response_format": {"type": "json_object"},
            **self.parameters
        })
        pprint(response)
        return self.get_infos(response)