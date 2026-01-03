from sklearn.datasets import fetch_california_housing
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

data = fetch_california_housing(as_frame = True)
df = data.frame
#print(df.head)

X = df.drop('MedHouseVal', axis = 1)
y = df['MedHouseVal']

X_train,X_test,y_train,y_test = train_test_split(X, y, test_size = 0.2, random_state = 42)
model = LinearRegression()
model.fit(X_train,y_train)

y_pred  = model.predict(X_test)
mse = mean_squared_error(y_test,y_pred)
r2 = r2_score(y_test, y_pred)

sample = X_test.iloc[0:1]
predicted_price = model.predict(sample)


print(f"Mean squared error: {mse}")
print(f"R-squared score:{r2}")

print(f"Predicted house price: {predicted_price[0]:.2f}")