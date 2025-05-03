import pandas as pd
import numpy as np
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.arima.model import ARIMA
from sklearn.metrics import mean_squared_error, mean_absolute_error
from sqlalchemy import create_engine

# -------------------------------
# 1. Load your enriched data
# -------------------------------
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/Predictive Analysis/doc_data_enriched.xlsx"
df = pd.read_excel(file_path)

# Clean column names
df.columns = df.columns.str.lower().str.replace('.', '_')

# Standardize key text fields
df['vendor_name'] = df['vendor_name'].str.upper().str.strip()
df['po_category_description'] = df['po_category_description'].str.upper().str.strip()

# Convert dates and create Fiscal Year and Fiscal Quarter
df['ordered_date'] = pd.to_datetime(df['ordered_date'], errors='coerce')

# Fiscal Year: July 1 - June 30
df['fiscal_year'] = df['ordered_date'].apply(lambda x: x.year + 1 if x.month >= 7 else x.year)
df['fiscal_quarter'] = df['ordered_date'].apply(lambda x: (
    'Q1' if 7 <= x.month <= 9 else
    'Q2' if 10 <= x.month <= 12 else
    'Q3' if 1 <= x.month <= 3 else
    'Q4'
))

# -------------------------------
# 2. Grouping: Vendor and Category Level
# -------------------------------
vendor_group = df.groupby(['vendor_name', 'fiscal_year', 'fiscal_quarter'])['line_total'].sum().reset_index()
category_group = df.groupby(['po_category_description', 'fiscal_year', 'fiscal_quarter'])['line_total'].sum().reset_index()

# Containers
vendor_forecasts = []
category_forecasts = []

# -------------------------------
# 2.5: Select Top N Vendors and Categories
# -------------------------------
TOP_N = 10  # Change this number as needed

# Top Vendors by Total Spend
top_vendors = vendor_group.groupby('vendor_name')['line_total'].sum().nlargest(TOP_N).index

# Top Categories by Total Spend
top_categories = category_group.groupby('po_category_description')['line_total'].sum().nlargest(TOP_N).index

# -------------------------------
# 3. Forecasting function with SEASONALITY
# -------------------------------
def forecast_series(series):
    series = series.sort_index()
    
    if len(series) < 3:  # Require enough data for seasonal models, reccomend 4
        return None

    train = series.iloc[:-1]
    test = series.iloc[-1:]

    forecasts = {}
    metrics = {}

    # Moving Average Forecast
    moving_avg_forecast = train.rolling(3, min_periods=1).mean().iloc[-1]
    forecasts['moving_average'] = moving_avg_forecast

    try:
        model_es = ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=4)
        model_es_fit = model_es.fit()
        exp_forecast = model_es_fit.forecast(1).iloc[0]
        forecasts['exponential_smoothing'] = exp_forecast
    except:
        forecasts['exponential_smoothing'] = np.nan

    try:
        model_arima = ARIMA(train, order=(1,1,1), seasonal_order=(1,1,1,4))
        model_arima_fit = model_arima.fit()
        arima_forecast = model_arima_fit.forecast(1).iloc[0]
        forecasts['arima'] = arima_forecast
    except:
        forecasts['arima'] = np.nan

    try:
        y_pred = model_arima_fit.predict(start=train.index[-1]+1, end=train.index[-1]+1)
        y_true = test.values
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        mae = mean_absolute_error(y_true, y_pred)
        mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if y_true[0] != 0 else np.nan
        metrics = {'rmse': rmse, 'mae': mae, 'mape': mape}
    except:
        metrics = {'rmse': np.nan, 'mae': np.nan, 'mape': np.nan}

    return forecasts, metrics

# -------------------------------
# 4. Run Forecasting for Top N (with 4-quarter chaining)
# -------------------------------

# Create a combined fiscal_year_quarter field
vendor_group['fiscal_year_quarter'] = vendor_group['fiscal_year'].astype(str) + '-Q' + vendor_group['fiscal_quarter'].str[1]
category_group['fiscal_year_quarter'] = category_group['fiscal_year'].astype(str) + '-Q' + category_group['fiscal_quarter'].str[1]

# Helper to generate next fiscal quarter
def get_next_quarter(fq):
    year, quarter = fq.split('-Q')
    year = int(year)
    quarter = int(quarter)
    
    if quarter == 4:
        next_year = year + 1
        next_quarter = 1
    else:
        next_year = year
        next_quarter = quarter + 1

    return f"{next_year}-Q{next_quarter}"

# Forecasting for vendors
for vendor in top_vendors:
    temp = vendor_group[vendor_group['vendor_name'] == vendor].set_index('fiscal_year_quarter')['line_total']
    if temp.empty:
        continue
    
    forecasts_chain = []
    temp_series = temp.copy()

    for _ in range(4):  # Forecast 4 quarters ahead
        result = forecast_series(temp_series)
        if result:
            forecasts, metrics = result
            next_quarter = get_next_quarter(temp_series.index.max())
            forecast_value = forecasts['exponential_smoothing']  # or moving_average or arima
            
            # Save forecast
            forecasts_chain.append({
                'vendor_name': vendor,
                'forecasted_fiscal_quarter': next_quarter,
                'moving_average_forecast': forecasts['moving_average'],
                'exponential_smoothing_forecast': forecasts['exponential_smoothing'],
                'arima_forecast': forecasts['arima'],
                'rmse': metrics['rmse'],
                'mae': metrics['mae'],
                'mape': metrics['mape']
            })
            
            # Add forecast back into temp_series for next prediction
            temp_series.loc[next_quarter] = forecast_value
            temp_series = temp_series.sort_index()
        else:
            break

    vendor_forecasts.extend(forecasts_chain)

# Forecasting for categories
for category in top_categories:
    temp = category_group[category_group['po_category_description'] == category].set_index('fiscal_year_quarter')['line_total']
    if temp.empty:
        continue
    
    forecasts_chain = []
    temp_series = temp.copy()

    for _ in range(4):  # Forecast 4 quarters ahead
        result = forecast_series(temp_series)
        if result:
            forecasts, metrics = result
            next_quarter = get_next_quarter(temp_series.index.max())
            forecast_value = forecasts['exponential_smoothing']
            
            # Save forecast
            forecasts_chain.append({
                'po_category_description': category,
                'forecasted_fiscal_quarter': next_quarter,
                'moving_average_forecast': forecasts['moving_average'],
                'exponential_smoothing_forecast': forecasts['exponential_smoothing'],
                'arima_forecast': forecasts['arima'],
                'rmse': metrics['rmse'],
                'mae': metrics['mae'],
                'mape': metrics['mape']
            })
            
            temp_series.loc[next_quarter] = forecast_value
            temp_series = temp_series.sort_index()
        else:
            break

    category_forecasts.extend(forecasts_chain)

# Convert results to DataFrames
vendor_forecast_df = pd.DataFrame(vendor_forecasts)
category_forecast_df = pd.DataFrame(category_forecasts)

# -------------------------------
# 5. Filter only useful forecasted years (optional)
# -------------------------------
YEAR_CUTOFF = 2025  # Adjustable

def extract_year(fq):
    return int(fq.split('-Q')[0])

if not vendor_forecast_df.empty:
    vendor_forecast_df = vendor_forecast_df[vendor_forecast_df['forecasted_fiscal_quarter'].apply(extract_year) >= YEAR_CUTOFF]

if not category_forecast_df.empty:
    category_forecast_df = category_forecast_df[category_forecast_df['forecasted_fiscal_quarter'].apply(extract_year) >= YEAR_CUTOFF]

# -------------------------------
# 6. Export to Postgres
# -------------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

if not vendor_forecast_df.empty:
    vendor_forecast_df.to_sql("vendor_forecast_results", engine, if_exists="replace", index=False)
    print("✅ Vendor forecast results saved to Postgres!")

if not category_forecast_df.empty:
    category_forecast_df.to_sql("category_forecast_results", engine, if_exists="replace", index=False)
    print("✅ Category forecast results saved to Postgres!")

print("🎯 Script completed successfully!")
