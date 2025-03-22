import pandas as pd
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
import matplotlib.pyplot as plt

# 1. Read in the data
df = pd.read_excel("MarchData.xlsx")

# 2. Convert date columns to datetime
df["Requisition.Submitted.Date"] = pd.to_datetime(df["Requisition.Submitted.Date"])
df["Requisition.Approved.Date"] = pd.to_datetime(df["Requisition.Approved.Date"])
df["Ordered.Date"] = pd.to_datetime(df["Ordered.Date"])

# 3. Calculate Approval and Fulfillment Delays (in days)
df["Approval.Delay"] = (df["Requisition.Approved.Date"] - df["Requisition.Submitted.Date"]).dt.days
df["Fulfillment.Delay"] = (df["Ordered.Date"] - df["Requisition.Approved.Date"]).dt.days

swam_columns = ["SWAM.Minority", "SWAM.Woman", "SWAM.Small", "SWAM.Micro.Business"]
df["SWAM_Compliance"] = df[swam_columns].sum(axis=1)

# 4. Exclude columns not needed for clustering
exclude_cols = [
    "NIGP..",
    "Order.Line.Number",
    "Quantity.Ordered",
    "Line.Total",
    "Requisition.Submitted.Date",
    "Requisition.Approved.Date",
    "Ordered.Date"
]
df.drop(columns=exclude_cols, inplace=True, errors='ignore')

# 5. One-hot encode the Order.Status column
#    This creates separate columns for each unique status (e.g., Status_Canceled, Status_Ordered, etc.)
df = pd.get_dummies(df, columns=["Order.Status"], prefix="Status")

# 6. Select the features for clustering
features = [
    "Unit.Price",
    "Line.Total.Change",
    "Approval.Delay",
    "Fulfillment.Delay",
    "Status_Canceled",
    "Status_Ordered",
    "Status_Received",
    "Status_Receiving",
    "SWAM_Compliance",
    "SWAM.Minority",
    "SWAM.Woman",
    "SWAM.Small",
    "SWAM.Micro.Business"
]
X = df[features].copy()

# 7. Handle missing values (if any)
X.dropna(inplace=True)

# 8. Scale the data
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# 9. (Optional) Use the Elbow method to check inertia across k values
inertia_values = []
k_values = range(2, 10)
for k in k_values:
    kmeans_test = KMeans(n_clusters=k, n_init=10, random_state=42)
    kmeans_test.fit(X_scaled)
    inertia_values.append(kmeans_test.inertia_)

plt.figure(figsize=(6, 4))
plt.plot(k_values, inertia_values, marker='o')
plt.title("Elbow Method for Optimal k")
plt.xlabel("Number of clusters (k)")
plt.ylabel("Inertia")
plt.show()  # Close the plot window to continue execution

# 10. Choose k=4 based on analysis
optimal_k = 4

# 11. Fit K-Means with k=4
kmeans = KMeans(n_clusters=optimal_k, n_init=10, random_state=42)
kmeans.fit(X_scaled)

# 12. Assign cluster labels back to the DataFrame
df["Cluster"] = kmeans.labels_

# 13. Inspect results
print("First 10 rows of the DataFrame with cluster labels:")
print(df.head(10))
print("\nCluster counts:")
print(df["Cluster"].value_counts())

# 14. Analyze each cluster's characteristics
cluster_analysis = df.groupby("Cluster")[features].mean()
print("\nCluster Analysis (mean values per feature):")
pd.set_option('display.max_columns', None)

# Now print the cluster analysis
print(cluster_analysis)

