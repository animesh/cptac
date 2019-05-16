import webbrowser
import textwrap
import os

def list_data():
    """List all available datasets."""
    print("Available datasets:")
    print("Endometrial")
    print("Ovarian")
    print("Colon")

def list_api():
    """Print docstrings for all accessible functions."""
    help(__name__)

def embargo():
    """Open CPTAC embargo details in web browser."""
    print("Opening embargo details in web browser...")
    webbrowser.open("https://proteomics.cancer.gov/data-portal/about/data-use-agreement")

def version():
    """Print version number of CPTAC package."""
    version = {}
    with open(dir_path + os.sep + "version.py") as fp:
    	exec(fp.read(), version)
    return(version['__version__'])

dir_path = os.path.dirname(os.path.realpath(__file__))
message = "Welcome to the CPTAC data service package. Available datasets may be viewed using CPTAC.list_data(). In order to access a specific data set, import a CPTAC subfolder using either \'import CPTAC.Dataset\' or \'from CPTAC import Dataset\'.\n"
wrapped_list = textwrap.wrap(message)
for line in wrapped_list:
    print(line)
print("******")
print("Version:",version())
print("******")
