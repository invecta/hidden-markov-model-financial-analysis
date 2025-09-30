# PythonAnywhere Deployment Instructions

## Step-by-Step Deployment Guide

### 1. Create PythonAnywhere Account
1. Go to [pythonanywhere.com](https://pythonanywhere.com)
2. Sign up for a free account
3. Verify your email address

### 2. Upload Your Code

#### Option A: Direct Upload
1. Go to the **Files** tab in your PythonAnywhere dashboard
2. Navigate to `/home/yourusername/`
3. Create a new directory: `financial-analyst-project`
4. Upload all your project files:
   - `main.py`
   - `requirements.txt`
   - `wsgi.py`
   - `static/index.html`
   - `README.md`

#### Option B: Git Clone (Recommended)
1. Go to the **Consoles** tab
2. Open a new Bash console
3. Clone your repository:
   ```bash
   git clone https://github.com/yourusername/financial-analyst-project.git
   cd financial-analyst-project
   ```

### 3. Set Up Virtual Environment
1. In the Bash console, create a virtual environment:
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 financial-analyst
   ```
2. Activate the virtual environment:
   ```bash
   workon financial-analyst
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### 4. Configure Web App
1. Go to the **Web** tab in your PythonAnywhere dashboard
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"**
4. Select **Python 3.10**
5. Click **"Next"**

### 5. Update WSGI Configuration
1. In the Web tab, find the **WSGI configuration file** link
2. Click on it to edit the file
3. Replace the entire content with:
   ```python
   import sys
   import os
   
   # Add the project directory to Python path
   project_dir = '/home/yourusername/financial-analyst-project'
   if project_dir not in sys.path:
       sys.path.append(project_dir)
   
   # Import the FastAPI application
   from main import app
   
   # WSGI application object
   application = app
   ```
4. **Important**: Replace `yourusername` with your actual PythonAnywhere username
5. Save the file

### 6. Configure Static Files
1. In the Web tab, scroll down to **Static files**
2. Add a new static file mapping:
   - **URL**: `/static/`
   - **Directory**: `/home/yourusername/financial-analyst-project/static/`
3. Click **"Add"**

### 7. Reload Web App
1. In the Web tab, click the **"Reload"** button
2. Wait for the reload to complete
3. Your app should now be live at: `https://yourusername.pythonanywhere.com`

### 8. Test Your Application
1. Visit your web app URL
2. Test the following features:
   - Market overview loads
   - Stock analysis works
   - Portfolio analysis functions
   - Charts display correctly

## Troubleshooting

### Common Issues and Solutions

#### 1. Import Errors
**Problem**: Module not found errors
**Solution**: 
- Check that all dependencies are installed in the virtual environment
- Verify the Python path in WSGI configuration
- Ensure the virtual environment is activated

#### 2. Static Files Not Loading
**Problem**: CSS/JS files not loading
**Solution**:
- Check static file mapping in Web tab
- Verify file paths are correct
- Ensure files are uploaded to the correct directory

#### 3. Application Not Starting
**Problem**: 500 Internal Server Error
**Solution**:
- Check the error log in the Web tab
- Verify WSGI configuration syntax
- Ensure all required files are present

#### 4. Data Not Loading
**Problem**: Stock data not fetching
**Solution**:
- Check internet connectivity
- Verify Yahoo Finance API is accessible
- Check for rate limiting issues

### Error Logs
To view error logs:
1. Go to the **Web** tab
2. Click on **"Error log"** link
3. Check for any error messages
4. Common log locations:
   - `/var/log/yourusername.pythonanywhere.com.error.log`
   - `/var/log/yourusername.pythonanywhere.com.access.log`

### Performance Optimization

#### 1. Enable Caching
Add caching headers to improve performance:
```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

@app.middleware("http")
async def add_cache_headers(request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "public, max-age=300"
    return response
```

#### 2. Database Integration
For production use, consider adding a database:
```python
# Add to requirements.txt
# sqlalchemy==2.0.23
# alembic==1.12.1
```

#### 3. Environment Variables
Use environment variables for configuration:
```python
import os
from dotenv import load_dotenv

load_dotenv()

# Use environment variables
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
```

## Free Account Limitations

### What's Included
- 1 web app
- 512 MB RAM
- 1 GB disk space
- 3 months free, then $5/month

### Limitations
- No custom domains on free plan
- Limited CPU seconds per day
- No background tasks
- Limited file uploads

### Upgrade Options
- **Hacker Plan**: $5/month
  - Custom domains
  - More CPU seconds
  - Background tasks
  - More disk space

## Security Considerations

### 1. API Rate Limiting
Implement rate limiting to prevent abuse:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/stock/{symbol}")
@limiter.limit("10/minute")
async def get_stock(request: Request, symbol: str):
    # Your code here
```

### 2. Input Validation
Validate all inputs:
```python
from pydantic import BaseModel, validator

class StockRequest(BaseModel):
    symbol: str
    period: str
    
    @validator('symbol')
    def validate_symbol(cls, v):
        if not v.isalpha() or len(v) > 10:
            raise ValueError('Invalid stock symbol')
        return v.upper()
```

### 3. Error Handling
Implement proper error handling:
```python
from fastapi import HTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## Monitoring and Maintenance

### 1. Regular Updates
- Update dependencies regularly
- Monitor for security vulnerabilities
- Keep PythonAnywhere account active

### 2. Performance Monitoring
- Monitor CPU usage
- Check memory consumption
- Review error logs regularly

### 3. Backup Strategy
- Keep code in version control
- Export important data regularly
- Document configuration changes

## Support Resources

### PythonAnywhere Documentation
- [PythonAnywhere Help](https://help.pythonanywhere.com/)
- [Web App Configuration](https://help.pythonanywhere.com/pages/WebAppConfiguration/)
- [WSGI Configuration](https://help.pythonanywhere.com/pages/WSGIConfiguration/)

### Community Support
- [PythonAnywhere Forum](https://www.pythonanywhere.com/forums/)
- [Stack Overflow](https://stackoverflow.com/questions/tagged/pythonanywhere)
- [Reddit r/PythonAnywhere](https://www.reddit.com/r/PythonAnywhere/)

### FastAPI Resources
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)
- [FastAPI GitHub](https://github.com/tiangolo/fastapi)

---

**Your Financial Data Analyst Dashboard is now ready for the world! 🚀📊**



