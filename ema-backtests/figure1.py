# GRAPH OF NIFTY50
import pandas as pd
from nsepy import get_history as gh
from matplotlib import pyplot as plt
from datetime import datetime

symbol = 'INIFTY'
start = datetime(2011, 1, 1)
end = datetime(2021, 1, 1)
df = gh(symbol=symbol, start=start, end=end)
print(type(df.index[0]))
x = df.index
y = df['Close']

# plotting the points
plt.plot(x, y)

# naming the x axis
plt.xlabel('Dates')
# naming the y axis
plt.ylabel('Prices')

# giving a title to my graph
plt.title(f'{symbol} Prices')

plt.show()