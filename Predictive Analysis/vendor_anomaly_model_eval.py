import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from collections import Counter

# === Load your cleaned anomaly dataset ===
df = pd.read_csv("/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/vendor_anomalies.csv")

# --- 1. Visual Comparison: Boxplots ---
def boxplot_compare(feature):
    plt.figure(figsize=(8, 5))
    sns.boxplot(data=df, x='is_anomaly', y=feature)
    plt.title(f'Boxplot of {feature} by Anomaly Flag')
    plt.xlabel("Is Anomaly")
    plt.ylabel(feature)
    plt.savefig(f"{feature}_anomaly_boxplot.png")
    print(f"📊 Saved boxplot: {feature}_anomaly_boxplot.png")

for col in ['total_spend', 'mean_approval_delay', 'mean_fulfillment_delay']:
    boxplot_compare(col)

# --- 2. Consistency: Vendors with Multiple Anomalies ---
vendor_counts = df[df['is_anomaly'] == True]['vendor_name'].value_counts()
multi_year_anomalies = vendor_counts[vendor_counts > 1]
print("\n📌 Vendors flagged as anomalies in multiple years:")
print(multi_year_anomalies)

# --- 3. Sensitivity Check: Multiple Contamination Levels ---
contamination_rates = [0.03, 0.05, 0.1]
anomaly_sets = {}

features = df[[
    'total_spend', 'num_transactions', 'num_categories',
    'mean_approval_delay', 'mean_fulfillment_delay'
]]
scaler = StandardScaler()
X_scaled = scaler.fit_transform(features)

for rate in contamination_rates:
    model = IsolationForest(n_estimators=100, contamination=rate, random_state=42)
    preds = model.fit_predict(X_scaled)
    anomalies = df[preds == -1]['vendor_name'].tolist()
    anomaly_sets[rate] = anomalies
    print(f"\n🔁 Contamination {rate:.2f}: {len(anomalies)} anomalies")

# --- Find Vendors Repeatedly Flagged ---
all_anomalies = anomaly_sets[0.03] + anomaly_sets[0.05] + anomaly_sets[0.1]
repeat_vendors = [vendor for vendor, count in Counter(all_anomalies).items() if count > 1]
repeat_df = pd.DataFrame(repeat_vendors, columns=['vendor_name'])
repeat_df.to_csv("repeat_anomalies_summary.csv", index=False)
print("\n✅ Vendors repeatedly flagged (>=2 models) saved to: repeat_anomalies_summary.csv")
