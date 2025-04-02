import requests
import plotly.express as px


API_KEY =  'YOUR_ALPHA_VANTAGE_API_KEY'
BASE_URL = "https://www.alphavantage.co/query"

def get_stock_data(symbol):
    """
    Retrieve stock data including closing prices and stock details from Alpha Vantage.

    Args:
    - symbol (str): The stock symbol (e.g., AAPL for Apple Inc.).

    Returns:
    - dict: A dictionary containing stock prices and relevant details.
    """
    stock_data = {}

    # Retrieve closing stock prices
    stock_prices = get_closing_stock_prices(symbol, API_KEY)
    if stock_prices:
        stock_data['closing_prices'] = stock_prices

    # Retrieve additional stock info (e.g., sector, market cap, etc.)
    overview_data = get_stock_overview(symbol, API_KEY)
    if overview_data:
        stock_data.update(overview_data)
        
    plot_close = plot_closing_prices(stock_data['closing_prices'])
    return stock_data, plot_close

def get_latest_close_price(symbol, api_key):
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if 'Time Series (Daily)' in data:
            closing_prices = {}
            for date, values in data['Time Series (Daily)'].items():
                if len(closing_prices) == 90:
                    break
                closing_prices[date] = values['4. close']
                latest_dt = max(list(closing_prices.keys()))
            return closing_prices[latest_dt]
        else:
            print("Error: Could not fetch data. Check your symbol or API key.")
            return None

    except requests.exceptions.RequestException as e:
        print("Error fetching data:", e)
        return None

def get_closing_stock_prices(symbol, api_key):
    """
    Retrieve stock prices for a given symbol from Alpha Vantage.

    Args:
    - symbol (str): The stock symbol (e.g., AAPL for Apple Inc.).
    - api_key (str): Your Alpha Vantage API key.

    Returns:
    - dict: A dictionary containing stock prices.
    """
    params = {
        "function": "TIME_SERIES_DAILY",
        "symbol": symbol,
        "apikey": api_key
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()

        if 'Time Series (Daily)' in data:
            closing_prices = {}
            for date, values in data['Time Series (Daily)'].items():
                if len(closing_prices) == 90:
                    break
                closing_prices[date] = values['4. close']
            return closing_prices
        else:
            print("Error: Could not fetch data. Check your symbol or API key.")
            return None

    except requests.exceptions.RequestException as e:
        print("Error fetching data:", e)
        return None


def get_stock_overview(symbol, api_key):
    """
    Retrieve company overview information from Alpha Vantage.

    Args:
    - symbol (str): The stock symbol (e.g., AAPL for Apple Inc.).
    - api_key (str): Your Alpha Vantage API key.

    Returns:
    - dict: A dictionary containing stock overview information.
    """
    params = {
        "function": "OVERVIEW",
        "symbol": symbol,
        "apikey": api_key
    }

    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        
        time_series_params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': API_KEY
        }
        time_series_response = requests.get(BASE_URL, params=time_series_params)
        time_series_data = time_series_response.json()
        daily_data = time_series_data["Time Series (Daily)"]
        dates = list(daily_data.keys())[:365]  # Get the past year data
        close_prices = [float(daily_data[date]['4. close']) for date in dates]

        if 'Name' in data:
            overview = {
                "symbol": symbol,
                "company_name": data.get('Name', 'N/A'),
                "sector": data.get('Sector', 'N/A'),
                "industry": data.get('Industry', 'N/A'),
                "market_cap": data.get('MarketCapitalization', 'N/A'),
                "pe_ratio": data.get('PERatio', 'N/A'),
                "eps": data.get('EPS', 'N/A'),
                "dividend": data.get('DividendYield', 'N/A'),
                "exchange": data.get('Exchange', 'N/A'),
                "current_price": daily_data[dates[0]]['4. close'],
                "previous_close": daily_data[dates[1]]['4. close'],
                "open": daily_data[dates[0]]['1. open'],
                "volumn": daily_data[dates[0]]['5. volume'],
                "52_week_high": max(close_prices),
                "52_week_low": min(close_prices)
            }
            return overview
        else:
            print("Error: Could not fetch stock overview.")
            return None

    except requests.exceptions.RequestException as e:
        print("Error fetching data:", e)
        return None

def plot_closing_prices(closing_prices):
    """
    Generate a plot of the closing prices for the past year.
    
    Args:
    - closing_prices (dict): A dictionary of dates and closing prices.
    
    Returns:
    - str: A base64 encoded image URL.
    """
    dates = list(closing_prices.keys())
    prices = [float(closing_prices[date]) for date in dates]

    # Plot the closing prices for the past year
    fig = px.line(x = dates, y = prices)

    return fig

