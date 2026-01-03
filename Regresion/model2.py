from sklearn.datasets import fetch_california_housing
from sklearn.tree import DecisionTreeRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, r2_score

data = fetch_california_housing(as_frame = True)

df = data.frame

X = df.drop("MedHouseVal", axis = 1)
y = df["MedHouseVal"]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)
tree_model = DecisionTreeRegressor(max_depth = 5, random_state =2)
tree_model.fit(X_train, y_train)
y_tree_pred = tree_model.predict(X_test)

tree_mse = mean_squared_error(y_test, y_tree_pred)
tree_r2 = r2_score(y_test, y_tree_pred)

print(f"MSE:{tree_mse}")
print(f"r2:{tree_r2}")
