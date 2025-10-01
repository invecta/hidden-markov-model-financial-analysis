from fastapi import FastAPI, Request
# from fastapi.staticfiles import StaticFiles
# from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Financial Analysis Dashboard", version="1.0.0")

# Get the directory where this script is located
current_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.join(current_dir, "static")
templates_dir = os.path.join(current_dir, "templates")

# Create templates directory if it doesn't exist
os.makedirs(templates_dir, exist_ok=True)

# Mount static files
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    logger.warning(f"Static directory {static_dir} does not exist")

# Setup templates
templates = Jinja2Templates(directory=templates_dir)

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial Analysis Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .header { text-align: center; color: #333; }
            .status { background: #e8f5e8; padding: 20px; border-radius: 5px; margin: 20px 0; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="header">Financial Analysis Dashboard</h1>
            <div class="status">
                <h2>Application Status: Running</h2>
                <p>Your FastAPI application is successfully deployed on PythonAnywhere!</p>
                <p>Environment: Production</p>
                <p>API Keys: Configured</p>
            </div>
            <h3>Available Endpoints:</h3>
            <ul>
                <li><a href="/docs">API Documentation (Swagger UI)</a></li>
                <li><a href="/redoc">API Documentation (ReDoc)</a></li>
                <li><a href="/health">Health Check</a></li>
            </ul>
        </div>
    </body>
    </html>
    '''

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "message": "Financial Analysis Dashboard is running",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "debug": os.getenv("DEBUG", "False")
    }

@app.get("/api/status")
async def api_status():
    return {
        "api_name": "Financial Analysis Dashboard",
        "version": "1.0.0",
        "status": "operational",
        "endpoints": [
            "/",
            "/health",
            "/api/status",
            "/docs",
            "/redoc"
        ]
    }
