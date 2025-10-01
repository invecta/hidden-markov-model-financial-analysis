from flask import Flask, render_template_string, request, jsonify
import json
from datetime import datetime, timedelta
import random

app = Flask(__name__)

# Supported stocks
SUPPORTED_STOCKS = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA"]

# Mock stock prices
MOCK_PRICES = {
    "AAPL": 175.50,
    "GOOGL": 142.30,
    "MSFT": 378.85,
    "AMZN": 155.20,
    "TSLA": 248.75,
    "META": 485.60,
    "NVDA": 875.40
}

def generate_simple_data(symbol, period="1y"):
    """Generate simple mock stock data"""
    try:
        base_price = MOCK_PRICES.get(symbol, 100.0)
        
        # Generate 30 data points
        dates = []
        prices = []
        
        for i in range(30):
            date = datetime.now() - timedelta(days=30-i)
            dates.append(date.strftime('%Y-%m-%d'))
            
            # Simple price movement
            change = random.uniform(-0.02, 0.02)
            base_price *= (1 + change)
            prices.append(round(base_price, 2))
        
        return {
            'dates': dates,
            'prices': prices,
            'current_price': prices[-1],
            'rsi': random.uniform(30, 70),
            'volatility': random.uniform(0.15, 0.35)
        }
        
    except Exception as e:
        print(f"Error generating data for {symbol}: {e}")
        return None

@app.route('/')
def home():
    return render_template_string('''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Financial Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .chart-container { position: relative; height: 400px; width: 100%; }
        .loading { display: inline-block; width: 20px; height: 20px; border: 3px solid #f3f3f3; border-top: 3px solid #3498db; border-radius: 50%; animation: spin 1s linear infinite; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold text-center mb-8 text-gray-800">Financial Analysis Dashboard</h1>
        
        <!-- Stock Selection -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 class="text-xl font-semibold mb-4">Stock Analysis</h2>
            <div class="flex flex-wrap gap-4">
                <select id="stockSelect" class="border rounded px-3 py-2">
                    <option value="">Select a stock...</option>
                    {% for stock in stocks %}
                    <option value="{{ stock }}">{{ stock }}</option>
                    {% endfor %}
                </select>
                <button onclick="analyzeStock()" class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600">
                    Analyze
                </button>
            </div>
        </div>

        <!-- Stock Information -->
        <div id="stockInfo" class="bg-white rounded-lg shadow-md p-6 mb-6" style="display: none;">
            <h2 class="text-xl font-semibold mb-4">Stock Information</h2>
            <div id="stockDetails" class="grid grid-cols-2 md:grid-cols-4 gap-4"></div>
        </div>

        <!-- Chart -->
        <div class="bg-white rounded-lg shadow-md p-6 mb-6">
            <h3 class="text-lg font-semibold mb-4">Price Chart</h3>
            <div class="chart-container">
                <canvas id="priceChart"></canvas>
            </div>
        </div>

        <!-- Market Overview -->
        <div class="bg-white rounded-lg shadow-md p-6">
            <h2 class="text-xl font-semibold mb-4">Market Overview</h2>
            <div id="marketOverview" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                <div class="loading"></div>
            </div>
        </div>
    </div>

    <script>
        let priceChart;

        function analyzeStock() {
            const symbol = document.getElementById('stockSelect').value;
            
            if (!symbol) {
                alert('Please select a stock');
                return;
            }

            // Show loading
            document.getElementById('stockInfo').style.display = 'block';
            document.getElementById('stockDetails').innerHTML = '<div class="loading"></div>';

            // Fetch stock data
            fetch(`/api/stock/${symbol}`)
                .then(response => response.json())
                .then(data => {
                    if (data.error) {
                        alert(data.error);
                        return;
                    }
                    displayStockInfo(data);
                    updateChart(data);
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('Error fetching stock data');
                });
        }

        function displayStockInfo(data) {
            const details = document.getElementById('stockDetails');
            
            details.innerHTML = `
                <div class="text-center">
                    <div class="text-2xl font-bold text-gray-800">$${data.current_price.toFixed(2)}</div>
                    <div class="text-sm text-gray-600">Current Price</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-semibold text-gray-800">${data.rsi.toFixed(1)}</div>
                    <div class="text-sm text-gray-600">RSI</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-semibold text-gray-800">${(data.volatility * 100).toFixed(1)}%</div>
                    <div class="text-sm text-gray-600">Volatility</div>
                </div>
                <div class="text-center">
                    <div class="text-lg font-semibold text-gray-800">${data.prices.length}</div>
                    <div class="text-sm text-gray-600">Data Points</div>
                </div>
            `;
        }

        function updateChart(data) {
            // Price Chart
            if (priceChart) priceChart.destroy();
            const priceCtx = document.getElementById('priceChart').getContext('2d');
            priceChart = new Chart(priceCtx, {
                type: 'line',
                data: {
                    labels: data.dates,
                    datasets: [
                        {
                            label: 'Close Price',
                            data: data.prices,
                            borderColor: 'rgb(59, 130, 246)',
                            backgroundColor: 'rgba(59, 130, 246, 0.1)',
                            tension: 0.1
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: false
                        }
                    }
                }
            });
        }

        // Load market overview on page load
        window.onload = function() {
            fetch('/api/market-overview')
                .then(response => response.json())
                .then(data => {
                    const overview = document.getElementById('marketOverview');
                    overview.innerHTML = data.stocks.map(stock => `
                        <div class="bg-gray-50 rounded-lg p-4">
                            <div class="flex justify-between items-center">
                                <div>
                                    <div class="font-semibold">${stock.symbol}</div>
                                    <div class="text-sm text-gray-600">$${stock.price.toFixed(2)}</div>
                                </div>
                                <div class="text-right">
                                    <div class="text-sm ${stock.change >= 0 ? 'text-green-600' : 'text-red-600'}">
                                        ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}%
                                    </div>
                                </div>
                            </div>
                        </div>
                    `).join('');
                })
                .catch(error => {
                    console.error('Error loading market overview:', error);
                    document.getElementById('marketOverview').innerHTML = '<div class="text-red-600">Error loading market data</div>';
                });
        };
    </script>
</body>
</html>
    ''', stocks=SUPPORTED_STOCKS)

@app.route('/api/stock/<symbol>')
def get_stock_data_api(symbol):
    """API endpoint to get stock data"""
    try:
        data = generate_simple_data(symbol)
        if data is None:
            return jsonify({'error': f'No data found for {symbol}'})
        
        return jsonify(data)
        
    except Exception as e:
        print(f"API Error for {symbol}: {e}")
        return jsonify({'error': str(e)})

@app.route('/api/market-overview')
def market_overview():
    """Get market overview for top stocks"""
    try:
        stocks = []
        for symbol in SUPPORTED_STOCKS:
            try:
                base_price = MOCK_PRICES.get(symbol, 100.0)
                change = random.uniform(-5, 5)
                current_price = base_price * (1 + change/100)
                
                stocks.append({
                    'symbol': symbol,
                    'price': float(current_price),
                    'change': float(change)
                })
            except Exception as e:
                print(f"Error generating {symbol}: {e}")
                continue
        
        return jsonify({'stocks': stocks})
        
    except Exception as e:
        print(f"Market overview error: {e}")
        return jsonify({'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
