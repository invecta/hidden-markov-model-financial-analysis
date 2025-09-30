#!/usr/bin/env python3
"""
Test script for Financial Data Analyst APIs
This script tests the Alpaca and Polygon.io API integrations
"""

import os
import sys
from dotenv import load_dotenv
import alpaca_trade_api as tradeapi
import requests
import yfinance as yf

# Load environment variables
load_dotenv()

def test_alpaca_api():
    """Test Alpaca API connection and data retrieval"""
    print("🔍 Testing Alpaca API...")
    
    try:
        # Initialize Alpaca API
        api = tradeapi.REST(
            os.getenv('ALPACA_API_KEY'),
            os.getenv('ALPACA_SECRET_KEY'),
            os.getenv('ALPACA_BASE_URL'),
            api_version='v2'
        )
        
        # Test account info
        account = api.get_account()
        print(f"✅ Alpaca API connected successfully!")
        print(f"   Account Status: {account.status}")
        print(f"   Buying Power: ${float(account.buying_power):,.2f}")
        
        # Test getting latest bar for AAPL
        try:
            latest_bar = api.get_latest_bar('AAPL')
            if latest_bar:
                print(f"✅ Latest AAPL data: ${latest_bar.c} (Volume: {latest_bar.v:,})")
            else:
                print("⚠️  No latest bar data for AAPL")
        except Exception as e:
            print(f"⚠️  Could not get latest bar: {e}")
        
        # Test getting historical data
        try:
            bars = api.get_bars('AAPL', tradeapi.TimeFrame.Day, limit=5)
            if bars:
                print(f"✅ Historical data retrieved: {len(bars)} bars")
                print(f"   Latest close: ${bars[-1].c}")
            else:
                print("⚠️  No historical data retrieved")
        except Exception as e:
            print(f"⚠️  Could not get historical data: {e}")
            
        return True
        
    except Exception as e:
        print(f"❌ Alpaca API test failed: {e}")
        return False

def test_polygon_api():
    """Test Polygon.io API connection and data retrieval"""
    print("\n🔍 Testing Polygon.io API...")
    
    try:
        api_key = os.getenv('POLYGON_API_KEY')
        base_url = os.getenv('POLYGON_BASE_URL')
        
        if not api_key:
            print("❌ Polygon API key not found in environment variables")
            return False
        
        # Test company info endpoint
        url = f"{base_url}/v3/reference/tickers/AAPL"
        params = {'apikey': api_key}
        
        response = requests.get(url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if 'results' in data:
                company_info = data['results']
                print(f"✅ Polygon API connected successfully!")
                print(f"   Company: {company_info.get('name', 'N/A')}")
                print(f"   Market Cap: ${company_info.get('market_cap', 0):,}")
                print(f"   Employees: {company_info.get('total_employees', 'N/A'):,}")
            else:
                print("⚠️  No company data in response")
        else:
            print(f"❌ Polygon API request failed: {response.status_code}")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ Polygon API test failed: {e}")
        return False

def test_yahoo_finance():
    """Test Yahoo Finance as fallback"""
    print("\n🔍 Testing Yahoo Finance API...")
    
    try:
        stock = yf.Ticker("AAPL")
        info = stock.info
        hist = stock.history(period="5d")
        
        if not hist.empty:
            print(f"✅ Yahoo Finance API working!")
            print(f"   Company: {info.get('longName', 'N/A')}")
            print(f"   Current Price: ${hist['Close'].iloc[-1]:.2f}")
            print(f"   Volume: {hist['Volume'].iloc[-1]:,}")
            return True
        else:
            print("❌ No data from Yahoo Finance")
            return False
            
    except Exception as e:
        print(f"❌ Yahoo Finance test failed: {e}")
        return False

def test_environment_variables():
    """Test if all required environment variables are set"""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        'ALPACA_API_KEY',
        'ALPACA_SECRET_KEY', 
        'ALPACA_BASE_URL',
        'POLYGON_API_KEY',
        'POLYGON_BASE_URL'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Missing environment variables: {', '.join(missing_vars)}")
        return False
    else:
        print("✅ All environment variables are set")
        return True

def main():
    """Run all API tests"""
    print("🚀 Financial Data Analyst API Test Suite")
    print("=" * 50)
    
    # Test environment variables
    env_ok = test_environment_variables()
    
    if not env_ok:
        print("\n❌ Environment setup incomplete. Please check your .env file.")
        return
    
    # Test APIs
    alpaca_ok = test_alpaca_api()
    polygon_ok = test_polygon_api()
    yahoo_ok = test_yahoo_finance()
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print(f"   Alpaca API: {'✅ PASS' if alpaca_ok else '❌ FAIL'}")
    print(f"   Polygon API: {'✅ PASS' if polygon_ok else '❌ FAIL'}")
    print(f"   Yahoo Finance: {'✅ PASS' if yahoo_ok else '❌ FAIL'}")
    
    if alpaca_ok and (polygon_ok or yahoo_ok):
        print("\n🎉 All critical APIs are working! Your Financial Data Analyst is ready to deploy.")
    else:
        print("\n⚠️  Some APIs are not working. Check your API keys and network connection.")
    
    print("\n💡 Next steps:")
    print("   1. Run: python main.py")
    print("   2. Visit: http://localhost:8000")
    print("   3. Deploy to PythonAnywhere using deploy_instructions.md")

if __name__ == "__main__":
    main()



