import numpy as np
import pandas as pd
from numpy import isnan
import math

# Algorithms

def _buy_sell_function_crossover(data):
    buy_list = []
    sell_list = []
    flag_long = False
    flag_short = False
    for i in range(0,len(data)):
        # main algorithm which allows for stocks to be bought and sold
        if data['Middle'][i] < data['Long'][i] and data['Short'][i] < data['Middle'][i] and flag_long == False and flag_short == False:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)
            flag_short = True
            prev_buy_value = data['Close'][i]
        elif flag_short == True and data['Short'][i] > data['Middle'][i] and prev_buy_value < data['Close'][i]:
            buy_list.append(np.nan)
            sell_list.append(data['Close'][i])
            flag_short = False
        elif data['Middle'][i] > data['Long'][i] and data['Short'][i] > data['Middle'][i] and flag_long == False and flag_short == False:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)
            flag_long = True
            prev_buy_value = data['Close'][i]
        elif flag_long == True and data['Short'][i] < data['Middle'][i] and prev_buy_value < data['Close'][i]:
            buy_list.append(np.nan)
            sell_list.append(data['Close'][i])
            flag_long = False
        else:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
    return buy_list, sell_list

def _buy_sell_function_macd(data):
    buy_list = []
    sell_list = []
    bought = False
    for i in range(len(data)):
        if data['MACD'][i] > data['Signal'][i] and bought == False:
            buy_list.append(data['Close'][i])
            sell_list.append(np.nan)
            bought = True
            prev_buy_value = data['Close'][i]
        elif data['MACD'][i] < data['Signal'][i] and bought == True and data['Close'][i] > prev_buy_value:
            buy_list.append(np.nan)
            sell_list.append(data['Close'][i])
            bought = False
        else:
            buy_list.append(np.nan)
            sell_list.append(np.nan)
    return buy_list, sell_list

def _profits(buys, sells, stocks_to_buy, stocks_to_sell):
    profits = []
    for i in range(len(buys)):
        if isnan(buys[i]) == False:
            profits.append(-buys[i] * stocks_to_buy[i])
        elif isnan(sells[i]) == False:
            profits.append(sells[i] * stocks_to_sell[i])
        else:
            profits.append(0)
    return profits

def _stocks_to_buy(df, budget):
    stocks_to_buy_list = []
    for i in range(len(df)):
        value = df['Buy'][i]
        if isnan(value) == True:
            stocks_to_buy_list.append(0)
        else:
            stocks_to_buy_list.append(math.floor(budget/value))
    return stocks_to_buy_list

def _stocks_to_sell(df):
    stocks_to_sell_list = []
    for i in range(len(df)):
        if isnan(df['Buy'][i]) == False:
            prev_value = df['Stocks_To_Buy'][i]
            tag = True
        if isnan(df['Sell'][i]) == False and tag == True:
            stocks_to_sell_list.append(prev_value)
        elif isnan(df['Sell'][i]) == True or tag == False:
            stocks_to_sell_list.append(0)
    return stocks_to_sell_list

def _current_assets(stocks_to_buy, stocks_to_sell):
    current_assets = list([0])
    for i in range(1, len(stocks_to_buy)):
        diff = stocks_to_buy[i] - stocks_to_sell[i]
        current_assets.append(current_assets[-1] + diff)
    return current_assets

def _totals(df):
    totals = list([0])
    for i in range(1, len(df)):
        if df['Profits'][i] == 0:
            totals.append(totals[-1])
        else:
            totals.append(totals[-1] + df['Profits'][i])
    totals = totals + df['Value']
    return totals

def multiple_emas(df, budget):
    df['Short'] = df.Close.ewm(span=5, adjust=False).mean()
    df['Middle'] = df.Close.ewm(span=20, adjust=False).mean()
    df['Long'] = df.Close.ewm(span=60, adjust=False).mean()
    df['Buy'], df['Sell'] = _buy_sell_function_crossover(df)
    df['Stocks_To_Buy'] = _stocks_to_buy(df, budget)
    df['Stocks_To_Sell'] = _stocks_to_sell(df)
    df['Current_Assets'] = _current_assets(df['Stocks_To_Buy'], df['Stocks_To_Sell'])
    df['Value'] = df['Current_Assets'] * df['Close']
    df['Profits'] = _profits(df['Buy'], df['Sell'], df['Stocks_To_Buy'], df['Stocks_To_Sell'])
    df['Total'] = _totals(df)
    return df

def macd(df, budget):
    df['MACD'] = df.Close.ewm(span=12, adjust=False).mean() - df.Close.ewm(span=26, adjust=False).mean()
    df['Signal'] = df.MACD.ewm(span=9, adjust=False).mean()
    df['Hist'] = df['MACD'] - df['Signal']
    df['Buy'], df['Sell'] = _buy_sell_function_macd(df)
    df['Stocks_To_Buy'] = _stocks_to_buy(df, budget)
    df['Stocks_To_Sell'] = _stocks_to_sell(df)
    df['Current_Assets'] = _current_assets(df['Stocks_To_Buy'], df['Stocks_To_Sell'])
    df['Value'] = df['Current_Assets'] * df['Close']
    df['Profits'] = _profits(df['Buy'], df['Sell'], df['Stocks_To_Buy'], df['Stocks_To_Sell'])
    df['Total'] = _totals(df)
    return df
