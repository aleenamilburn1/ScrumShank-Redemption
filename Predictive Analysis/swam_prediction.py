
# swam_prediction.py

import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# --- File path to Excel data ---
file_path = '/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/MarchData.xlsx'  # Update path if needed

# --- Load the data ---
df = pd.read_excel(file_path)

# --- Create target variable (1 = any SWaM flag is set) ---
df['IsSWaM'] = df[['SWAM.Minority', 'SWAM.Woman', 'SWAM.Small', 'SWAM.Micro.Business']].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)

# --- Create local vendor flag ---
df['IsLocal'] = df['Vendor.Address.State'].apply(lambda x: 1 if str(x).strip().upper() == 'VA' else 0)

# --- Encode text features ---
le_cat = LabelEncoder()
le_trx = LabelEncoder()
df['Category_encoded'] = le_cat.fit_transform(df['NIGP.Description'].astype(str))
df['Transaction_encoded'] = le_trx.fit_transform(df['Procurement.Transaction.Desc'].astype(str))

# --- Train-test split ---
X = df[['Category_encoded', 'Transaction_encoded', 'IsLocal']]
y = df['IsSWaM']
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# --- Train model ---
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# --- Evaluate model ---
# Evaluate Model
y_pred = model.predict(X_test)
print("\n📊 Classification Report:\n", classification_report(y_test, y_pred))
print("\n🔢 Confusion Matrix:\n", confusion_matrix(y_test, y_pred))

from sklearn.metrics import classification_report

# Training set predictions
y_train_pred = model.predict(X_train)
print("\n📊 Training Set Classification Report:\n", classification_report(y_train, y_train_pred))


# --- Predict on all data for category analysis ---
df['SWaM_Predicted'] = model.predict(X)

category_summary = df.groupby('NIGP.Description').agg(
    Total=('SWaM_Predicted', 'count'),
    SWaM_Likely=('SWaM_Predicted', 'sum')
)
category_summary['Likelihood'] = category_summary['SWaM_Likely'] / category_summary['Total']
category_summary = category_summary.sort_values('Likelihood', ascending=False)

# --- Save to CSV for Tableau ---
category_summary.to_csv('swam_likelihood_by_category.csv')

print("\n✅ Export complete: swam_likelihood_by_category.csv")
