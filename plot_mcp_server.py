# FastMCP Server with Python and R Plot Execution
from pydantic import BaseModel
from mcp.server.fastmcp import FastMCP
import matplotlib.pyplot as plt
import pandas as pd
import os
import uuid
import rpy2.robjects as robjects

mcp_server = FastMCP("Plot")

OUTPUT_DIR = "plots"
os.makedirs(OUTPUT_DIR, exist_ok=True)

class CodeRequest(BaseModel):
    file_path: str
    code: str

class InstallRequest(BaseModel):
    library_name: str

# Route 1: Execute Python Code
@mcp_server.tool()
def plot_python(req: CodeRequest) -> dict:
    """
    Executes Python code to generate a plot from a CSV or Excel file.

    :param req: CodeRequest object containing the file path and Python code to execute.
    :return: Dictionary with the path to the generated plot or an error message.
    """
    df = pd.read_csv(req.file_path) if req.file_path.endswith(".csv") else pd.read_excel(req.file_path)
    context = {"df": df, "plt": plt}
    try:
        exec(req.code, context)
        plot_id = str(uuid.uuid4()) + ".png"
        plot_path = os.path.join(OUTPUT_DIR, plot_id)
        plt.savefig(plot_path)
        plt.clf()
        return {"plot_path": plot_path}
    except Exception as e:
        return {"error": str(e)}

@mcp_server.tool()
def get_df_infos_python(req: CodeRequest) -> dict:
    """
    Executes python code which allows to extract metadata from a CSV or Excel file.
    The code should store all calculated metadata in the `res` dictionary.

    :param req: CodeRequest object containing the file path.
    :return: Dictionary metadata about the DataFrame, including the first few rows.
    """
    df = pd.read_csv(req.file_path) if req.file_path.endswith(".csv") else pd.read_excel(req.file_path)
    try:
        context = {"df": df, "res": {}}
        exec(req.code, context)
        res = context["res"]
        res["df_head"] = df.head()
        return res
    except Exception as e:
        return {"error": str(e)}

# Route 2: Execute R Code via rpy2
@mcp_server.tool()
def plot_r(req: CodeRequest) -> dict:
    """
    Executes R code to generate a plot from a CSV or Excel file.

    :param req: CodeRequest object containing the file path and R code to execute.
    :return: A dictionary with the path to the generated plot or an error message.
    """
    try:
        if req.file_path.endswith(".csv"):
            robjects.r(f"""data <- read.csv('{req.file_path.replace('\\', '/')}')""")
        else:
            robjects.r(f"""data <- readxl::read_excel('{req.file_path.replace('\\', '/')}')""")

        plot_id = str(uuid.uuid4()) + ".png"
        plot_path = os.path.abspath(os.path.join(OUTPUT_DIR, plot_id))
        robjects.r(f"png('{plot_path.replace('\\', '/')}')")
        robjects.r(req.code)
        robjects.r("dev.off()")
        return {"plot_path": plot_path}
    except Exception as e:
        return {"error": str(e)}

@mcp_server.tool()
def install_python_library(library_name: str) -> dict:
    """
    Installs a Python library using pip.

    :param library_name: Name of the Python library to install.
    :return: Dictionary with success or error message.
    """
    import subprocess
    try:
        subprocess.check_call(["pip", "install", library_name])
        return {"message": f"Successfully installed {library_name}"}
    except subprocess.CalledProcessError as e:
        return {"error": str(e)}

@mcp_server.tool()
def install_r_library(library_name: str) -> dict:
    """
    Installs an R library using install.packages.

    :param library_name: Name of the R library to install.
    :return: Dictionary with success or error message.
    """
    try:
        robjects.r(f"install.packages('{library_name}')")
        return {"message": f"Successfully installed {library_name}"}
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    mcp_server.run(transport="stdio")