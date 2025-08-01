import streamlit as st
import yfinance as yf
import pandas as pd
import datetime
import requests
import xml.etree.ElementTree as ET

FINNHUB_API_KEY = 'd269jc1r01qh25lmfuh0d269jc1r01qh25lmfuhg'  # <-- Replace with your actual key

def get_news_finnhub(ticker):
    url = f"https://finnhub.io/api/v1/company-news?symbol={ticker}&from=2024-07-01&to=2024-07-31&token={FINNHUB_API_KEY}"
    try:
        r = requests.get(url)
        data = r.json()
        # Only return if Finnhub actually returns news (list of dicts)
        if isinstance(data, list) and len(data) > 0:
            news = []
            for article in data[:2]:
                news.append({
                    'headline': article.get('headline', 'No headline'),
                    'url': article.get('url', '#')
                })
            return news
        else:
            # Finnhub denied access, or no news, or wrong format
            return []
    except Exception as e:
        return []

def get_news_yahoo(ticker):
    url = f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={ticker}&region=US&lang=en-US"
    try:
        r = requests.get(url)
        tree = ET.fromstring(r.content)
        items = tree.findall('.//item')
        news = []
        for item in items[:2]:
            title = item.find('title').text
            link = item.find('link').text
            news.append({'headline': title, 'url': link})
        return news
    except Exception as e:
        return []
        
st.set_page_config(page_title="My Portfolio Dashboard", layout="wide")

st.title("📈 My Stock Portfolio Dashboard")

# --- Portfolio Upload or Input ---
st.sidebar.header("1. Upload Your Portfolio")
portfolio_file = st.sidebar.file_uploader("Choose a CSV file", type="csv")
if portfolio_file:
    df = pd.read_csv(portfolio_file)
    df.columns = df.columns.str.strip()  # Always clean column headers
else:
    st.sidebar.info("Upload a CSV to begin. See the sample in instructions.")
    df = pd.DataFrame(columns=["Ticker", "Name", "Market", "Buy Price", "Shares"])

if not df.empty:
    tickers = df['Ticker'].tolist()
    st.write("## Your Holdings")
    st.dataframe(df)

    # --- Price Fetch ---
    st.write("## Latest Prices")
    prices = {}
    last_close_dates = {}
    for ticker in df['Ticker']:
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period='5d')
            # Use the most recent available closing price
            if not hist.empty:
                last_close = hist['Close'][-1]
                last_date = hist.index[-1].strftime('%Y-%m-%d')
            else:
                last_close = None
                last_date = None
        except Exception as e:
            last_close = None
            last_date = None
        prices[ticker] = last_close
        last_close_dates[ticker] = last_date

    df['Latest Price'] = df['Ticker'].map(prices)
    df['Last Close Date'] = df['Ticker'].map(last_close_dates)
    st.dataframe(df)

    # --- Simple Alerts (per session for demo) ---
    st.write("## Price Alerts")
    for idx, row in df.iterrows():
        alert_price = st.number_input(
            f"Alert if {row['Ticker']} drops below:",
            value=float(row['Buy Price']),
            key=row['Ticker']
        )
        if prices[row['Ticker']] is not None and prices[row['Ticker']] < alert_price:
            st.warning(f"🚨 Alert: {row['Ticker']} dropped below {alert_price}! (Current: {prices[row['Ticker']]})")

    # --- News Feed (using Finnhub, fallback Yahoo demo) ---
    for ticker in df['Ticker']:
        st.markdown(f"### {ticker}")
    # Try Finnhub first
        articles = get_news_finnhub(ticker)
    # Fallback to Yahoo if Finnhub failed
        if not articles:
            articles = get_news_yahoo(ticker)
        if articles:
            for article in articles:
                st.markdown(f"- [{article['headline']}]({article['url']})")
        else:
            st.info("No recent news found.")
else:
    st.info("Upload a CSV to get started.")

st.sidebar.markdown("---")
st.sidebar.write("Developed with ❤️ using Streamlit.")