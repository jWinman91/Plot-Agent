import requests
from src.plot_agent_client.response_be import BeResponse
from streamlit.runtime.uploaded_file_manager import UploadedFile


class BeRequest:
    def __init__(self, ip: str = "127.0.0.1", port: int = 8000, protocol: str = "http"):
        """
        Initializes the BeRequest with the backend server's IP, port, and protocol.

        :param ip: IP address of the backend server.
        :param port: Port number of the backend server.
        :param protocol: Protocol to use for the request (default is "http").
        """
        self._url = f"{protocol}://{ip}:{port}"

    def get(self, path: str) -> dict:
        """
        Sends a GET request to the backend server.

        :param path: Path to the endpoint on the backend server.
        :return: Dictionary containing the response from the backend.
        """
        response = requests.get(f"{self._url}/{path}")
        if response.status_code != 200:
            raise RuntimeError(f"GET request failed with status code {response.status_code}: {response.reason}")
        else:
            return BeResponse(response=response).image_bytes()

    def post(self, path: str, user_prompt: str, data_file: UploadedFile) -> dict:
        """
        Sends a POST request to the backend with a user prompt and a data file.

        :param path: Path to the endpoint on the backend server.
        :param user_prompt: User's prompt to be sent with the request.
        :param data_file: Data file to be uploaded with the request.
        :return: Dictionary containing the response from the backend.
        """
        files = {"file": data_file}
        data = {"user_prompt": user_prompt}
        print(f"Sending POST request to {self._url}/{path} with data: {data} and files: {files}")
        response = BeResponse(response=requests.post(f"{self._url}/{path}", data=data, files=files))

        if response.is_error():
            raise RuntimeError("Something went wrong with the post request...")
        else:
            return response.json()
