from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import logging
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json
from typing import List, Optional
import plotly.graph_objects as go
import plotly.express as px
from plotly.utils import PlotlyJSONEncoder
import requests
import os
from concurrent.futures import ThreadPoolExecutor
from scipy.optimize import minimize
# import ta  # Commented out due to installation issues
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

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

# Financial Analysis Class
class FinancialAnalyzer:
    def __init__(self):
        # Supported stocks
        self.supported_stocks = [
            'AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'META', 'NVDA', 'NFLX',
            'AMD', 'INTC', 'CRM', 'ADBE', 'PYPL', 'UBER', 'LYFT', 'SQ',
            'ROKU', 'ZM', 'DOCU', 'OKTA', 'SNOW', 'PLTR', 'CRWD', 'NET'
        ]
        
        # Initialize Alpaca API
        try:
            import alpaca_trade_api as tradeapi
            self.alpaca_api = tradeapi.REST(
                os.getenv('APCA_API_KEY_ID'),
                os.getenv('APCA_SECRET_KEY'),
                os.getenv('APCA_API_BASE_URL'),
                api_version='v2'
            )
        except ImportError:
            self.alpaca_api = None
            logger.warning("Alpaca API not available - install alpaca-trade-api")
        except Exception as e:
            self.alpaca_api = None
            logger.warning(f"Alpaca API initialization failed: {e}")
        
        # Polygon.io configuration
        self.polygon_api_key = os.getenv('POLYGON_API_KEY')
        self.polygon_base_url = os.getenv('POLYGON_BASE_URL')
        
        # Thread pool for concurrent API calls
        self.executor = None
    
    def get_stock_data(self, symbol: str, period: str = "1y") -> dict:
        """Fetch stock data from multiple sources (Alpaca, Polygon, Yahoo Finance)"""
        try:
            # Try Alpaca first for real-time data
            try:
                hist = self.get_alpaca_data(symbol, period)
                if not hist.empty:
                    return self.process_stock_data(hist, symbol)
            except:
                pass
            
            # Fallback to Yahoo Finance
            stock = yf.Ticker(symbol)
            hist = stock.history(period=period)
            
            if hist.empty:
                # Try with a different period
                hist = stock.history(period="1y")
                if hist.empty:
                    # Try with a different symbol format
                    hist = stock.history(period="1y", auto_adjust=True)
                    if hist.empty:
                        raise HTTPException(status_code=404, detail=f"No data found for {symbol} after trying multiple periods")
            
            return self.process_stock_data(hist, symbol)
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")
    
    def get_alpaca_data(self, symbol: str, period: str) -> pd.DataFrame:
        """Fetch data from Alpaca API"""
        # Convert period to Alpaca format
        end_date = datetime.now()
        if period == "1y":
            start_date = end_date - timedelta(days=365)
        elif period == "6mo":
            start_date = end_date - timedelta(days=180)
        elif period == "3mo":
            start_date = end_date - timedelta(days=90)
        elif period == "1mo":
            start_date = end_date - timedelta(days=30)
        else:
            start_date = end_date - timedelta(days=365)
        
        # Get bars from Alpaca
        if self.alpaca_api:
            try:
                import alpaca_trade_api as tradeapi
                bars = self.alpaca_api.get_bars(
                    symbol,
                    tradeapi.TimeFrame.Day,
                    start=start_date.strftime('%Y-%m-%d'),
                    end=end_date.strftime('%Y-%m-%d'),
                    adjustment='raw'
                ).df
                return bars
            except Exception as e:
                logger.warning(f"Alpaca API error: {e}")
                return pd.DataFrame()
        return pd.DataFrame()
    
    def get_polygon_data(self, symbol: str, period: str) -> dict:
        """Fetch additional data from Polygon.io"""
        try:
            # Get company info
            url = f"{self.polygon_base_url}/v3/reference/tickers/{symbol}"
            params = {'apikey': self.polygon_api_key}
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                return response.json()
            return {}
        except:
            return {}
    
    def process_stock_data(self, hist: pd.DataFrame, symbol: str) -> dict:
        """Process and enhance stock data with technical indicators"""
        # Calculate technical indicators manually (without ta library)
        hist['SMA_20'] = hist['Close'].rolling(window=20).mean()
        hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
        hist['EMA_12'] = hist['Close'].ewm(span=12).mean()
        hist['EMA_26'] = hist['Close'].ewm(span=26).mean()
        hist['RSI'] = self.calculate_rsi(hist['Close'], 14)
        hist['MACD'] = hist['EMA_12'] - hist['EMA_26']
        hist['MACD_signal'] = hist['MACD'].ewm(span=9).mean()
        hist['BB_upper'] = hist['SMA_20'] + (hist['Close'].rolling(window=20).std() * 2)
        hist['BB_lower'] = hist['SMA_20'] - (hist['Close'].rolling(window=20).std() * 2)
        hist['Volatility'] = hist['Close'].pct_change().rolling(window=20).std() * np.sqrt(252)
        hist['Volume_SMA'] = hist['Volume'].rolling(window=20).mean()
        
        # Calculate additional metrics
        hist['Price_Change'] = hist['Close'].pct_change()
        hist['Volume_Change'] = hist['Volume'].pct_change()
        hist['High_Low_Ratio'] = hist['High'] / hist['Low']
        
        # Get additional info from Polygon
        polygon_info = self.get_polygon_data(symbol, "1y")
        
        # Convert to JSON-serializable format
        data = {
            'symbol': symbol,
            'dates': hist.index.strftime('%Y-%m-%d').tolist(),
            'open': hist['Open'].fillna(0).tolist(),
            'high': hist['High'].fillna(0).tolist(),
            'low': hist['Low'].fillna(0).tolist(),
            'close': hist['Close'].fillna(0).tolist(),
            'volume': hist['Volume'].fillna(0).tolist(),
            'sma_20': hist['SMA_20'].fillna(0).tolist(),
            'sma_50': hist['SMA_50'].fillna(0).tolist(),
            'ema_12': hist['EMA_12'].fillna(0).tolist(),
            'ema_26': hist['EMA_26'].fillna(0).tolist(),
            'rsi': hist['RSI'].fillna(50).tolist(),
            'macd': hist['MACD'].fillna(0).tolist(),
            'macd_signal': hist['MACD_signal'].fillna(0).tolist(),
            'bb_upper': hist['BB_upper'].fillna(0).tolist(),
            'bb_lower': hist['BB_lower'].fillna(0).tolist(),
            'volatility': hist['Volatility'].fillna(0).tolist(),
            'volume_sma': hist['Volume_SMA'].fillna(0).tolist(),
            'price_change': hist['Price_Change'].fillna(0).tolist(),
            'volume_change': hist['Volume_Change'].fillna(0).tolist(),
            'high_low_ratio': hist['High_Low_Ratio'].fillna(1).tolist(),
            'current_price': hist['Close'].iloc[-1] if not hist.empty else 0,
            'company_info': polygon_info.get('results', {}) if polygon_info else {}
        }
        
        return data
    
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """Calculate Relative Strength Index"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def get_portfolio_analysis(self, symbols: List[str], weights: Optional[List[float]] = None) -> dict:
        """Analyze a portfolio of stocks"""
        if weights is None:
            weights = [1.0 / len(symbols)] * len(symbols)
        
        if len(symbols) != len(weights):
            raise HTTPException(status_code=400, detail="Number of symbols and weights must match")
        
        portfolio_data = {}
        returns_data = {}
        
        for symbol, weight in zip(symbols, weights):
            try:
                stock_data = self.get_stock_data(symbol, "1y")
                prices = stock_data['close']
                returns = [0] + [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
                returns_data[symbol] = returns
                portfolio_data[symbol] = {
                    'weight': weight,
                    'current_price': prices[-1],
                    'returns': returns
                }
            except:
                continue
        
        # Calculate portfolio metrics
        if returns_data:
            portfolio_returns = []
            for i in range(len(list(returns_data.values())[0])):
                daily_return = sum(returns_data[symbol][i] * weights[j] 
                                 for j, symbol in enumerate(returns_data.keys()))
                portfolio_returns.append(daily_return)
            
            # Calculate portfolio statistics
            portfolio_volatility = np.std(portfolio_returns) * np.sqrt(252)
            portfolio_return = np.mean(portfolio_returns) * 252
            sharpe_ratio = portfolio_return / portfolio_volatility if portfolio_volatility > 0 else 0
            
            return {
                'portfolio_return': portfolio_return,
                'portfolio_volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'stocks': portfolio_data,
                'daily_returns': portfolio_returns
            }
        
        return {'error': 'No valid stock data found'}

analyzer = FinancialAnalyzer()

@app.get("/")
async def read_root():
    """Serve the main dashboard"""
    try:
        static_dir = os.path.join(os.path.dirname(__file__), "static")
        index_path = os.path.join(static_dir, "index.html")
        with open(index_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    except FileNotFoundError:
        return HTMLResponse(content="""
        <html>
            <head><title>Financial Data Analyst</title></head>
            <body>
                <h1>Financial Data Analyst Dashboard</h1>
                <p>API is running! Frontend will be available once deployed.</p>
                <p>Try: <a href="/docs">/docs</a> for API documentation</p>
            </body>
        </html>
        """)

@app.get("/api/stocks")
async def get_supported_stocks():
    """Get list of supported stock symbols"""
    return {"stocks": analyzer.supported_stocks}

@app.get("/api/stock/{symbol}")
async def get_stock(symbol: str, period: str = "1y"):
    """Get stock data and analysis for a specific symbol"""
    if symbol.upper() not in analyzer.supported_stocks:
        raise HTTPException(status_code=400, detail=f"Stock {symbol} not supported")
    
    return analyzer.get_stock_data(symbol.upper(), period)

@app.post("/api/portfolio")
async def analyze_portfolio(request: dict):
    """Analyze a portfolio of stocks"""
    symbols = request.get('symbols', [])
    weights = request.get('weights', None)
    
    if not symbols:
        raise HTTPException(status_code=400, detail="At least one stock symbol required")
    
    return analyzer.get_portfolio_analysis(symbols, weights)

@app.get("/api/market-overview")
async def get_market_overview():
    """Get overview of all supported stocks with enhanced data"""
    overview = {}
    
    # Use thread pool for concurrent API calls
    def get_stock_overview(symbol):
        try:
            # Try to get real-time data from Alpaca first
            if analyzer.alpaca_api:
                try:
                    latest_bar = analyzer.alpaca_api.get_latest_bar(symbol)
                    if latest_bar:
                        return {
                            'symbol': symbol,
                            'current_price': round(latest_bar.c, 2),
                            'change': round(latest_bar.c - latest_bar.o, 2),
                            'change_percent': round(((latest_bar.c - latest_bar.o) / latest_bar.o) * 100, 2),
                            'volume': latest_bar.v,
                            'high': round(latest_bar.h, 2),
                            'low': round(latest_bar.l, 2),
                            'source': 'alpaca'
                        }
                except:
                    pass
            
            # Fallback to Yahoo Finance
            stock = yf.Ticker(symbol)
            info = stock.info
            hist = stock.history(period="5d")
            
            if not hist.empty:
                current_price = hist['Close'].iloc[-1]
                change = hist['Close'].iloc[-1] - hist['Close'].iloc[-2]
                change_percent = (change / hist['Close'].iloc[-2]) * 100
                
                return {
                    'symbol': symbol,
                    'name': info.get('longName', symbol),
                    'current_price': round(current_price, 2),
                    'change': round(change, 2),
                    'change_percent': round(change_percent, 2),
                    'volume': hist['Volume'].iloc[-1],
                    'high': round(hist['High'].iloc[-1], 2),
                    'low': round(hist['Low'].iloc[-1], 2),
                    'source': 'yahoo'
                }
        except:
            return None
    
    # Get data for all stocks concurrently
    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(get_stock_overview, symbol) for symbol in analyzer.supported_stocks[:8]]
        results = [future.result() for future in futures if future.result() is not None]
    
    # Convert to dictionary format
    for result in results:
        if result:
            overview[result['symbol']] = result
    
    return overview

@app.get("/api/real-time/{symbol}")
async def get_real_time_data(symbol: str):
    """Get real-time data for a specific symbol"""
    try:
        # Get latest bar from Alpaca
        if analyzer.alpaca_api:
            latest_bar = analyzer.alpaca_api.get_latest_bar(symbol)
            
            if latest_bar:
                return {
                    'symbol': symbol,
                    'timestamp': latest_bar.t.isoformat(),
                    'open': round(latest_bar.o, 2),
                    'high': round(latest_bar.h, 2),
                    'low': round(latest_bar.l, 2),
                    'close': round(latest_bar.c, 2),
                    'volume': latest_bar.v,
                    'vwap': round(latest_bar.vw, 2) if hasattr(latest_bar, 'vw') else None
                }
        
        # Fallback to Yahoo Finance
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        
        if not hist.empty:
            latest = hist.iloc[-1]
            return {
                'symbol': symbol,
                'timestamp': hist.index[-1].isoformat(),
                'open': round(latest['Open'], 2),
                'high': round(latest['High'], 2),
                'low': round(latest['Low'], 2),
                'close': round(latest['Close'], 2),
                'volume': int(latest['Volume']),
                'vwap': None
            }
        else:
            raise HTTPException(status_code=404, detail=f"No real-time data available for {symbol}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching real-time data: {str(e)}")

@app.get("/api/company-info/{symbol}")
async def get_company_info(symbol: str):
    """Get detailed company information from Polygon.io"""
    try:
        polygon_info = analyzer.get_polygon_data(symbol, "1y")
        
        if polygon_info and 'results' in polygon_info:
            company_data = polygon_info['results']
            return {
                'symbol': symbol,
                'name': company_data.get('name', ''),
                'description': company_data.get('description', ''),
                'sector': company_data.get('sic_description', ''),
                'market_cap': company_data.get('market_cap', 0),
                'employees': company_data.get('total_employees', 0),
                'website': company_data.get('homepage_url', ''),
                'logo': company_data.get('branding', {}).get('logo_url', ''),
                'list_date': company_data.get('list_date', ''),
                'type': company_data.get('type', '')
            }
        else:
            # Fallback to Yahoo Finance
            stock = yf.Ticker(symbol)
            info = stock.info
            return {
                'symbol': symbol,
                'name': info.get('longName', symbol),
                'description': info.get('longBusinessSummary', ''),
                'sector': info.get('sector', ''),
                'market_cap': info.get('marketCap', 0),
                'employees': info.get('fullTimeEmployees', 0),
                'website': info.get('website', ''),
                'logo': '',
                'list_date': '',
                'type': 'stock'
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching company info: {str(e)}")

@app.get("/api/technical-analysis/{symbol}")
async def get_technical_analysis(symbol: str, period: str = "1y"):
    """Get comprehensive technical analysis for a symbol"""
    try:
        stock_data = analyzer.get_stock_data(symbol, period)
        
        if not stock_data or not stock_data.get('close'):
            raise HTTPException(status_code=404, detail=f"No data found for {symbol}")
        
        # Calculate additional technical metrics
        closes = stock_data['close']
        volumes = stock_data['volume']
        
        # Price momentum
        price_momentum = []
        for i in range(1, len(closes)):
            momentum = (closes[i] - closes[i-1]) / closes[i-1] * 100
            price_momentum.append(momentum)
        
        # Volume analysis
        avg_volume = np.mean(volumes) if volumes else 0
        current_volume = volumes[-1] if volumes else 0
        volume_ratio = current_volume / avg_volume if avg_volume > 0 else 1
        
        # Support and resistance levels
        recent_highs = max(closes[-20:]) if len(closes) >= 20 else max(closes)
        recent_lows = min(closes[-20:]) if len(closes) >= 20 else min(closes)
        
        # Trend analysis
        sma_20 = stock_data.get('sma_20', [])
        sma_50 = stock_data.get('sma_50', [])
        
        trend_direction = "neutral"
        if sma_20 and sma_50 and len(sma_20) > 0 and len(sma_50) > 0:
            if sma_20[-1] > sma_50[-1]:
                trend_direction = "bullish"
            elif sma_20[-1] < sma_50[-1]:
                trend_direction = "bearish"
        
        return {
            'symbol': symbol,
            'current_price': stock_data.get('current_price', 0),
            'price_momentum': price_momentum[-10:] if price_momentum else [],  # Last 10 days
            'volume_analysis': {
                'current_volume': current_volume,
                'average_volume': avg_volume,
                'volume_ratio': round(volume_ratio, 2)
            },
            'support_resistance': {
                'recent_high': recent_highs,
                'recent_low': recent_lows,
                'resistance_level': recent_highs * 1.02,  # 2% above recent high
                'support_level': recent_lows * 0.98  # 2% below recent low
            },
            'trend_analysis': {
                'direction': trend_direction,
                'sma_20': sma_20[-1] if sma_20 else 0,
                'sma_50': sma_50[-1] if sma_50 else 0
            },
            'rsi': stock_data.get('rsi', [])[-1] if stock_data.get('rsi') else 50,
            'volatility': stock_data.get('volatility', [])[-1] if stock_data.get('volatility') else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error in technical analysis: {str(e)}")

# Markowitz Portfolio Theory Functions
class MarkowitzPortfolio:
    def __init__(self, returns_data):
        """
        Initialize Markowitz Portfolio Theory calculations
        
        Args:
            returns_data: DataFrame with stock returns (columns = stocks, rows = time periods)
        """
        self.returns = returns_data
        self.n_assets = len(returns_data.columns)
        self.asset_names = returns_data.columns.tolist()
        
        # Calculate expected returns and covariance matrix
        self.expected_returns = returns_data.mean() * 252  # Annualized
        self.cov_matrix = returns_data.cov() * 252  # Annualized
        
    def portfolio_performance(self, weights):
        """
        Calculate portfolio expected return and volatility
        
        Args:
            weights: Portfolio weights (must sum to 1)
            
        Returns:
            tuple: (expected_return, volatility)
        """
        portfolio_return = np.sum(weights * self.expected_returns)
        portfolio_volatility = np.sqrt(np.dot(weights.T, np.dot(self.cov_matrix, weights)))
        return portfolio_return, portfolio_volatility
    
    def negative_sharpe_ratio(self, weights, risk_free_rate=0.02):
        """
        Calculate negative Sharpe ratio for optimization
        
        Args:
            weights: Portfolio weights
            risk_free_rate: Risk-free rate (default 2%)
            
        Returns:
            float: Negative Sharpe ratio
        """
        portfolio_return, portfolio_volatility = self.portfolio_performance(weights)
        sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
        return -sharpe_ratio
    
    def portfolio_variance(self, weights):
        """
        Calculate portfolio variance
        
        Args:
            weights: Portfolio weights
            
        Returns:
            float: Portfolio variance
        """
        return np.dot(weights.T, np.dot(self.cov_matrix, weights))
    
    def optimize_portfolio(self, target_return=None, risk_free_rate=0.02):
        """
        Optimize portfolio using Markowitz theory
        
        Args:
            target_return: Target return (if None, maximizes Sharpe ratio)
            risk_free_rate: Risk-free rate
            
        Returns:
            dict: Optimization results
        """
        # Constraints: weights sum to 1
        constraints = ({'type': 'eq', 'fun': lambda x: np.sum(x) - 1})
        
        # Bounds: weights between 0 and 1 (no short selling)
        bounds = tuple((0, 1) for _ in range(self.n_assets))
        
        # Initial guess: equal weights
        initial_weights = np.array([1/self.n_assets] * self.n_assets)
        
        if target_return is not None:
            # Minimize variance for given return
            constraints = [
                {'type': 'eq', 'fun': lambda x: np.sum(x) - 1},
                {'type': 'eq', 'fun': lambda x: np.sum(x * self.expected_returns) - target_return}
            ]
            result = minimize(self.portfolio_variance, initial_weights, 
                            method='SLSQP', bounds=bounds, constraints=constraints)
        else:
            # Maximize Sharpe ratio
            result = minimize(self.negative_sharpe_ratio, initial_weights,
                            method='SLSQP', bounds=bounds, constraints=constraints,
                            args=(risk_free_rate,))
        
        if result.success:
            optimal_weights = result.x
            portfolio_return, portfolio_volatility = self.portfolio_performance(optimal_weights)
            sharpe_ratio = (portfolio_return - risk_free_rate) / portfolio_volatility
            
            return {
                'weights': optimal_weights,
                'expected_return': portfolio_return,
                'volatility': portfolio_volatility,
                'sharpe_ratio': sharpe_ratio,
                'success': True
            }
        else:
            return {'success': False, 'message': result.message}
    
    def efficient_frontier(self, num_portfolios=100, risk_free_rate=0.02):
        """
        Generate efficient frontier
        
        Args:
            num_portfolios: Number of portfolios to generate
            risk_free_rate: Risk-free rate
            
        Returns:
            dict: Efficient frontier data
        """
        # Get min and max returns
        min_ret = self.expected_returns.min()
        max_ret = self.expected_returns.max()
        
        # Generate target returns
        target_returns = np.linspace(min_ret, max_ret, num_portfolios)
        
        # Calculate efficient frontier
        efficient_portfolios = []
        
        for target_return in target_returns:
            result = self.optimize_portfolio(target_return=target_return)
            if result['success']:
                efficient_portfolios.append({
                    'return': result['expected_return'],
                    'volatility': result['volatility'],
                    'sharpe_ratio': result['sharpe_ratio'],
                    'weights': result['weights']
                })
        
        # Find optimal portfolio (max Sharpe ratio)
        optimal_result = self.optimize_portfolio()
        if optimal_result['success']:
            optimal_portfolio = {
                'return': optimal_result['expected_return'],
                'volatility': optimal_result['volatility'],
                'sharpe_ratio': optimal_result['sharpe_ratio'],
                'weights': optimal_result['weights']
            }
        else:
            optimal_portfolio = None
        
        return {
            'efficient_frontier': efficient_portfolios,
            'optimal_portfolio': optimal_portfolio,
            'asset_names': self.asset_names
        }

@app.get("/api/markowitz/efficient-frontier")
async def get_efficient_frontier(symbols: str = "AAPL,GOOGL,MSFT,AMZN,TSLA", period: str = "1y"):
    """
    Generate efficient frontier for given stocks using Markowitz theory
    
    Args:
        symbols: Comma-separated stock symbols
        period: Time period for data
    
    Returns:
        dict: Efficient frontier data
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Get historical data for all stocks
        returns_data = {}
        
        for symbol in symbol_list:
            stock_data = analyzer.get_stock_data(symbol, period)
            if stock_data and stock_data.get('close'):
                prices = stock_data['close']
                # Calculate daily returns
                returns = pd.Series(prices).pct_change().dropna()
                returns_data[symbol] = returns
        
        if not returns_data:
            raise HTTPException(status_code=404, detail="No data found for any symbols")
        
        # Create DataFrame with aligned dates
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()  # Remove any rows with NaN
        
        if len(returns_df) < 30:  # Need sufficient data
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")
        
        # Initialize Markowitz portfolio
        markowitz = MarkowitzPortfolio(returns_df)
        
        # Generate efficient frontier
        frontier_data = markowitz.efficient_frontier()
        
        return {
            'symbols': symbol_list,
            'period': period,
            'data_points': len(returns_df),
            'efficient_frontier': frontier_data['efficient_frontier'],
            'optimal_portfolio': frontier_data['optimal_portfolio'],
            'asset_names': frontier_data['asset_names']
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating efficient frontier: {str(e)}")

@app.get("/api/markowitz/optimize-portfolio")
async def optimize_portfolio(symbols: str = "AAPL,GOOGL,MSFT,AMZN,TSLA", 
                           period: str = "1y", 
                           target_return: Optional[float] = None,
                           risk_free_rate: float = 0.02):
    """
    Optimize portfolio using Markowitz theory
    
    Args:
        symbols: Comma-separated stock symbols
        period: Time period for data
        target_return: Target return (if None, maximizes Sharpe ratio)
        risk_free_rate: Risk-free rate
        
    Returns:
        dict: Optimization results
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Get historical data for all stocks
        returns_data = {}
        
        for symbol in symbol_list:
            stock_data = analyzer.get_stock_data(symbol, period)
            if stock_data and stock_data.get('close'):
                prices = stock_data['close']
                # Calculate daily returns
                returns = pd.Series(prices).pct_change().dropna()
                returns_data[symbol] = returns
        
        if not returns_data:
            raise HTTPException(status_code=404, detail="No data found for any symbols")
        
        # Create DataFrame with aligned dates
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()
        
        if len(returns_df) < 30:
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")
        
        # Initialize Markowitz portfolio
        markowitz = MarkowitzPortfolio(returns_df)
        
        # Optimize portfolio
        result = markowitz.optimize_portfolio(target_return, risk_free_rate)
        
        if result['success']:
            # Format weights with asset names
            weights_dict = {}
            for i, asset in enumerate(markowitz.asset_names):
                weights_dict[asset] = float(result['weights'][i])
            
            return {
                'symbols': symbol_list,
                'period': period,
                'optimization_type': 'target_return' if target_return else 'max_sharpe',
                'target_return': target_return,
                'risk_free_rate': risk_free_rate,
                'weights': weights_dict,
                'expected_return': float(result['expected_return']),
                'volatility': float(result['volatility']),
                'sharpe_ratio': float(result['sharpe_ratio']),
                'success': True
            }
        else:
            return {
                'success': False,
                'message': result['message']
            }
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error optimizing portfolio: {str(e)}")

@app.get("/api/markowitz/correlation-matrix")
async def get_correlation_matrix(symbols: str = "AAPL,GOOGL,MSFT,AMZN,TSLA", period: str = "1y"):
    """
    Get correlation matrix for given stocks
    
    Args:
        symbols: Comma-separated stock symbols
        period: Time period for data
        
    Returns:
        dict: Correlation matrix data
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Get historical data for all stocks
        returns_data = {}
        
        for symbol in symbol_list:
            stock_data = analyzer.get_stock_data(symbol, period)
            if stock_data and stock_data.get('close'):
                prices = stock_data['close']
                # Calculate daily returns
                returns = pd.Series(prices).pct_change().dropna()
                returns_data[symbol] = returns
        
        if not returns_data:
            raise HTTPException(status_code=404, detail="No data found for any symbols")
        
        # Create DataFrame with aligned dates
        returns_df = pd.DataFrame(returns_data)
        returns_df = returns_df.dropna()
        
        if len(returns_df) < 30:
            raise HTTPException(status_code=400, detail="Insufficient data for analysis")
        
        # Calculate correlation matrix
        correlation_matrix = returns_df.corr()
        
        return {
            'symbols': symbol_list,
            'period': period,
            'correlation_matrix': correlation_matrix.to_dict(),
            'data_points': len(returns_df)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating correlation matrix: {str(e)}")

# Simple Hidden Markov Model implementation
class HiddenMarkovModel:
    def __init__(self, n_states=3):
        self.n_states = n_states
        self.transition_matrix = None
        self.means = None
        self.covars = None
        self.is_trained = False
        
    def train(self, returns_data):
        """Train a simple HMM model using K-means for state identification"""
        try:
            returns = np.array(returns_data)
            
            # Use K-means to identify states (simplified approach)
            from sklearn.cluster import KMeans
            kmeans = KMeans(n_clusters=self.n_states, random_state=42)
            states = kmeans.fit_predict(returns.reshape(-1, 1))
            
            # Calculate state statistics
            self.means = []
            self.covars = []
            
            for i in range(self.n_states):
                state_returns = returns[states == i]
                if len(state_returns) > 0:
                    self.means.append(np.mean(state_returns))
                    self.covars.append(np.var(state_returns))
                else:
                    self.means.append(0.0)
                    self.covars.append(1.0)
            
            self.means = np.array(self.means)
            self.covars = np.array(self.covars)
            
            # Calculate transition matrix
            self.transition_matrix = np.zeros((self.n_states, self.n_states))
            for i in range(len(states) - 1):
                self.transition_matrix[states[i], states[i+1]] += 1
            
            # Normalize transition matrix
            row_sums = self.transition_matrix.sum(axis=1)
            self.transition_matrix = self.transition_matrix / row_sums[:, np.newaxis]
            
            # Handle any NaN values
            self.transition_matrix = np.nan_to_num(self.transition_matrix)
            
            self.is_trained = True
            
            # Calculate log likelihood (simplified)
            log_likelihood = 0
            for i, state in enumerate(states):
                mean = self.means[state]
                var = self.covars[state]
                log_likelihood += -0.5 * np.log(2 * np.pi * var) - 0.5 * (returns[i] - mean)**2 / var
            
            return {
                'n_states': self.n_states,
                'converged': True,
                'log_likelihood': log_likelihood,
                'transition_matrix': self.transition_matrix.tolist(),
                'means': self.means.tolist(),
                'covars': self.covars.tolist()
            }
        except Exception as e:
            raise Exception(f"Error training HMM: {str(e)}")
    
    def predict_states(self, returns_data):
        """Predict hidden states for given returns"""
        if not self.is_trained:
            raise Exception("Model not trained yet")
        
        returns = np.array(returns_data)
        states = []
        
        for return_val in returns:
            # Find the state with the highest probability
            probabilities = []
            for i in range(self.n_states):
                mean = self.means[i]
                var = self.covars[i]
                prob = np.exp(-0.5 * (return_val - mean)**2 / var) / np.sqrt(2 * np.pi * var)
                probabilities.append(prob)
            
            best_state = np.argmax(probabilities)
            states.append(best_state)
        
        return states
    
    def predict_next_state(self, returns_data):
        """Predict the next state"""
        if not self.is_trained:
            raise Exception("Model not trained yet")
        
        # Get the last state - use available data, minimum 1 return
        min_returns = min(10, len(returns_data))
        if min_returns < 1:
            raise Exception("Insufficient data for state prediction")
        
        last_states = self.predict_states(returns_data[-min_returns:])
        last_state = last_states[-1]
        
        # Get transition probabilities from last state
        transition_probs = self.transition_matrix[last_state]
        
        # Predict next state (most likely)
        next_state = np.argmax(transition_probs)
        
        # Calculate state probabilities for the last return
        last_return = returns_data[-1]
        state_probs = []
        for i in range(self.n_states):
            mean = self.means[i]
            var = self.covars[i]
            prob = np.exp(-0.5 * (last_return - mean)**2 / var) / np.sqrt(2 * np.pi * var)
            state_probs.append(prob)
        
        # Normalize probabilities
        state_probs = np.array(state_probs)
        state_probs = state_probs / np.sum(state_probs)
        
        return {
            'current_state': int(last_state),
            'next_state': int(next_state),
            'transition_probabilities': transition_probs.tolist(),
            'state_probabilities': state_probs.tolist()
        }
    
    def generate_predictions(self, returns_data, n_days=30):
        """Generate future predictions based on HMM"""
        if not self.is_trained:
            raise Exception("Model not trained yet")
        
        if len(returns_data) < 1:
            raise Exception("Insufficient data for predictions")
        
        predictions = []
        current_returns = returns_data.copy()
        
        for _ in range(n_days):
            try:
                # Predict next state
                next_state_info = self.predict_next_state(current_returns)
                next_state = next_state_info['next_state']
                
                # Generate return based on state parameters
                mean_return = self.means[next_state]
                std_return = np.sqrt(self.covars[next_state])
                
                # Ensure std_return is positive
                if std_return <= 0:
                    std_return = 0.01  # Small positive value
                
                # Sample from normal distribution
                predicted_return = np.random.normal(mean_return, std_return)
                predictions.append(predicted_return)
                
                # Update current returns for next prediction
                current_returns = np.append(current_returns, predicted_return)
                
            except Exception as e:
                # If prediction fails, use a simple fallback
                last_return = current_returns[-1] if len(current_returns) > 0 else 0.0
                predicted_return = last_return * 0.99  # Slight decrease as fallback
                predictions.append(predicted_return)
                current_returns = np.append(current_returns, predicted_return)
        
        return predictions

# Initialize HMM
hmm_model = HiddenMarkovModel(n_states=3)

@app.get("/api/hmm/train")
async def train_hmm_model(symbols: str, period: str = "1y"):
    """
    Train Hidden Markov Model for given stocks
    
    Args:
        symbols: Comma-separated stock symbols
        period: Time period for data
        
    Returns:
        dict: HMM training results
    """
    try:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Get historical data for the first symbol (primary stock)
        primary_symbol = symbol_list[0]
        stock_data = analyzer.get_stock_data(primary_symbol, period)
        
        if not stock_data or not stock_data.get('close'):
            raise HTTPException(status_code=404, detail=f"No data found for {primary_symbol}")
        
        # Calculate returns
        prices = stock_data['close']
        returns = pd.Series(prices).pct_change().dropna().values
        
        if len(returns) < 50:
            raise HTTPException(status_code=400, detail="Insufficient data for HMM training")
        
        # Train HMM
        training_results = hmm_model.train(returns)
        
        # Get state probabilities for the data
        states = hmm_model.predict_states(returns)
        state_counts = pd.Series(states).value_counts().sort_index()
        state_probabilities = (state_counts / len(states)).to_dict()
        
        return {
            'symbols': symbol_list,
            'primary_symbol': primary_symbol,
            'period': period,
            'model_parameters': training_results,
            'state_probabilities': {str(k): float(v) for k, v in state_probabilities.items()},  # Convert to float for JSON serialization
            'data_points': int(len(returns))  # Convert to int for JSON serialization
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error training HMM: {str(e)}")

@app.get("/api/hmm/predict")
async def predict_with_hmm(symbols: str, period: str = "1y", n_days: int = 30):
    """
    Make predictions using trained HMM
    
    Args:
        symbols: Comma-separated stock symbols
        period: Time period for data
        n_days: Number of days to predict
        
    Returns:
        dict: HMM predictions
    """
    try:
        if not hmm_model.is_trained:
            # Auto-train the model if not trained
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            primary_symbol = symbol_list[0]
            stock_data = analyzer.get_stock_data(primary_symbol, period)
            
            if not stock_data or not stock_data.get('close'):
                raise HTTPException(status_code=404, detail=f"No data found for {primary_symbol}")
            
            # Calculate returns and train model
            prices = stock_data['close']
            returns = pd.Series(prices).pct_change().dropna().values
            
            if len(returns) < 50:
                raise HTTPException(status_code=400, detail="Insufficient data for HMM training")
            
            # Train the model
            hmm_model.train(returns)
        
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Get historical data for the first symbol
        primary_symbol = symbol_list[0]
        stock_data = analyzer.get_stock_data(primary_symbol, period)
        
        if not stock_data or not stock_data.get('close'):
            raise HTTPException(status_code=404, detail=f"No data found for {primary_symbol}")
        
        # Calculate returns
        prices = stock_data['close']
        returns = pd.Series(prices).pct_change().dropna().values
        
        # Generate predictions
        predictions = hmm_model.generate_predictions(returns, n_days)
        
        # Create dates for predictions
        try:
            last_date = pd.to_datetime(stock_data['date'][-1])
            prediction_dates = [last_date + timedelta(days=i+1) for i in range(n_days)]
            prediction_dates_str = [d.strftime('%Y-%m-%d') for d in prediction_dates]
        except Exception as e:
            # Fallback: use simple date generation
            from datetime import datetime
            today = datetime.now()
            prediction_dates_str = [(today + timedelta(days=i+1)).strftime('%Y-%m-%d') for i in range(n_days)]
        
        # Convert predictions to price predictions (starting from last price)
        try:
            last_price = float(prices[-1])
            price_predictions = []
            
            for pred_return in predictions:
                new_price = last_price * (1 + float(pred_return))
                price_predictions.append(new_price)
                last_price = new_price  # Update for next iteration
                
        except Exception as e:
            # Fallback: simple linear prediction
            last_price = float(prices[-1])
            price_predictions = [last_price * (1 + 0.001 * i) for i in range(1, n_days + 1)]
        
        return {
            'symbols': symbol_list,
            'primary_symbol': primary_symbol,
            'period': period,
            'predictions': {primary_symbol: [float(price) for price in price_predictions]},  # Convert to float for JSON serialization
            'dates': prediction_dates_str,
            'n_days': int(n_days)  # Convert to int for JSON serialization
        }
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"HMM Prediction Error: {str(e)}")
        print(f"Error Details: {error_details}")
        raise HTTPException(status_code=500, detail=f"Error making HMM predictions: {str(e)}")

@app.get("/api/hmm/state-transitions")
async def get_hmm_state_transitions(symbols: str, period: str = "1y"):
    """
    Get HMM state transition matrix and analysis
    
    Args:
        symbols: Comma-separated stock symbols
        period: Time period for data
        
    Returns:
        dict: State transition data
    """
    try:
        if not hmm_model.is_trained:
            # Auto-train the model if not trained
            symbol_list = [s.strip().upper() for s in symbols.split(',')]
            primary_symbol = symbol_list[0]
            stock_data = analyzer.get_stock_data(primary_symbol, period)
            
            if not stock_data or not stock_data.get('close'):
                raise HTTPException(status_code=404, detail=f"No data found for {primary_symbol}")
            
            # Calculate returns and train model
            prices = stock_data['close']
            returns = pd.Series(prices).pct_change().dropna().values
            
            if len(returns) < 50:
                raise HTTPException(status_code=400, detail="Insufficient data for HMM training")
            
            # Train the model
            hmm_model.train(returns)
        
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        
        # Get historical data for the first symbol
        primary_symbol = symbol_list[0]
        stock_data = analyzer.get_stock_data(primary_symbol, period)
        
        if not stock_data or not stock_data.get('close'):
            raise HTTPException(status_code=404, detail=f"No data found for {primary_symbol}")
        
        # Calculate returns and predict states
        prices = stock_data['close']
        returns = pd.Series(prices).pct_change().dropna().values
        states = hmm_model.predict_states(returns)
        
        # Get transition matrix
        transition_matrix = hmm_model.transition_matrix.tolist()
        
        # Get state means and covariances
        state_means = hmm_model.means.tolist()
        state_covars = hmm_model.covars.tolist()
        
        return {
            'symbols': symbol_list,
            'primary_symbol': primary_symbol,
            'period': period,
            'transition_matrix': transition_matrix,
            'states': [f"State {i}" for i in range(hmm_model.n_states)],
            'state_means': state_means,
            'state_covars': state_covars,
            'predicted_states': [int(state) for state in states[-50:]],  # Convert to int for JSON serialization
            'data_points': int(len(returns))  # Convert to int for JSON serialization
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting state transitions: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
