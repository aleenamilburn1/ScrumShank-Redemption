import pandas as pd
import numpy as np
from sqlalchemy import create_engine
from statsmodels.tsa.holtwinters import ExponentialSmoothing
import warnings

# ------------------------
# 1. Connect to Postgres
# ------------------------
engine = create_engine("postgresql+psycopg2://postgres:ScrumShankRedemp!@localhost:5432/ScrumRedemp")

# ------------------------
# 2. Load Data
# ------------------------
doc_data = pd.read_sql("SELECT vendor_name, ordered_date, line_total FROM doc_data_enriched", engine)

# Ensure ordered_date is datetime
doc_data['ordered_date'] = pd.to_datetime(doc_data['ordered_date'])

# ------------------------
# 3. Clean and Setup
# ------------------------
def get_fiscal_quarter(date):
    month = date.month
    if 7 <= month <= 9:
        return 'Q1'
    elif 10 <= month <= 12:
        return 'Q2'
    elif 1 <= month <= 3:
        return 'Q3'
    elif 4 <= month <= 6:
        return 'Q4'

doc_data['fiscal_year'] = doc_data['ordered_date'].apply(lambda x: x.year + 1 if x.month >= 7 else x.year)
doc_data['fiscal_quarter'] = doc_data['ordered_date'].apply(get_fiscal_quarter)
doc_data['fiscal_year_quarter'] = doc_data['fiscal_year'].astype(str) + '-Q' + doc_data['fiscal_quarter'].str[1]

# ------------------------
# 4. Filter FY2024 and Get Top Vendors
# ------------------------

# Define FY2024 boundaries (July 1, 2023 - June 30, 2024)
fy2024_start = pd.Timestamp('2023-07-01')
fy2024_end = pd.Timestamp('2024-06-30')

doc_data_fy2024 = doc_data[(doc_data['ordered_date'] >= fy2024_start) & (doc_data['ordered_date'] <= fy2024_end)]

# Aggregate spend for FY2024
vendor_spend_2024 = doc_data_fy2024.groupby('vendor_name')['line_total'].sum().reset_index()

# Find Top 10 vendors by FY2024 spend
vendor_spend_2024 = vendor_spend_2024.sort_values('line_total', ascending=False)

# Assign spend_ranking only to Top 10
vendor_spend_2024['spend_ranking'] = np.nan  # Initialize column as NaN
vendor_spend_2024.loc[vendor_spend_2024.index[:10], 'spend_ranking'] = range(1, 11)

# Top 10 vendors by FY2024 spend
top_vendors = vendor_spend_2024.sort_values('line_total', ascending=False).head(10)['vendor_name'].tolist()

# Now filter ALL transaction history to these Top 10 vendors
doc_data_top10 = doc_data[doc_data['vendor_name'].isin(top_vendors)]

# ------------------------
# 5. Forecast Next 4 Quarters (with success/failure tracking)
# ------------------------

forecast_results = []
successful_vendors = []
skipped_vendors = []

warnings.filterwarnings("ignore")

for vendor in top_vendors:
    vendor_data = doc_data_top10[doc_data_top10['vendor_name'] == vendor]
    vendor_quarterly = vendor_data.groupby('fiscal_year_quarter')['line_total'].sum().sort_index()

    if len(vendor_quarterly) < 4:
        skipped_vendors.append(vendor)
        continue

    forecasts = []
    temp_series = vendor_quarterly.copy()

    for _ in range(4):
        try:
            model = ExponentialSmoothing(temp_series, trend='add', seasonal='add', seasonal_periods=4)
            model_fit = model.fit()
            forecast = model_fit.forecast(1).iloc[0]
        except:
            forecast = temp_series.rolling(4, min_periods=1).mean().iloc[-1]

        forecasts.append(forecast)

        next_period = f"{int(temp_series.index[-1][:4]) + (1 if temp_series.index[-1][-1] == '4' else 0)}-Q{(int(temp_series.index[-1][-1]) % 4) + 1}"
        temp_series.loc[next_period] = forecast
        temp_series = temp_series.sort_index()

    forecast_results.append({
        'vendor_name': vendor,
        'forecast_q1_spend': forecasts[0],
        'forecast_q2_spend': forecasts[1],
        'forecast_q3_spend': forecasts[2],
        'forecast_q4_spend': forecasts[3]
    })
    
    successful_vendors.append(vendor)

# ------------------------
# 6. Print Forecast Status
# ------------------------

print("✅ Forecast completed!")
print(f"✅ {len(successful_vendors)} vendors had enough history to forecast:")
for v in successful_vendors:
    print(f"   - {v}")

print(f"⚠️ {len(skipped_vendors)} vendors did NOT have enough history and were skipped:")
for v in skipped_vendors:
    print(f"   - {v}")

# ------------------------
# 7. Build and Clean Forecast Table
# ------------------------

forecast_df = pd.DataFrame(forecast_results)

# 🚨 Clip negative forecasts to 0
forecast_df[['forecast_q1_spend', 'forecast_q2_spend', 'forecast_q3_spend', 'forecast_q4_spend']] = \
    forecast_df[['forecast_q1_spend', 'forecast_q2_spend', 'forecast_q3_spend', 'forecast_q4_spend']].clip(lower=0)

# ------------------------
# 8. Merge into vendor_view
# ------------------------

vendor_view = pd.read_sql("SELECT * FROM vendor_view", engine)

# Clean vendor names
vendor_view['vendor_name'] = vendor_view['vendor_name'].str.strip()
forecast_df['vendor_name'] = forecast_df['vendor_name'].str.strip()
vendor_spend_2024['vendor_name'] = vendor_spend_2024['vendor_name'].str.strip()

# Merge forecasts
vendor_view_updated = pd.merge(
    vendor_view,
    forecast_df,
    how='left',
    on='vendor_name'
)

# 🎯 NEW: Merge spend_ranking
vendor_view_updated = pd.merge(
    vendor_view_updated,
    vendor_spend_2024[['vendor_name', 'spend_ranking']],
    how='left',
    on='vendor_name'
)

# ------------------------
# 9. Calculate Total Forecasted Spend for Next Year
# ------------------------

forecast_cols = ['forecast_q1_spend', 'forecast_q2_spend', 'forecast_q3_spend', 'forecast_q4_spend']

if all(col in vendor_view_updated.columns for col in forecast_cols):
    vendor_view_updated['forecasted_total_spend_next_year'] = vendor_view_updated[forecast_cols].sum(axis=1, min_count=4)
else:
    print("⚠️ Warning: Forecast columns missing, cannot calculate total forecasted spend.")

# ------------------------
# 10. Save Updated vendor_view
# ------------------------

vendor_view_updated.to_sql(
    name='vendor_view',
    con=engine,
    if_exists='replace',
    index=False
)

print("✅ vendor_view updated successfully with quarterly forecasts + spend ranking (Top 10 vendors of FY2024)!")
