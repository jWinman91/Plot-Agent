import uvicorn, os, yaml, subprocess
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse
from typing import List
from loguru import logger

from src.plot_agent import PlotAgent


class PlotAgentApp:
    def __init__(self, ip: str = "127.0.0.1", port: int = 8000, output_dir: str = "data", config_path: str = "config.yaml"):
        """
        Initializes the PlotAgentApp with the given parameters.

        :param ip:
        :param port:
        :param output_dir:
        :param config_path:
        """
        self._ip = ip
        self._port = port

        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        config = self.load_prompt(config_path)
        self.plot_agent = PlotAgent(**config)

        self.app = FastAPI()
        self._register_routes()

    async def create(self) -> None:
        """
        Connects to the MCP server and initializes the agent.
        """
        await self.plot_agent.create()

    def save_file(self, file: UploadFile) -> str:
        """
        Save the uploaded file to the output directory.
        :param file: UploadFile object
        :return: Path to the saved file
        """
        file_path = os.path.join(self.output_dir, file.filename)
        with open(file_path, "wb") as f:
            content = file.file.read()
            f.write(content)
        return file_path

    @staticmethod
    def load_prompt(config_path: str) -> dict:
        """
        Loads in a system prompt (and additional parameters) for the LLM and returns them as a tuple.
        :param config_path: path to yaml file
        :return: Tuple containing the system prompt and additional parameters
        """
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        return config

    @staticmethod
    def get_file_metadata(file_path: str) -> List[str]:
        """
        Extracts metadata from the file to be used in the prompt.
        :param file_path: Path to the uploaded file
        :return: Tuple containing the file name and column names
        """
        import pandas as pd

        # Read the file to extract metadata
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        elif file_path.endswith('.xlsx'):
            df = pd.read_excel(file_path)
        else:
            raise ValueError("Unsupported file type. Only CSV and Excel files are supported.")

        col_names = df.columns.tolist()
        return col_names

    def _register_routes(self):
        @self.app.post("/generate_plot")
        async def generate_plot(user_prompt: str = Form(...), file: UploadFile = File(...)) -> dict:
            # save file to a temporary location
            file_path = self.save_file(file)
            col_names = self.get_file_metadata(file_path)

            response_dict = await self.plot_agent.predict(user_prompt, file_path, col_names)
            logger.info(f"Agent response: {response_dict}")

            # Extract the plot path from the response
            logger.info(f"File saved at: {response_dict['plot_path']}")
            logger.info(f"Tool used: {response_dict['tool_used']}")

            return response_dict

        @self.app.get("/plot_path/{plot_path:path}/download")
        async def download_file(plot_path: str) -> FileResponse:
            """
            Endpoint to download a file.
            :param plot_path: Name of the file to download
            :return: FileResponse with the requested file
            """
            if os.path.exists(plot_path):
                return FileResponse(plot_path, media_type='image/png', filename=os.path.basename(plot_path))
            else:
                raise FileNotFoundError(f"File {plot_path} not found")

    def run(self) -> None:
        """
        Run the api
        :return: None
        """
        uvicorn.run(self.app, host=self._ip, port=self._port)
        subprocess.run("rm plots/*.png", shell=True)


if __name__ == "__main__":
    app = PlotAgentApp()
    import asyncio
    asyncio.run(app.create())
    app.run()