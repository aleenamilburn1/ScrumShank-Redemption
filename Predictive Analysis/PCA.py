import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler

# Load Excel file
file_path = "/Users/aleenamilburn/Desktop/2024-2025 Classes/2025/IS Capstone/ScrumShank-Redemption/MarchData.xlsx"
df = pd.read_excel(file_path)

# Optional: Print column names
print("Columns in dataset:", df.columns)

# Keep only numeric columns
numeric_df = df.select_dtypes(include=[np.number])

# Fill missing values with column means
numeric_df = numeric_df.fillna(numeric_df.mean())

# Standardize the data
scaler = StandardScaler()
scaled_data = scaler.fit_transform(numeric_df)

# Run PCA
pca = PCA()
pca_components = pca.fit_transform(scaled_data)

# Explained variance
print("Explained variance ratio by component:")
for i, ratio in enumerate(pca.explained_variance_ratio_):
    print(f"PC{i+1}: {ratio:.4f}")

# Create a DataFrame with first two principal components
pca_df = pd.DataFrame(data=pca_components[:, :2], columns=["PC1", "PC2"])

# Plot the first two principal components
plt.figure(figsize=(8, 6))
plt.scatter(pca_df["PC1"], pca_df["PC2"], alpha=0.7)
plt.xlabel("Principal Component 1")
plt.ylabel("Principal Component 2")
plt.title("PCA - First 2 Principal Components")
plt.grid(True)
plt.tight_layout()
plt.show()
