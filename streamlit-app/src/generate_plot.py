import streamlit as st
from streamlit.runtime.uploaded_file_manager import UploadedFile

from loguru import logger
from src.plot_agent_client.request_be import BeRequest


class GeneratePlot:
    """
    Class to generate plots based on user input and uploaded data files.
    """
    def __init__(self, ip: str = "127.0.0.1", port: int = 8000, protocol: str = "http") -> None:
        self._request_be = BeRequest(ip, port, protocol)

        st.session_state["uploaded_file"] = st.session_state.get("uploaded_file", None)

    def build_upload_widget(self) -> UploadedFile | None:
        """
        Builds the upload widget for the Streamlit app.
        Allows users to upload data files for plotting.
        """
        uploaded_file = st.file_uploader("Upload your data files here...", accept_multiple_files=False)
        if uploaded_file:
            return uploaded_file
        else:
            return None

    def build_user_prompt(self) -> None:
        """
        Builds the user prompt input widget for the Streamlit app.
        Allows users to specify their plotting requirements.
        """
        uploaded_file = self.build_upload_widget()
        user_prompt = st.text_area("Enter your plotting requirements here...")
        submit_button = st.button("Generate Plot")

        if user_prompt and submit_button and uploaded_file:
            with st.spinner("Generating plot..."):
                print(f"User prompt: {user_prompt}, uploaded file: {uploaded_file.name}")
                try:
                    response_json = self._request_be.post("generate_plot", user_prompt, uploaded_file)
                    plot_path = response_json.get("plot_path").replace("/", "_")
                    with st.container(border=True):
                        st.write(f"**Tool used:** {response_json['tool_used']}")
                        image = self._request_be.get(f"plot_path/{plot_path}/download")
                        st.image(image, caption=response_json["code_summary"])
                        logger.info(f"Plot generation successful: {response_json}.")

                except RuntimeError as e:
                    st.error(f"Error generating plot: {e}")
                    return

    def build_page(self) -> None:
        """
        Builds the main page of the Streamlit app.
        Combines the upload widget and user prompt for generating plots.
        """
        self.build_user_prompt()


generate_plot = GeneratePlot()
generate_plot.build_page()
