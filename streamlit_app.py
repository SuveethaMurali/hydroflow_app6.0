import streamlit as st
import pandas as pd

st.title("🌧️ RunMeter – Runoff Estimation Web App")
st.write("Upload your input data file to calculate surface runoff using SCS CN or Strange Method.")

uploaded_file = st.file_uploader("📂 Upload CSV File", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file)
    st.success("✅ File uploaded successfully!")
    st.dataframe(data)

    method = st.radio("Select a Method:", ["SCS CN Method", "Strange Method"])

    if st.button("Calculate Runoff"):
        try:
            rainfall = data["Rainfall (mm)"]
            CN = data["Curve Number"]
            area = data["Area (sq.km)"]

            if method == "SCS CN Method":
                S = (25400 / CN) - 254
                Q = ((rainfall - 0.2 * S) ** 2) / (rainfall + 0.8 * S)
                runoff_volume = Q * area * 1000
                st.subheader("💦 Runoff Results (SCS CN Method)")
            else:
                runoff_volume = rainfall * area * 0.278  # simple Strange Method assumption
                Q = runoff_volume / area
                st.subheader("💦 Runoff Results (Strange Method)")

            result = pd.DataFrame({
                "Rainfall (mm)": rainfall.round(2),
                "Runoff (mm)": Q.round(2),
                "Runoff Volume (m³)": runoff_volume.round(2)
            })
            st.dataframe(result)

            csv = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Results as CSV",
                data=csv,
                file_name="runoff_results.csv",
                mime="text/csv"
            )
        except Exception as e:
            st.error(f"Error: {e}")
            st.warning("⚠️ Make sure CSV has columns: Rainfall (mm), Curve Number, Area (sq.km)")
else:
    st.info("👆 Upload a CSV file to start.")
