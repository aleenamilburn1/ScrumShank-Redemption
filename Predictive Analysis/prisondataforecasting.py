# Forecast and Evaluation Script for Vendor and Category Sales (with terminal output)

import pandas as pd
import numpy as np
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_squared_error

# Load and preprocess data
df = pd.read_csv('/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/Predictive Analysis/MarchData.csv')
df['Ordered.Date'] = pd.to_datetime(df['Ordered.Date'])
df['Fiscal_Year'] = df['Ordered.Date'].dt.year

# Group data by Fiscal Year and Vendor / Category
sales_by_vendor = df.groupby(['Fiscal_Year', 'Vendor.Name'])['Line.Total'].sum().reset_index()
sales_by_category = df.groupby(['Fiscal_Year', 'PO.Category.Description'])['Line.Total'].sum().reset_index()

# Function to evaluate forecasts
def evaluate_forecast(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = mean_squared_error(y_true, y_pred, squared=False)
    mape = np.mean(np.abs((y_true - y_pred) / y_true)) * 100 if all(y_true != 0) else np.nan
    return mae, rmse, mape

# Forecasting and evaluation loop (works for vendor or category level)
def forecast_and_evaluate(data, group_col, label):
    forecast_results = []

    for group in data[group_col].unique():
        sales_data = data[data[group_col] == group].set_index('Fiscal_Year')['Line.Total']

        if len(sales_data) < 4:
            print(f"\n⚠️ Not enough data for forecasting for {group}")
            forecast_results.append({
                label: group,
                'Best Model': 'Not Enough Data',
                'Moving Avg Forecast': None,
                'Exp Smoothing Forecast': None,
                'ARIMA Forecast': None,
                'MAE': None,
                'RMSE': None,
                'MAPE': None
            })
            continue

        # Split into training (all but last) and test (last point)
        train = sales_data.iloc[:-1]
        test = sales_data.iloc[-1:]

        # Moving Average Forecast
        mov_avg = train.rolling(window=3).mean().iloc[-1]

        # Exponential Smoothing Forecast
        try:
            exp_model = ExponentialSmoothing(train, trend=None, seasonal=None).fit()
            exp_forecast = exp_model.forecast(1)[0]
        except:
            exp_forecast = np.nan

        # ARIMA Forecast
        try:
            arima_model = ARIMA(train, order=(1,1,1)).fit()
            arima_forecast = arima_model.forecast(1)[0]
        except:
            arima_forecast = np.nan

        # Evaluate forecasts against test
        forecasts = {
            'Moving Average': mov_avg,
            'Exponential Smoothing': exp_forecast,
            'ARIMA': arima_forecast
        }

        scores = {}
        for model_name, forecast in forecasts.items():
            if pd.notna(forecast):
                mae, rmse, mape = evaluate_forecast(test.values, [forecast])
                scores[model_name] = (mae, rmse, mape)

        # Identify best model by RMSE
        if scores:
            best_model = min(scores.items(), key=lambda x: x[1][1])  # sort by RMSE
            best_name = best_model[0]
            mae, rmse, mape = best_model[1]
        else:
            best_name = 'All Failed'
            mae = rmse = mape = None

        # Print evaluation for this group
        print(f"\n📊 {label}: {group}")
        print(f"   Best Model: {best_name}")
        print(f"   MAE:  {mae:.2f}" if mae is not None else "   MAE: N/A")
        print(f"   RMSE: {rmse:.2f}" if rmse is not None else "   RMSE: N/A")
        print(f"   MAPE: {mape:.2f}%" if mape is not None else "   MAPE: N/A")

        forecast_results.append({
            label: group,
            'Best Model': best_name,
            'Moving Avg Forecast': mov_avg,
            'Exp Smoothing Forecast': exp_forecast,
            'ARIMA Forecast': arima_forecast,
            'MAE': mae,
            'RMSE': rmse,
            'MAPE': mape
        })

    return pd.DataFrame(forecast_results)

# Run forecasts and evaluations
vendor_forecast_df = forecast_and_evaluate(sales_by_vendor, 'Vendor.Name', 'Vendor')
category_forecast_df = forecast_and_evaluate(sales_by_category, 'PO.Category.Description', 'Category')

print("\n✅ Forecasting and evaluation complete! Review terminal output above before saving to Excel.")