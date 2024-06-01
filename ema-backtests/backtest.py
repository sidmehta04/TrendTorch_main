# BACKTEST
import pandas as pd
from nsepy import get_history as gh
from datetime import datetime
from utils import *

stock_list = ['BHARTIARTL', 'ICICIBANK', 'TATASTEEL',
              'IDEA', 'CANBK', 'JINDALSTEL',
               'LUXIND', 'IDFC', 'CEATLTD',
              'ICICINIFTY'
]

symbol = stock_list[0]
start = datetime(2010, 1, 1)
end = datetime(2024, 2, 1)
df = gh(symbol=symbol, start=start, end=end)
budget = 100000

# CROSSOVER
crossover_df = multiple_emas(df, budget)
crossover_df.to_csv(f'crossover_{symbol}.csv', index=True)


# MACD
macd_df = macd(df, budget)
macd_df.to_csv(f'macd_{symbol}.csv',index=True)

all_tests = []
for stock in stock_list:
    start = datetime(2016, 1, 1)
    end = datetime(2019, 1, 1)
    df = gh(symbol=stock, start=start, end=end)

    # MACD
    macd_df = macd(df[['Close']], budget)
    # CROSSOVER
    crossover_df = multiple_emas(df[['Close']], budget)


    crossover_total = crossover_df['Total'][-1]
    macd_total = macd_df['Total'][-1]

    all_tests.append(
        {'Symbol': stock, 'Crossover': crossover_total, 'MACD': macd_total}
    )
all_tests_df = pd.DataFrame(all_tests)
all_tests_df.to_csv('all_tests.csv', index=False)
