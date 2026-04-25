import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error
from prophet import Prophet


df = pd.read_csv("data/ecommerce_sales_data (2).csv")
df1 = pd.read_csv("data/Updated_sales.csv")
df2 = pd.read_csv("data/Holidays.csv")
df3 = pd.read_csv("data/Samsung Dataset.csv")
df4 = pd.read_csv('data/Sony_stock_data.csv', skiprows=[0,1,2], 
                  names=['Date', 'Close', 'High', 'Low', 'Open', 'Volume'])
df5 = pd.read_csv("data/NVidia_stock_history.csv")
print(df.head()) 
df_commodity = pd.read_csv("data/commodity_prices.csv")
df_inf_raw   = pd.read_csv("data/Inflationdata.csv", skiprows=4)
df_int_raw   = pd.read_csv("data/interest_rates.csv")
df_lithium   = pd.read_excel("data/ds140-lithium-2021.xlsx",sheet_name='Lithium statistics', header=None) 


# dataset info
print(df.info())

# check missing values
print(df.isnull().sum())
df = df.dropna()
df['Order Date'] = pd.to_datetime(df['Order Date']).dt.normalize()
df2['Date'] = pd.to_datetime(df2['Date'], errors='coerce')
df3['Date'] = pd.to_datetime(df3['Date'], errors='coerce').dt.normalize()
df4['Date'] = pd.to_datetime(df4['Date'])
df5['Date'] = pd.to_datetime(df5['Date'], utc=True).dt.tz_convert(None).dt.normalize()

# STEP 1. clean and standardize datasets

# Fix Updated_sales (has repeated header rows)
df1 = df1[df1['Order Date'] != 'Order Date']  # remove duplicate headers

# Convert to numeric BEFORE arithmetic — this is the fix
df1['Quantity Ordered'] = pd.to_numeric(df1['Quantity Ordered'], errors='coerce')
df1['Price Each'] = pd.to_numeric(df1['Price Each'], errors='coerce')
df1['Order Date'] = pd.to_datetime(df1['Order Date'],format='mixed', errors='coerce')
df1 = df1.dropna(subset=['Order Date'])
df1['Revenue'] = df1['Quantity Ordered'] * df1['Price Each']

# Fix Sony (already in your code with skiprows)
df4['Date'] = pd.to_datetime(df4['Date'])
df4[['Close','High','Low','Open','Volume']] = df4[['Close','High','Low','Open','Volume']].apply(pd.to_numeric, errors='coerce')

# Commodity
df_commodity['date'] = pd.to_datetime(df_commodity['date']).dt.normalize()
 
# Lithium
df_lithium = df_lithium.iloc[5:].copy()
df_lithium.columns = ['year','us_prod','imports','exports','consumption',
                      'unit_value_usd','uv_98','world_prod_t','world_li','world_lce']
df_lithium = df_lithium.drop(columns='uv_98')
for col in df_lithium.columns:
    df_lithium[col] = pd.to_numeric(df_lithium[col], errors='coerce')
df_lithium = df_lithium.dropna(subset=['year'])
df_lithium['year'] = df_lithium['year'].astype(int)

# Fix NVidia timezone
df5['Date'] = pd.to_datetime(df5['Date'], utc=True).dt.tz_localize(None).dt.normalize()

# Drop index column from Holidays
df2 = df2.drop(columns=['Unnamed: 0'])

# STEP 2. feature engineering on main sales dataset (prediction of future sales)

df['year'] = df['Order Date'].dt.year
df['month'] = df['Order Date'].dt.month
df['week'] = df['Order Date'].dt.isocalendar().week.astype(int)
df['day_of_week'] = df['Order Date'].dt.dayofweek
df['quarter'] = df['Order Date'].dt.quarter

# Is it a holiday?
holiday_dates = set(df2['Date'].dt.date)
df['is_holiday'] = df['Order Date'].dt.date.apply(lambda x: x in holiday_dates).astype(int)

# Rolling averages (lag features) — crucial for time-series ML
df = df.sort_values('Order Date')
df['sales_lag_7']  = df['Sales'].shift(7)
df['sales_lag_30'] = df['Sales'].shift(30)
df['sales_rolling_7_mean'] = df['Sales'].rolling(7).mean()

# Merge stock prices as "market sentiment" features
df_daily = df.groupby('Order Date')[['Sales','Profit']].sum().reset_index()
df_daily = df_daily.merge(
    df5[['Date','Close']].rename(columns={'Close':'nvidia_close'}),
    left_on='Order Date', right_on='Date', how='left'
).drop(columns='Date')
df_daily = df_daily.merge(
    df3[['Date','Close']].rename(columns={'Close':'samsung_close'}),
    left_on='Order Date', right_on='Date', how='left'
).drop(columns='Date')

# Fill missing stock values (weekends/holidays have no stock data)
df_daily['nvidia_close'] = df_daily['nvidia_close'].ffill()
df_daily['samsung_close'] = df_daily['samsung_close'].ffill()

# Merge stock features back onto the original df
df = df.merge(
    df_daily[['Order Date', 'nvidia_close', 'samsung_close']],
    on='Order Date', how='left'
)

#STEP 2.5: Add commodity prices and macroeconomic indicators

# Master daily calendar matching sales date range
cal = pd.DataFrame({
    'date': pd.date_range(df['Order Date'].min(), df['Order Date'].max(), freq='D')
})
cal['year']  = cal['date'].dt.year
cal['month'] = cal['date'].dt.month
 
# ── Inflation (annual → daily broadcast) ──────────────────────
india_inf  = df_inf_raw[df_inf_raw['Country Name'] == 'India'].iloc[0]
year_cols  = [c for c in df_inf_raw.columns if c.isdigit()]
annual_inf = pd.DataFrame({
    'year': [int(y) for y in year_cols],
    'inflation_india': [
        float(india_inf[y]) if str(india_inf[y]) != 'nan' else np.nan
        for y in year_cols
    ]
})
cal = cal.merge(annual_inf, on='year', how='left')
 
# ── Interest rate (annual → daily, forward-fill 2023/2024) ────
india_int   = df_int_raw[df_int_raw['Country Name'] == 'India'].iloc[0]
year_cols_i = [c for c in df_int_raw.columns if c.isdigit()]
annual_int  = pd.DataFrame({
    'year': [int(y) for y in year_cols_i],
    'interest_rate': [
        float(india_int[y]) if str(india_int[y]) != 'nan' else np.nan
        for y in year_cols_i
    ]
})
max_year = int(cal['year'].max())
ext = pd.DataFrame({
    'year': range(annual_int['year'].max() + 1, max_year + 1),
    'interest_rate': [np.nan] * (max_year - annual_int['year'].max())
})
annual_int = pd.concat([annual_int, ext], ignore_index=True)
annual_int['interest_rate'] = annual_int['interest_rate'].ffill()
cal = cal.merge(annual_int, on='year', how='left')
 
# ── Commodity prices (monthly → forward-fill to daily) ────────
COMMODITIES = {
    'Aluminum'        : 'price_aluminum',
    'Copper'          : 'price_copper',
    'Nickel'          : 'price_nickel',
    'Crude oil, Brent': 'price_crude_oil',
    'Natural gas, US' : 'price_natural_gas',
}
df_rel = df_commodity[df_commodity['commodity_name'].isin(COMMODITIES.keys())].copy()
df_rel['col'] = df_rel['commodity_name'].map(COMMODITIES)
pivot = df_rel.pivot_table(
    index='date', columns='col',
    values='price_nominal_usd', aggfunc='mean'
).reset_index()
cal = cal.merge(pivot, on='date', how='left')
price_cols = list(COMMODITIES.values())
cal[price_cols] = cal[price_cols].ffill()
 
# ── Lithium (linear extrapolation 2022-2024) ──────────────────
trend     = df_lithium[df_lithium['year'].between(2010, 2021)].dropna(subset=['unit_value_usd'])
li_fit    = np.polyfit(trend['year'], trend['unit_value_usd'], 1)
lithium_ext = pd.DataFrame({
    'year': range(2022, max_year + 1),
    'lithium_price_usd': [np.polyval(li_fit, y) for y in range(2022, max_year + 1)]
})
lithium_all = pd.concat([
    df_lithium[['year','unit_value_usd']].rename(columns={'unit_value_usd':'lithium_price_usd'}),
    lithium_ext
], ignore_index=True)
cal = cal.merge(lithium_all, on='year', how='left')
 
# ── Merge all aligned features back onto main df ──────────────
macro_cols = ['inflation_india','interest_rate','lithium_price_usd'] + price_cols
df = df.merge(cal[['date'] + macro_cols],
              left_on='Order Date', right_on='date', how='left')
df = df.drop(columns='date')
 
print("✅ Macro features merged. Shape:", df.shape)
print(df[['Order Date','inflation_india','interest_rate',
          'price_copper','lithium_price_usd']].head())

# STEP 3. Aggregate to daily/weekly level for time-series forecasting

daily_sales = df.groupby('Order Date')['Sales'].sum().reset_index()
daily_sales.columns = ['ds', 'y']

# Add holiday regressor to Prophet
m = Prophet(yearly_seasonality=True, weekly_seasonality=True)

# Add holidays as a custom dataframe
holiday_df = df2[['Date','Name']].rename(columns={'Date':'ds','Name':'holiday'})
m = Prophet(holidays=holiday_df)

m.fit(daily_sales)
future = m.make_future_dataframe(periods=90)  # predict 90 days ahead
forecast = m.predict(future)
m.plot(forecast)


#STEP 4. ML model for category/region-level sales prediction 

features = ['month','week','day_of_week','quarter','is_holiday',
            'sales_lag_7','sales_lag_30','sales_rolling_7_mean',
            'nvidia_close','samsung_close', 'inflation_india','interest_rate','lithium_price_usd', 'price_aluminum','price_copper', 'price_crude_oil']

# One-hot encode Category and Region
df_model = pd.get_dummies(df, columns=['Category','Region'])
df_model = df_model.dropna(subset=features)

X = df_model[features + [c for c in df_model.columns if 'Category_' in c or 'Region_' in c]]
y = df_model['Sales']

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, shuffle=False)
model = LinearRegression()
model.fit(X_train, y_train)
preds = model.predict(X_test)
print("MAE:", mean_absolute_error(y_test, preds))


# STEP 5. Visualizations

# 1. Monthly sales trend
plt.figure(figsize=(14, 5))
df.groupby(df['Order Date'].dt.to_period('M'))['Sales'].sum().plot(kind='bar')
plt.title('Monthly Sales Trend')
plt.xlabel('Month')
plt.ylabel('Total Sales')
plt.tight_layout()
plt.savefig('monthly_sales.png')
plt.close()  # ← critical: close before next plot

# 2. Sales by category
plt.figure(figsize=(8, 5))
sns.boxplot(data=df, x='Category', y='Sales')
plt.title('Sales Distribution by Category')
plt.tight_layout()
plt.savefig('sales_by_category.png')
plt.close()

# 3. Heatmap: Region × Month
plt.figure(figsize=(12, 5))
pivot = df.pivot_table(values='Sales', index='Region',
                       columns=df['Order Date'].dt.month, aggfunc='sum')
pivot.columns = ['Jan','Feb','Mar','Apr','May','Jun',
                 'Jul','Aug','Sep','Oct','Nov','Dec']
sns.heatmap(pivot, annot=True, fmt='.0f', cmap='YlOrRd')
plt.title('Sales Heatmap: Region × Month')
plt.tight_layout()
plt.savefig('region_month_heatmap.png')
plt.close()

# 4. Prophet forecast plot
fig = m.plot(forecast)
plt.title('90-Day Sales Forecast')
fig.savefig('forecast.png')
plt.close()

# 5. Prophet components (trend + seasonality breakdown) — bonus, very useful
fig2 = m.plot_components(forecast)
fig2.savefig('forecast_components.png')
plt.close()

print("✅ All plots saved.")
print(df[['Order Date','Sales','nvidia_close','samsung_close']].head())


import joblib

# Save the trained model — this is all your backend needs
joblib.dump(model, 'model.pkl')
print("✅ Model saved to model.pkl")
joblib.dump(list(X.columns), 'model_features.pkl')  # ← add this if missing
print("✅ Feature columns saved to model_features.pkl")

## CONNNECTING TO DATABASE AND USING SMART QUERIES

from database.create_database import get_connection, SmartQuery

conn = get_connection()
sq = SmartQuery(conn)

# Replace your raw df reads with smart queries
df = sq.query(category="end_product", ticker="NVDA", include_macro=True)

# For Prophet - pull daily aggregated sales
daily_sales = sq.stock_sales_correlation("NVDA")[['date','total_revenue']].rename(
    columns={'date':'ds','total_revenue':'y'}
)

#TEST RUN

# Sales during Indian holidays
print(sq.holiday_sales_summary())

# Copper price impact on electronics
print(sq.commodity_impact("Copper", category="end_product"))

# Full macro context
print(sq.macro_sales_trend())