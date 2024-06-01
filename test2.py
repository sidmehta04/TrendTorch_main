import time
import datetime
import pandas as pd
import matplotlib.pyplot as plt
import os
import requests
from bs4 import BeautifulSoup
import yfinance as yf
from yahoo_fin import stock_info as si
import talib

# Define functions for each strategy

def download_stock_data(ticker, interval):
    period1 = int(time.mktime(datetime.date(2010, 12, 1).timetuple()))
    period2 = int(time.mktime(datetime.date.today().timetuple()))
    query_string = f'https://query1.finance.yahoo.com/v7/finance/download/{ticker}?period1={period1}&period2={period2}&interval={interval}&events-history&includeAdjustedClose=true'
    df = pd.read_csv(query_string)
    return df

def golden_cross_strategy(df):
    # Calculate 8-day and 34-day moving averages
    df['MA8'] = df['Close'].rolling(window=8).mean()
    df['MA34'] = df['Close'].rolling(window=34).mean()

    # Generate signals
    df['Signal'] = 0  # 0 represents no signal
    df.loc[df['MA8'] > df['MA34'], 'Signal'] = 1  # 1 represents buy signal
    df.loc[df['MA8'] < df['MA34'], 'Signal'] = -1  # -1 represents sell signal

    # Identify buying prices
    buy_signals = df[(df['Signal'] == 1) & (df['Signal'].shift(1) == -1)]
    buying_prices = buy_signals['Close']

    # Exclude buying signals that are too close to the end of the data
    if len(buying_prices) > 0:
        last_buy_signal_index = buying_prices.index[-1]
        last_possible_sell_index = df.index[-1]
        if last_possible_sell_index - last_buy_signal_index < 3:
            buying_prices = buying_prices[:-1]

    # Calculate selling prices (3:1 ratio)
    selling_prices = buying_prices * 1.03  # Assuming a 3% profit target

    return buying_prices, selling_prices


def rsi_strategy(df, window=14, upper_band=70, lower_band=30):
    rsi = talib.RSI(df['Close'], timeperiod=window)
    buy_signal = df[(rsi < lower_band)]
    sell_signal = df[(rsi > upper_band)]
    return buy_signal, sell_signal

def macd_strategy(df):
    macd, signal, _ = talib.MACD(df['Close'])
    buy_signal = df[(macd > signal) & (macd.shift(1) < signal.shift(1))]
    sell_signal = df[(macd < signal) & (macd.shift(1) > signal.shift(1))]
    return buy_signal, sell_signal

def download_and_save(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end)
        csv_file_path = f'stock_data/{ticker}.csv'
        df.to_csv(csv_file_path)
        return df, csv_file_path
    except Exception as e:
        print(f"Error downloading data for {ticker}: {e}")
        return None, None

def get_and_print_pe_ratios(stock_symbols):
    for symbol in stock_symbols:
        stock_data = get_stock_data(symbol)
        if stock_data:
            print(f"Stock: {stock_data['symbol']}")
            pe_ratio = print_pe_ratio(stock_data)
            print("-" * 40)
            if pe_ratio is not None and pe_ratio > 22.6:
                print(f"P/E Ratio for {stock_data['symbol']} is greater than industry.")
                return True
            else:
                print(f"P/E Ratio for {stock_data['symbol']} is not available or less than industry.")
                return False

def print_pe_ratio(stock_data):
    if 'PE Ratio (TTM)' in stock_data:
        pe_ratio = float(stock_data['PE Ratio (TTM)'].replace(",", ""))
        print(f"P/E Ratio for {stock_data['symbol']}: {pe_ratio}")
        return pe_ratio
    else:
        print(f"P/E Ratio not available for {stock_data['symbol']}.")
        return None

def get_stock_data(stock_symbol):
    url = f"https://finance.yahoo.com/quote/{stock_symbol}?p={stock_symbol}&.tsrc=fin-srch"
    response = requests.get(url)

    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'html.parser')
        quote_summary = soup.find('div', {'id': 'quote-summary'})

        if quote_summary:
            stock_data = {'symbol': stock_symbol}
            for row in quote_summary.find_all('tr'):
                columns = row.find_all(['td', 'th'])
                if len(columns) == 2:
                    key = columns[0].get_text(strip=True)
                    value = columns[1].get_text(strip=True)
                    stock_data[key] = value
            return stock_data
        else:
            print(f"ID 'quote-summary' not found for stock {stock_symbol}.")
    else:
        print(f"Failed to retrieve data for stock {stock_symbol}. Status code: {response.status_code}")

# Define functions to run each strategy

def run_golden_cross_strategy():
    tickers_nifty50 = si.tickers_nifty50()
    nifty500_symbol = '^NSEI'  # Nifty 500 index symbol

    start = datetime.datetime.now() - datetime.timedelta(days=1825)
    end = datetime.datetime.now()

    os.makedirs('stock_data', exist_ok=True)

    nifty500_df, nifty500_csv_path = download_and_save(nifty500_symbol, start, end)

    if nifty500_df is not None:
        nifty500_df['Pct Change'] = nifty500_df['Adj Close'].pct_change()
        sp500_return = (nifty500_df['Pct Change'] + 1).cumprod()[-1]

        data_list = []

        for ticker in tickers_nifty50:
            stock_df, stock_csv_path = download_and_save(ticker, start, end)

            if stock_df is not None and 'Adj Close' in stock_df.columns:
                try:
                    stock_df['Pct Change'] = stock_df['Adj Close'].pct_change()
                    stock_return = (stock_df['Pct Change'] + 1).cumprod()[-1]
                    returns_compared = round((stock_return / sp500_return), 2)

                    moving_averages = [150, 200]
                    for ma in moving_averages:
                        stock_df[f'SMA_{ma}'] = round(stock_df['Adj Close'].rolling(window=ma).mean(), 2)

                    latest_price = stock_df['Adj Close'].iloc[-1]
                    moving_average_150 = stock_df['SMA_150'].iloc[-1]
                    moving_average_200 = stock_df['SMA_200'].iloc[-1]
                    low_52week = round(min(stock_df['Low'].iloc[-(52 * 5):]), 2)
                    high_52week = round(max(stock_df['High'].iloc[-(52 * 5):]), 2)
                    score = round(returns_compared * 100)

                    # Adjusted conditions
                    condition_1 = latest_price > moving_average_150 > moving_average_200
                    condition_2 = latest_price >= (1.3 * low_52week)
                    condition_3 = latest_price >= (0.75 * high_52week)
                    condition_4 = get_and_print_pe_ratios([ticker])  # This line is adjusted
                    condition_5 = True  # Just a placeholder for now, you can add your condition here

                    if condition_1 and condition_2 and condition_3 and condition_4 and condition_5:
                        weekly_data = download_stock_data(ticker, "1wk")
                        buying_prices, selling_prices = golden_cross_strategy(weekly_data)

                        print(f"\nBuying Prices for {ticker} - Weekly Data:")
                        print(buying_prices)
                        print(f"\nSelling Prices for {ticker} - Weekly Data:")
                        print(selling_prices)

                        plt.figure(figsize=(10, 6))
                        plt.plot(weekly_data['Date'], weekly_data['Close'], label='Close Price')
                        plt.plot(weekly_data['Date'], weekly_data['MA8'], label='8-day MA')
                        plt.plot(weekly_data['Date'], weekly_data['MA34'], label='34-day MA')
                        plt.scatter(buying_prices.index, buying_prices, marker='^', color='g', label='Buy Signal')
                        if not selling_prices.empty:
                            plt.scatter(selling_prices.index, selling_prices, marker='v', color='r', label='Sell Signal')
                        plt.title(f'Golden Cross Strategy - {ticker} - Weekly Data')
                        plt.xlabel('Date')
                        plt.ylabel('Price')
                        plt.legend()
                        plt.show()

                    data_list.append({
                        'Ticker': ticker,
                        'Latest_Price': latest_price,
                        'Score': score,
                        'Moving_avg_150': moving_average_150,
                        'Moving_avg_200': moving_average_200,
                        'Buy_Signal_Date': buying_prices.index[-1] if not buying_prices.empty else None,
                        'Buy_Signal_Price': buying_prices.iloc[-1] if not buying_prices.empty else None,
                        'Target_Price': selling_prices.iloc[-1] if not selling_prices.empty else None,
                        # Add other necessary data fields here
                    })

                except Exception as e:
                    print(f"Error processing data for {ticker}: {e}")

        final_df = pd.DataFrame(data_list)
        final_df.sort_values(by="Score", ascending=False, inplace=True)
        final_df.to_csv("Golden_Cross_Final.csv", index=False)
        print(final_df)
    else:
        print("Error downloading Nifty 500 data.")


def run_macd_strategy():
    tickers_nifty50 = si.tickers_nifty50()
    nifty500_symbol = '^NSEI'  # Nifty 500 index symbol

    start = datetime.datetime.now() - datetime.timedelta(days=1825)
    end = datetime.datetime.now()

    os.makedirs('stock_data', exist_ok=True)

    nifty500_df, nifty500_csv_path = download_and_save(nifty500_symbol, start, end)

    if nifty500_df is not None:
        nifty500_df['Pct Change'] = nifty500_df['Adj Close'].pct_change()
        sp500_return = (nifty500_df['Pct Change'] + 1).cumprod()[-1]

        data_list = []

        for ticker in tickers_nifty50:
            stock_df, stock_csv_path = download_and_save(ticker, start, end)

            if stock_df is not None and 'Adj Close' in stock_df.columns:
                try:
                    stock_df['Pct Change'] = stock_df['Adj Close'].pct_change()
                    stock_return = (stock_df['Pct Change'] + 1).cumprod()[-1]
                    returns_compared = round((stock_return / sp500_return), 2)

                    moving_averages = [150, 200]
                    for ma in moving_averages:
                        stock_df[f'SMA_{ma}'] = round(stock_df['Adj Close'].rolling(window=ma).mean(), 2)

                    latest_price = stock_df['Adj Close'].iloc[-1]
                    moving_average_150 = stock_df['SMA_150'].iloc[-1]
                    moving_average_200 = stock_df['SMA_200'].iloc[-1]
                    low_52week = round(min(stock_df['Low'].iloc[-(52 * 5):]), 2)
                    high_52week = round(max(stock_df['High'].iloc[-(52 * 5):]), 2)
                    score = round(returns_compared * 100)

                    # Adjusted conditions
                    condition_1 = latest_price > moving_average_150 > moving_average_200
                    condition_2 = latest_price >= (1.3 * low_52week)
                    condition_3 = latest_price >= (0.75 * high_52week)
                    condition_4 = get_and_print_pe_ratios([ticker])  # This line is adjusted
                    condition_5 = True  # Just a placeholder for now, you can add your condition here

                    if condition_1 and condition_2 and condition_3 and condition_4 and condition_5:
                        weekly_data = download_stock_data(ticker, "1wk")
                        buying_prices, selling_prices = macd_strategy(weekly_data)

                        print(f"\nBuying Prices for {ticker} - Weekly Data:")
                        print(buying_prices)
                        print(f"\nSelling Prices for {ticker} - Weekly Data:")
                        print(selling_prices)

                        plt.figure(figsize=(10, 6))
                        plt.plot(weekly_data['Date'], weekly_data['Close'], label='Close Price')
                        plt.plot(weekly_data['Date'], weekly_data['MA8'], label='8-day MA')
                        plt.plot(weekly_data['Date'], weekly_data['MA34'], label='34-day MA')
                        plt.scatter(buying_prices.index, buying_prices, marker='^', color='g', label='Buy Signal')
                        if not selling_prices.empty:
                            plt.scatter(selling_prices.index, selling_prices, marker='v', color='r', label='Sell Signal')
                        plt.title(f'Golden Cross Strategy - {ticker} - Weekly Data')
                        plt.xlabel('Date')
                        plt.ylabel('Price')
                        plt.legend()
                        plt.show()

                    data_list.append({
                        'Ticker': ticker,
                        'Latest_Price': latest_price,
                        'Score': score,
                        'Moving_avg_150': moving_average_150,
                        'Moving_avg_200': moving_average_200,
                        'Buy_Signal_Date': buying_prices.index[-1] if not buying_prices.empty else None,
                        'Buy_Signal_Price': buying_prices.iloc[-1] if not buying_prices.empty else None,
                        'Target_Price': selling_prices.iloc[-1] if not selling_prices.empty else None,
                        # Add other necessary data fields here
                    })

                except Exception as e:
                    print(f"Error processing data for {ticker}: {e}")

        final_df = pd.DataFrame(data_list)
        final_df.sort_values(by="Score", ascending=False, inplace=True)
        final_df.to_csv("Golden_Cross_Final.csv", index=False)
        print(final_df)
    else:
        print("Error downloading Nifty 500 data.")
def run_rsi_strategy():
    tickers_nifty50 = si.tickers_nifty50()
    nifty500_symbol = '^NSEI'  # Nifty 500 index symbol

    start = datetime.datetime.now() - datetime.timedelta(days=1825)
    end = datetime.datetime.now()

    os.makedirs('stock_data', exist_ok=True)

    nifty500_df, nifty500_csv_path = download_and_save(nifty500_symbol, start, end)

    if nifty500_df is not None:
        nifty500_df['Pct Change'] = nifty500_df['Adj Close'].pct_change()
        sp500_return = (nifty500_df['Pct Change'] + 1).cumprod()[-1]

        data_list = []

        for ticker in tickers_nifty50:
            stock_df, stock_csv_path = download_and_save(ticker, start, end)

            if stock_df is not None and 'Adj Close' in stock_df.columns:
                try:
                    stock_df['Pct Change'] = stock_df['Adj Close'].pct_change()
                    stock_return = (stock_df['Pct Change'] + 1).cumprod()[-1]
                    returns_compared = round((stock_return / sp500_return), 2)

                    moving_averages = [150, 200]
                    for ma in moving_averages:
                        stock_df[f'SMA_{ma}'] = round(stock_df['Adj Close'].rolling(window=ma).mean(), 2)

                    latest_price = stock_df['Adj Close'].iloc[-1]
                    moving_average_150 = stock_df['SMA_150'].iloc[-1]
                    moving_average_200 = stock_df['SMA_200'].iloc[-1]
                    low_52week = round(min(stock_df['Low'].iloc[-(52 * 5):]), 2)
                    high_52week = round(max(stock_df['High'].iloc[-(52 * 5):]), 2)
                    score = round(returns_compared * 100)

                    # Adjusted conditions
                    condition_1 = latest_price > moving_average_150 > moving_average_200
                    condition_2 = latest_price >= (1.3 * low_52week)
                    condition_3 = latest_price >= (0.75 * high_52week)
                    condition_4 = get_and_print_pe_ratios([ticker])  # This line is adjusted
                    condition_5 = True  # Just a placeholder for now, you can add your condition here

                    if condition_1 and condition_2 and condition_3 and condition_4 and condition_5:
                        weekly_data = download_stock_data(ticker, "1wk")
                        buying_prices, selling_prices = rsi_strategy(weekly_data)

                        print(f"\nBuying Prices for {ticker} - Weekly Data:")
                        print(buying_prices)
                        print(f"\nSelling Prices for {ticker} - Weekly Data:")
                        print(selling_prices)

                        plt.figure(figsize=(10, 6))
                        plt.plot(weekly_data['Date'], weekly_data['Close'], label='Close Price')
                        plt.plot(weekly_data['Date'], weekly_data['MA8'], label='8-day MA')
                        plt.plot(weekly_data['Date'], weekly_data['MA34'], label='34-day MA')
                        plt.scatter(buying_prices.index, buying_prices, marker='^', color='g', label='Buy Signal')
                        if not selling_prices.empty:
                            plt.scatter(selling_prices.index, selling_prices, marker='v', color='r', label='Sell Signal')
                        plt.title(f'Golden Cross Strategy - {ticker} - Weekly Data')
                        plt.xlabel('Date')
                        plt.ylabel('Price')
                        plt.legend()
                        plt.show()

                    data_list.append({
                        'Ticker': ticker,
                        'Latest_Price': latest_price,
                        'Score': score,
                        'Moving_avg_150': moving_average_150,
                        'Moving_avg_200': moving_average_200,
                        'Buy_Signal_Date': buying_prices.index[-1] if not buying_prices.empty else None,
                        'Buy_Signal_Price': buying_prices.iloc[-1] if not buying_prices.empty else None,
                        'Target_Price': selling_prices.iloc[-1] if not selling_prices.empty else None,
                        # Add other necessary data fields here
                    })

                except Exception as e:
                    print(f"Error processing data for {ticker}: {e}")

        final_df = pd.DataFrame(data_list)
        final_df.sort_values(by="Score", ascending=False, inplace=True)
        final_df.to_csv("Golden_Cross_Final.csv", index=False)
        print(final_df)
    else:
        print("Error downloading Nifty 500 data.")

def main():
    while True:
        print("\nMenu:")
        print("1. Run Golden Cross Strategy")
        print("2. Run RSI Strategy")
        print("3. Run MACD Strategy")
        print("4. Exit")
        choice = input("Enter your choice: ")

        if choice == "1":
            run_golden_cross_strategy()
        elif choice == "2":
            run_rsi_strategy()
        elif choice == "3":
            run_macd_strategy()
        elif choice == "4":
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()