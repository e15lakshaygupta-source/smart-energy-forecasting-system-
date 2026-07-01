import pandas as pd
from sklearn.linear_model import LinearRegression
import joblib

data = pd.read_csv("energy.csv")

X = data[['Hour']]
y = data['Consumption']

model = LinearRegression()
model.fit(X, y)

joblib.dump(model, "energy_model.pkl")

print("Model Trained Successfully")