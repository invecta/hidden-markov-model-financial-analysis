# PythonAnywhere Deployment Guide for Hidden Markov Model Financial Analysis

## Step 1: Upload Your Code

### Option A: Using Git (Recommended)
1. In PythonAnywhere console, navigate to your home directory:
   `ash
   cd /home/hindaouihani
   `

2. Clone your repository:
   `ash
   git clone https://github.com/invecta/hidden-markov-model-financial-analysis.git
   `

### Option B: Manual Upload
1. Create a ZIP file of your project folder
2. Upload via PythonAnywhere Files tab
3. Extract in /home/hindaouihani/

## Step 2: Set Up Virtual Environment

1. Create virtual environment:
   `ash
   mkvirtualenv --python=/usr/bin/python3.10 hidden-markov-model
   `

2. Activate virtual environment:
   `ash
   workon hidden-markov-model
   `

3. Install dependencies:
   `ash
   cd /home/hindaouihani/hidden-markov-model-financial-analysis
   pip install -r requirements.txt
   `

## Step 3: Configure Web App

### Web App Settings:
- **Source code**: /home/hindaouihani/hidden-markov-model-financial-analysis
- **Working directory**: /home/hindaouihani/hidden-markov-model-financial-analysis
- **WSGI configuration file**: /var/www/hindaouihani_pythonanywhere_com_wsgi.py
- **Python version**: 3.10
- **Virtualenv**: /home/hindaouihani/.virtualenvs/hidden-markov-model

### WSGI Configuration:
Replace the content of /var/www/hindaouihani_pythonanywhere_com_wsgi.py with:

`python
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
`

## Step 4: Static Files Configuration

Add static file mapping:
- **URL**: /static
- **Directory**: /home/hindaouihani/hidden-markov-model-financial-analysis/static

## Step 5: Environment Variables (Optional)

If you need API keys, create a .env file:
`ash
echo "ALPACA_API_KEY=your_key_here" > .env
echo "ALPACA_SECRET_KEY=your_secret_here" >> .env
echo "ALPACA_BASE_URL=https://paper-api.alpaca.markets" >> .env
`

## Step 6: Reload Web App

Click the "Reload" button in the Web tab.

## Step 7: Test Your Application

Visit: https://hindaouihani.pythonanywhere.com

## Troubleshooting

### Common Issues:

1. **Import Errors**: Check that all dependencies are installed in the virtual environment
2. **Static Files Not Loading**: Verify static file mapping in Web app configuration
3. **WSGI Errors**: Check the error log for specific error messages
4. **Port Issues**: PythonAnywhere handles ports automatically, no need to specify

### Log Files:
- Access log: hindaouihani.pythonanywhere.com.access.log
- Error log: hindaouihani.pythonanywhere.com.error.log
- Server log: hindaouihani.pythonanywhere.com.server.log

## Features Available After Deployment:

- Real-time stock analysis dashboard
- Hidden Markov Model predictions
- Interactive charts and visualizations
- Portfolio management tools
- API endpoints for programmatic access
- Responsive web interface

## API Endpoints:
- GET / - Main dashboard
- GET /docs - API documentation
- GET /api/stock/{symbol} - Stock analysis
- GET /api/market-overview - Market overview
- POST /api/portfolio - Portfolio analysis
- GET /api/hmm/train - Train HMM model
- GET /api/hmm/predict - Get predictions

Your Hidden Markov Model Financial Analysis application will be live at:
https://hindaouihani.pythonanywhere.com
