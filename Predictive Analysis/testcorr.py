import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load Excel file
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/MarchData.xlsx"
xls = pd.ExcelFile(file_path)

# Load the cleaned sheet
df = pd.read_excel(xls, sheet_name="cleaned")

# Convert date columns to datetime format
date_columns = ["Requisition.Submitted.Date", "Requisition.Approved.Date", "Ordered.Date"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Compute Approval Delay
df["Approval_Delay"] = (df["Requisition.Approved.Date"] - df["Requisition.Submitted.Date"]).dt.days

# Define Cost Overrun and Apply Log Transformation
df["Log_Cost_Overrun"] = np.log1p(df["Cost_Overrun"].abs()) * np.sign(df["Cost_Overrun"])

# 🚨 Define the updated feature set (X) - Using only Approval_Delay & Log-transformed Cost Overrun
X = df[["Approval_Delay", "Log_Cost_Overrun"]]

# 🚨 Adjusted Risk Score Formula (Balanced Weight)
y = (0.60 * df["Approval_Delay"]) + \
    (0.40 * df["Log_Cost_Overrun"]) + \
    np.random.normal(0, 0.1, size=len(df))  # Small noise to improve generalization

# Train/Test Split (70% training, 30% testing for better evaluation)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# Normalize Features (Ensures Balanced Contribution)
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# 🚨 Train Model with Reduced Complexity to Avoid Overfitting
model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=3212025)
model.fit(X_train_scaled, y_train)

# Make Predictions
y_pred = model.predict(X_test_scaled)

# Evaluate Model
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

print(f"Mean Absolute Error (MAE): {mae}")
print(f"Mean Squared Error (MSE): {mse}")
print(f"R² Score: {r2}")

# Feature Importance Analysis
importances = model.feature_importances_
feature_importance_df = pd.DataFrame({"Feature": X.columns, "Importance": importances}).sort_values(by="Importance", ascending=False)

print("\nFeature Importances:")
print(feature_importance_df)
