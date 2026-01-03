# app.py
import streamlit as st
import joblib
import pandas as pd

st.title("House Price Predictor")

model = joblib.load("RandomForestRegressor.pkl")

# Take manual inputs
MedInc = st.number_input("Median Income", min_value=0.0)
HouseAge = st.number_input("House Age", min_value=0.0)
AveRooms = st.number_input("Average Rooms", min_value=0.0)
AveBedrms = st.number_input("Average Bedrooms", min_value=0.0)
Population = st.number_input("Population", min_value=0.0)
AveOccup = st.number_input("Average Occupancy", min_value=0.0)
Latitude = st.number_input("Latitude", min_value=0.0)
Longitude = st.number_input("Longitude", min_value=0.0)

if st.button("Predict"):
    input_df = pd.DataFrame([[MedInc, HouseAge, AveRooms, AveBedrms, Population, AveOccup, Latitude, Longitude]],
                            columns=["MedInc", "HouseAge", "AveRooms", "AveBedrms", "Population", "AveOccup", "Latitude", "Longitude"])
    
    prediction = model.predict(input_df)[0]
    st.success(f"Estimated Price: ₹{prediction * 100000:.2f}")