# WSGI configuration for PythonAnywhere deployment
import sys
import os

# Add the project directory to Python path
project_dir = '/home/hindaouihani/hidden-markov-model-financial-analysis'
if project_dir not in sys.path:
    sys.path.append(project_dir)

# Import the FastAPI application
from main import app

# WSGI application object
application = app
