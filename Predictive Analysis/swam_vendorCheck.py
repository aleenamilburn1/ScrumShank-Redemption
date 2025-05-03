import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.preprocessing import LabelEncoder

# 1. Load data
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/Predictive Analysis/doc_data_enriched.xlsx"
df = pd.read_excel(file_path)

# 2. Create binary target: IsSWaM
df['IsSWaM'] = df[['swam_minority', 'swam_woman', 'swam_small', 'swam_micro_business']].sum(axis=1).apply(lambda x: 1 if x > 0 else 0)

# 3. Feature engineering
df['IsLocal'] = df['vendor_address_state'].astype(str).str.strip().str.upper().apply(lambda x: 1 if x == 'VA' else 0)
df['Category_encoded'] = LabelEncoder().fit_transform(df['nigp_description'].astype(str))
df['Transaction_encoded'] = LabelEncoder().fit_transform(df['procurement_transaction_desc'].astype(str))

# 4. Setup features and target
X = df[['Category_encoded', 'Transaction_encoded', 'IsLocal']]
y = df['IsSWaM']

# 5. Check class distribution
print("📊 CLASS DISTRIBUTION (IsSWaM):")
print(y.value_counts())
print("-" * 50)

# 6. Split into train and test sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=42)

# 7. Train the model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# 8. Evaluate on test data
y_pred = model.predict(X_test)
print("🔍 TEST SET PERFORMANCE:")
print(classification_report(y_test, y_pred))
print("CONFUSION MATRIX (Test):")
print(confusion_matrix(y_test, y_pred))
print("-" * 50)

# 9. Evaluate on training data
y_train_pred = model.predict(X_train)
print("🧪 TRAIN SET PERFORMANCE:")
print(classification_report(y_train, y_train_pred))
print("CONFUSION MATRIX (Train):")
print(confusion_matrix(y_train, y_train_pred))
print("-" * 50)

# 10. Cross-validation
print("⏱️ CROSS-VALIDATION (5-FOLD):")
cv_scores = cross_val_score(model, X, y, cv=5)
print(f"Mean Accuracy: {cv_scores.mean():.4f}")
print(f"Standard Deviation: {cv_scores.std():.4f}")
print("All Fold Scores:", cv_scores)
print("-" * 50)

# 11. Feature importance
importances = model.feature_importances_
features = ['Category_encoded', 'Transaction_encoded', 'IsLocal']
print("🔎 FEATURE IMPORTANCE:")
for feature, score in zip(features, importances):
    print(f"{feature}: {score:.4f}")

# 12. Add predictions to DataFrame
df['SWaM_Predicted'] = model.predict(X)

# === MODEL PERFORMANCE SUMMARY (TEST SET) ===
# Accuracy: 88%
# Precision (Not SWaM): 0.91
# Recall (Not SWaM):    0.88
# Precision (SWaM):     0.83
# Recall (SWaM):        0.87
# F1 Score (SWaM):      0.85

# Confusion Matrix (Test):
# [[57139  7571]   → TN / FP
#  [ 5659 36437]]  → FN / TP
# → Correct Predictions: 57,139 + 36,437 = 93,576
# → Errors: 7,571 (false positives), 5,659 (false negatives)

# Interpretation:
# - Model captures 87% of all actual SWaM vendors (strong recall)
# - Predicts SWaM vendors with 83% precision (moderate false positive rate)
# - Confusion matrix shows balanced trade-offs, no overfitting detected

# === CROSS-VALIDATION (5-Fold) ===
# Mean Accuracy: 86.5%
# Standard Deviation: ±1.5%
# Fold Scores: [0.8570, 0.8831, 0.8684, 0.8778, 0.8407]
# → The model is stable across different subsets of the data.

# === FEATURE IMPORTANCE ===
# Category_encoded (NIGP Category):        91.8%
# Transaction_encoded (Procurement Type):  3.98%
# IsLocal (Virginia Vendor Flag):          4.27%

# → Product category is by far the strongest predictor of SWaM likelihood.

# Total rows: 356,019
# SWaM = 1: 140,425 (39.4%)
# SWaM = 0: 215,594 (60.6%)
# → No extreme imbalance, appropriate for Random Forest

