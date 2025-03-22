import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

# Load Excel file
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/MarchData.xlsx"  # Change this to your local file path
xls = pd.ExcelFile(file_path)

# Display available sheets
print(xls.sheet_names)

# Load the cleaned sheet
df = pd.read_excel(xls, sheet_name="cleaned")

# View first rows
print(df.head())

# Convert date columns to datetime format
date_columns = ["Requisition.Submitted.Date", "Requisition.Approved.Date", "Ordered.Date"]
for col in date_columns:
    df[col] = pd.to_datetime(df[col], errors='coerce')

# Compute Delays
df["Approval_Delay"] = (df["Requisition.Approved.Date"] - df["Requisition.Submitted.Date"]).dt.days
df["Fulfillment_Delay"] = (df["Ordered.Date"] - df["Requisition.Approved.Date"]).dt.days

# Define Cost Overrun
df["Cost_Overrun"] = df["Line.Total.Change"]

# Compute SWAM Compliance Violations
swam_columns = ["SWAM.Minority", "SWAM.Woman", "SWAM.Small", "SWAM.Micro.Business"]
df["SWAM_Compliance_Violations"] = df[swam_columns].sum(axis=1)

# Define Features (X) and Target (y)
X = df[["Approval_Delay", "Fulfillment_Delay", "Cost_Overrun", "SWAM_Compliance_Violations"]]

# Risk Score Formula: Delays measure vendor reliability, cost overrun measures financial impact, compliance measures ethical/legal risk
y = (0.3 * df["Approval_Delay"]) + \
    (0.3 * df["Fulfillment_Delay"]) + \
    (0.2 * df["Cost_Overrun"]) + \
    (0.2 * df["SWAM_Compliance_Violations"])  

# Train/Test Split (80% training, 20% testing)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Before Scaling:")
print(X_train.describe())  # Check original feature ranges

print(X.corrwith(y))

# 🚨 NEW: Normalize Features
scaler = StandardScaler()  # Standardization (mean=0, std=1)
X_train_scaled = scaler.fit_transform(X_train)  # Fit only on training data
X_test_scaled = scaler.transform(X_test)  # Transform test data using the same scaler

print("\nAfter Scaling:")
import numpy as np
print(pd.DataFrame(X_train_scaled, columns=X.columns).describe())  # Check scaled features

print(X.corrwith(y))


# Initialize and Train Model
model = RandomForestRegressor(n_estimators=100, random_state=3212025)
model.fit(X_train_scaled, y_train)  # Train with normalized data

# Make Predictions
y_pred = model.predict(X_test_scaled)  # Predict with normalized test data

# Calculate Evaluation Metrics
mae = mean_absolute_error(y_test, y_pred)
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)

# Print Evaluation Results
print(f"Mean Absolute Error (MAE): {mae}")
print(f"Mean Squared Error (MSE): {mse}")
print(f"R² Score: {r2}")

# Feature Importance Analysis
importances = model.feature_importances_
feature_importance_df = pd.DataFrame({"Feature": X.columns, "Importance": importances}).sort_values(by="Importance", ascending=False)
print("Feature Importances:\n", feature_importance_df)

print(df[["Approval_Delay", "Cost_Overrun"]].corr())

