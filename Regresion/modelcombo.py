import pandas as pd
import joblib
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.tree import DecisionTreeRegressor
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.datasets import fetch_california_housing


data = fetch_california_housing(as_frame = True)
df = data.frame

X = df.drop("MedHouseVal", axis = 1)
y = df["MedHouseVal"]

X_train,X_test,y_train, y_test = train_test_split(X,y, test_size = 0.2, random_state = 42)

Lin_model = LinearRegression()
tree_model = DecisionTreeRegressor()
rf_model = RandomForestRegressor(n_estimators = 100, random_state = 42)

Lin_model.fit(X_train, y_train)
tree_model.fit(X_train,y_train)
rf_model.fit(X_train, y_train)

y_Line_pred = Lin_model.predict(X_test)
y_tree_pred = tree_model.predict(X_test)
y_rf_pred = rf_model.predict(X_test)

joblib.dump(Lin_model, "LinearRegressor.pkl")
joblib.dump(tree_model, "DecisionTreeRegressor.pkl")
joblib.dump(rf_model, "RandomForestRegressor.pkl")

Lin_mse = mean_squared_error(y_test, y_Line_pred)
Lin_r2 = r2_score(y_test, y_Line_pred)

tree_mse = mean_squared_error(y_test, y_tree_pred)
tree_r2 = r2_score(y_test, y_tree_pred)

rf_mse = mean_squared_error(y_test, y_rf_pred)
rf_r2 = r2_score(y_test,y_rf_pred)

print(f"Tree Mse:{tree_mse:.3f}, Lin_mse:{Lin_mse:.3f}, RF MSE:{rf_mse:.3f}")
print(f"Tree r2:{tree_r2:.3f}, Lin r2:{Lin_r2:.3f}, RF r2:{rf_r2:.3f}")

plt.figure(figsize=(8,6))
plt.scatter(y_test,y_Line_pred,label= "Linear Regression", alpha=0.6)
plt.scatter(y_test, y_tree_pred, label = "Decision regressor", alpha = 0.4)
plt.scatter(y_test,y_rf_pred, label = "Random Forest Regressor", alpha = 0.4)
plt.xlabel("Actual Prices")
plt.ylabel("Predicted Prices")
plt.title("Actual vs Predicted House Prices")
plt.legend()
plt.grid(True)
plt.show()