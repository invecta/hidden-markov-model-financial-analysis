from flask import Flask, render_template_string, jsonify
import requests
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# Your API keys
ALPACA_API_KEY = "PK1XLYB4JCL3D16LMTPM"
ALPACA_SECRET_KEY = "kHL621Q6u0UehLTX0bMNznKIRx4L2GUG73OhVSdL"
ALPACA_BASE_URL = "https://paper-api.alpaca.markets/v2"
POLYGON_API_KEY = "SWbaiH7zZIQRj04sFUfWzVLXT4VeKCkP"

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Financial Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .container { max-width: 800px; margin: 0 auto; }
            .stock-card { border: 1px solid #ddd; padding: 20px; margin: 10px 0; border-radius: 5px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>Financial Dashboard</h1>
            <div class="stock-card">
                <h2>Stock Analysis</h2>
                <p>Your Hidden Markov Model Financial Analysis is now running!</p>
                <p>API Endpoints:</p>
                <ul>
                    <li><a href="/api/stock/AAPL">AAPL Stock Data</a></li>
                    <li><a href="/api/stock/GOOGL">GOOGL Stock Data</a></li>
                    <li><a href="/api/stock/MSFT">MSFT Stock Data</a></li>
                    <li><a href="/api/stock/TSLA">TSLA Stock Data</a></li>
                    <li><a href="/api/stock/AMZN">AMZN Stock Data</a></li>
                </ul>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/api/stock/<symbol>')
def get_stock(symbol):
    try:
        # Try Alpaca API first
        headers = {
            'APCA-API-KEY-ID': ALPACA_API_KEY,
            'APCA-API-SECRET-KEY': ALPACA_SECRET_KEY
        }
        
        # Get latest quote from Alpaca
        quote_url = f"{ALPACA_BASE_URL}/stocks/{symbol}/quotes/latest"
        response = requests.get(quote_url, headers=headers)
        
        if response.status_code == 200:
            quote_data = response.json()
            quote = quote_data.get('quote', {})
            
            data = {
                'symbol': symbol,
                'current_price': quote.get('ap', 0),
                'bid': quote.get('bp', 0),
                'ask': quote.get('ap', 0),
                'volume': quote.get('v', 0),
                'timestamp': quote.get('t', ''),
                'source': 'Alpaca'
            }
            return jsonify(data)
        
        # If Alpaca fails, try Polygon.io
        polygon_url = f"https://api.polygon.io/v2/aggs/ticker/{symbol}/prev?apikey={POLYGON_API_KEY}"
        response = requests.get(polygon_url)
        
        if response.status_code == 200:
            polygon_data = response.json()
            if polygon_data.get('results'):
                result = polygon_data['results'][0]
                
                data = {
                    'symbol': symbol,
                    'current_price': result.get('c', 0),
                    'open': result.get('o', 0),
                    'high': result.get('h', 0),
                    'low': result.get('l', 0),
                    'volume': result.get('v', 0),
                    'timestamp': result.get('t', ''),
                    'source': 'Polygon.io'
                }
                return jsonify(data)
        
        return jsonify({'error': f'No data available for {symbol} from both APIs'}), 404
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
