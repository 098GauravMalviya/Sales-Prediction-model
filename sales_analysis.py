import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from prophet import Prophet
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("ecommerce_sales_data (2).csv")
df1 = pd.read_csv("updated_sales.csv")

print(df.head())                

# dataset info
print(df.info())

# check missing values
print(df.isnull().sum())
df = df.dropna()
df['Order Date'] = pd.to_datetime(df['Order Date'])
df['Sales'] = df['Quantity'] * df['Sales']
print(df.head())