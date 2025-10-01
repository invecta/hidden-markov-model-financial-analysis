# Financial Data Analyst Dashboard

A comprehensive financial data analysis platform built with Python FastAPI and modern web technologies. This project provides real-time stock analysis, portfolio management, and financial insights.

[![GitHub](https://img.shields.io/badge/GitHub-Repository-blue?style=for-the-badge&logo=github)](https://github.com/invecta/hidden-markov-model-financial-analysis)
[![Live Demo](https://img.shields.io/badge/Live%20Demo-PythonAnywhere-green?style=for-the-badge)](https://hindaouihani.pythonanywhere.com)
[![Python](https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com)

## Features

### 📊 Stock Analysis
- Real-time stock data from Yahoo Finance
- Technical indicators (SMA, RSI, Volatility)
- Interactive charts and visualizations
- Multiple time periods (1M, 3M, 6M, 1Y)

### 💼 Portfolio Management
- Multi-stock portfolio analysis
- Risk metrics calculation (Volatility, Sharpe Ratio)
- Portfolio performance visualization
- Equal-weight portfolio optimization

### 📈 Market Overview
- Real-time market data for top stocks
- Price changes and volume analysis
- Market trends and insights

## Technology Stack

### Backend
- **FastAPI**: Modern Python web framework
- **Pandas & NumPy**: Data manipulation and analysis
- **yfinance**: Yahoo Finance API integration
- **Plotly**: Advanced charting capabilities

### Frontend
- **HTML5 & CSS3**: Modern web standards
- **Tailwind CSS**: Utility-first CSS framework
- **Chart.js**: Interactive charts and graphs
- **Axios**: HTTP client for API calls

### Deployment
- **PythonAnywhere**: Cloud hosting platform
- **Static file serving**: Integrated frontend delivery

## Installation & Setup

### Local Development

1. **Clone the repository**
   ```bash
   git clone https://github.com/invecta/hidden-markov-model-financial-analysis.git
   cd hidden-markov-model-financial-analysis
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python main.py
   ```

5. **Access the dashboard**
   - Open your browser and go to `http://localhost:8000`
   - API documentation available at `http://localhost:8000/docs`

### PythonAnywhere Deployment

1. **Create PythonAnywhere account**
   - Go to [pythonanywhere.com](https://pythonanywhere.com)
   - Sign up for a free account

2. **Upload your code**
   - Use the Files tab to upload your project files
   - Or use Git to clone your repository

3. **Set up virtual environment**
   ```bash
   mkvirtualenv --python=/usr/bin/python3.10 financial-analyst
   pip install -r requirements.txt
   ```

4. **Configure Web App**
   - Go to Web tab in PythonAnywhere dashboard
   - Create a new web app
   - Choose "Manual configuration" and Python 3.10
   - Set the source code path to your project directory

5. **Update WSGI configuration**
   - Edit the WSGI file to point to your FastAPI application
   - Add the following code:
   ```python
   import sys
   path = '/home/yourusername/financial-analyst-project'
   if path not in sys.path:
       sys.path.append(path)
   
   from main import app
   application = app
   ```

6. **Reload the web app**
   - Click the "Reload" button in the Web tab

## API Endpoints

### Stock Data
- `GET /api/stocks` - Get supported stock symbols
- `GET /api/stock/{symbol}` - Get stock data and analysis
- `GET /api/market-overview` - Get market overview

### Portfolio Analysis
- `POST /api/portfolio` - Analyze portfolio performance

### Parameters
- `symbol`: Stock ticker symbol (e.g., AAPL, GOOGL)
- `period`: Time period (1y, 6mo, 3mo, 1mo)
- `symbols`: Array of stock symbols for portfolio
- `weights`: Array of portfolio weights (optional)

## Usage Examples

### Analyze a Single Stock
```bash
curl "http://localhost:8000/api/stock/AAPL?period=1y"
```

### Portfolio Analysis
```bash
curl -X POST "http://localhost:8000/api/portfolio" \
     -H "Content-Type: application/json" \
     -d '{"symbols": ["AAPL", "GOOGL", "MSFT"]}'
```

### Market Overview
```bash
curl "http://localhost:8000/api/market-overview"
```

## Project Structure

```
financial-analyst-project/
├── main.py                 # FastAPI application
├── requirements.txt        # Python dependencies
├── wsgi.py                # WSGI configuration for deployment
├── static/
│   └── index.html         # Frontend dashboard
├── README.md              # Project documentation
└── deploy_instructions.md # Deployment guide
```

## Key Features Explained

### Technical Indicators
- **SMA (Simple Moving Average)**: 20-day and 50-day moving averages
- **RSI (Relative Strength Index)**: Momentum oscillator (0-100)
- **Volatility**: Annualized standard deviation of returns

### Portfolio Metrics
- **Expected Return**: Weighted average of individual stock returns
- **Portfolio Volatility**: Risk measure based on return variance
- **Sharpe Ratio**: Risk-adjusted return metric

### Data Sources
- **Yahoo Finance**: Free financial data API
- **Real-time data**: Live stock prices and market data
- **Historical data**: Up to 1 year of historical data

## Customization

### Adding New Stocks
Edit the `supported_stocks` list in `main.py`:
```python
self.supported_stocks = [
    "AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", 
    "META", "NVDA", "NFLX", "AMD", "INTC",
    "YOUR_NEW_STOCK"  # Add here
]
```

### Adding New Indicators
Extend the `FinancialAnalyzer` class in `main.py`:
```python
def calculate_new_indicator(self, prices):
    # Your custom indicator calculation
    return indicator_values
```

### Styling Changes
Modify the CSS in `static/index.html` or add custom stylesheets.

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Check Python version compatibility (3.8+)

2. **Data Fetching Issues**
   - Verify internet connection
   - Check if Yahoo Finance API is accessible
   - Some stocks may have limited data availability

3. **Chart Display Problems**
   - Ensure Chart.js is loaded correctly
   - Check browser console for JavaScript errors
   - Verify data format matches chart expectations

4. **PythonAnywhere Deployment**
   - Check WSGI configuration
   - Verify file paths are correct
   - Ensure virtual environment is activated

### Performance Optimization

1. **Data Caching**
   - Implement Redis for data caching
   - Cache frequently accessed stock data
   - Set appropriate cache expiration times

2. **Database Integration**
   - Add SQLite/PostgreSQL for data persistence
   - Store historical data locally
   - Implement data update schedules

3. **API Rate Limiting**
   - Implement request rate limiting
   - Add API key authentication
   - Monitor API usage and costs

## Future Enhancements

### Planned Features
- [ ] User authentication and portfolios
- [ ] Advanced technical indicators
- [ ] Options and derivatives analysis
- [ ] News sentiment analysis
- [ ] Mobile-responsive design
- [ ] Real-time notifications
- [ ] Export functionality (PDF, Excel)
- [ ] Backtesting capabilities
- [ ] Machine learning predictions

### Technical Improvements
- [ ] Database integration
- [ ] Caching layer
- [ ] API rate limiting
- [ ] Error handling improvements
- [ ] Unit tests
- [ ] CI/CD pipeline
- [ ] Docker containerization
- [ ] Monitoring and logging

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is open source and available under the MIT License.

## Support

For questions, issues, or contributions:
- Create an issue in the [GitHub repository](https://github.com/invecta/hidden-markov-model-financial-analysis/issues)
- Contact the development team
- Check the documentation and examples

## Repository Links

- **GitHub Repository**: [https://github.com/invecta/hidden-markov-model-financial-analysis](https://github.com/invecta/hidden-markov-model-financial-analysis)
- **Live Demo**: [https://hindaouihani.pythonanywhere.com](https://hindaouihani.pythonanywhere.com)
- **Documentation**: Available in the `/static/documentation.html` file

## Acknowledgments

- Yahoo Finance for providing free financial data
- FastAPI team for the excellent web framework
- Chart.js for interactive charting capabilities
- PythonAnywhere for cloud hosting platform

---

**Happy Analyzing! 📊💹**



