import streamlit as st
import folium
from streamlit_folium import st_folium

st.subheader("🌍 Location Map (optional)")
lat = st.number_input("Enter Latitude:", value=13.0827, format="%.4f")
lon = st.number_input("Enter Longitude:", value=80.2707, format="%.4f")

m = folium.Map(location=[lat, lon], zoom_start=12)
folium.Marker([lat, lon], tooltip="Runoff Location").add_to(m)
st_folium(m, width=700, height=400)
