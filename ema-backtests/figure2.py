# GRAPH OF BHARTIARTL PROFITS
import pandas as pd
from matplotlib import pyplot as plt

# Crossover profit curve
crossover_profits = pd.read_csv('crossover_BHARTIARTL.csv')[['Date', 'Total']]
crossover_profits['Date'] = pd.to_datetime(crossover_profits['Date'])
crossover_profits.index = crossover_profits['Date']

# MACD profit curve
macd_profits = pd.read_csv('macd_BHARTIARTL.csv')

# Holding profit curve
hold_profits = (macd_profits['Close'] * 307) - 100000

x = crossover_profits.index
y1 = crossover_profits['Total']
y2 = macd_profits['Total']
y3 = hold_profits

# plotting the points
plt.plot(x, y1)
plt.plot(x, y2)
plt.plot(x, y3)

# naming the x axis
plt.xlabel('Date')
# naming the y axis
plt.ylabel('Profit')

# giving a title to my graph
plt.title(f'BHARTIARTL Backtest')
plt.legend(["Crossover", "MACD", "Hold"], loc ="lower right")
plt.show()