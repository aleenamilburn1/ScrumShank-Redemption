from sklearn.conftest import fetch_california_housing
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
from sklearn.tree import plot_tree
import matplotlib.pyplot as plt


# load the California Housing dataset
california = fetch_california_housing()


# separate the features and target variable
X = california.data
y = california.target


# split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)


# create the random forest regressor with 10 decision trees
regressor = RandomForestRegressor(n_estimators=10, max_depth=5, random_state=42)


# fit the model on the training data
regressor.fit(X_train, y_train)


# make predictions on the testing data
y_pred = regressor.predict(X_test)


# calculate the mean squared error of the predictions
mse = mean_squared_error(y_test, y_pred)


print("Mean squared error:", mse)


# (optional) 
# plot each decision trees in the random forest seperately 
for i, estimator in enumerate(regressor.estimators_):
    plt.figure(figsize=(20,10))
    plot_tree(estimator, filled=True, rounded=True, feature_names=california.feature_names)
    plt.title(f"Decision Tree {i+1}")
    plt.show()