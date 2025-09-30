# WSGI configuration for PythonAnywhere deployment
import sys
import os

# Add the project directory to Python path
project_dir = os.path.dirname(os.path.abspath(__file__))
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Import the FastAPI application
from main import app

# WSGI application object
application = app



