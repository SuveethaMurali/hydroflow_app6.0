import streamlit as st
import folium
from streamlit_folium import st_folium
import requests
from datetime import datetime

# ---------------- Page Configuration ----------------
st.set_page_config(page_title="RunMeter - Runoff Estimation", page_icon="🌧️", layout="wide")

# ---------------- Helpers ----------------
@st.cache_data(ttl=300)
def ip_lookup():
    """Return (city, lat, lon) using IP geolocation. Falls back to India centroid if it fails."""
    try:
        r = requests.get("https://ipinfo.io/json", timeout=8)
        if r.ok:
            data = r.json()
            city = data.get("city") or "Unknown"
            loc = (data.get("loc") or "20,0").split(",")
            lat, lon = float(loc[0]), float(loc[1])
            return city, lat, lon
    except Exception:
        pass
    # Fallback: India approx center
    return "India", 21.0, 78.0

@st.cache_data(ttl=300)
def geocode_city(city: str, api_key: str):
    """Use OpenWeatherMap geocoding to resolve a city to (lat, lon, display_name)."""
    try:
        url = (
            "https://api.openweathermap.org/geo/1.0/direct"
            f"?q={requests.utils.quote(city)}&limit=1&appid={api_key}"
        )
        r = requests.get(url, timeout=8)
        if r.ok and len(r.json()) > 0:
            d = r.json()[0]
            name_parts = [d.get("name"), d.get("state"), d.get("country")]
            display = ", ".join([p for p in name_parts if p])
            return float(d["lat"]), float(d["lon"]), display
    except Exception:
        pass
    return None

@st.cache_data(ttl=180)
def get_weather(lat: float, lon: float, api_key: str, units: str = "metric"):
    """Fetch current weather for given coords from OpenWeatherMap Current Weather API."""
    url = (
        "https://api.openweathermap.org/data/2.5/weather"
        f"?lat={lat}&lon={lon}&appid={api_key}&units={units}"
    )
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    data = r.json()
    # Extract rainfall (mm) in last 1h or 3h if present
    rain_1h = None
    rain_3h = None
    if isinstance(data.get("rain"), dict):
        rain_1h = data["rain"].get("1h")
        rain_3h = data["rain"].get("3h")
    # Pick an icon/emoji based on weather id
    weather_main = (data.get("weather") or [{}])[0].get("main", "")
    emoji = {
        "Thunderstorm": "⛈️",
        "Drizzle": "🌦️",
        "Rain": "🌧️",
        "Snow": "❄️",
        "Clear": "☀️",
        "Clouds": "☁️",
        "Mist": "🌫️",
        "Smoke": "🌫️",
        "Haze": "🌫️",
        "Dust": "🌫️",
        "Fog": "🌫️",
        "Sand": "🌫️",
        "Ash": "🌫️",
        "Squall": "🌬️",
        "Tornado": "🌪️",
    }.get(weather_main, "🌍")

    return {
        "name": data.get("name"),
        "temp": data.get("main", {}).get("temp"),
        "feels_like": data.get("main", {}).get("feels_like"),
        "humidity": data.get("main", {}).get("humidity"),
        "pressure": data.get("main", {}).get("pressure"),
        "wind": data.get("wind", {}).get("speed"),
        "weather": weather_main,
        "desc": (data.get("weather") or [{}])[0].get("description", "").title(),
        "rain_1h": rain_1h,
        "rain_3h": rain_3h,
        "dt": data.get("dt"),
        "emoji": emoji,
    }

# Try to read the API key from Streamlit secrets first
OWM_KEY = None
try:
    OWM_KEY = st.secrets["openweather"]["api_key"]
except Exception:
    # Optional fallback to environment variable if user prefers
    OWM_KEY = None

# ---------------- Sidebar Navigation ----------------
st.sidebar.markdown("### 🧭 Navigation")
st.sidebar.write("🏠 Home")
st.sidebar.button("📘 Method Selection")
st.sidebar.button("🌀 SCN Method")
st.sidebar.button("📈 Strangers Method")
st.sidebar.button("📊 Runoff Result")


with st.sidebar.expander("⚙️ Weather Settings", expanded=True):
    units = st.radio("Units", ["metric", "imperial"], index=0, horizontal=True, help="Metric = °C, km/h; Imperial = °F, mph")
    use_auto = st.toggle("Auto-detect location via IP", value=True)
    city_query = st.text_input("Or search city", placeholder="e.g., Chennai")
    refresh = st.button("🔄 Refresh Weather")

# ---------------- Layout: Columns ----------------
col1, col2 = st.columns([1, 2], gap="large")

# ----------- Left Column: Live Map -------------
with col1:
    st.markdown("### 🌍 Live Global Map")
    st.write("View real-time geographical reference using OpenStreetMap.")

    # Determine target location
    target_city = None
    lat, lon = 20.0, 0.0

    if city_query.strip() and OWM_KEY:
        geo = geocode_city(city_query.strip(), OWM_KEY)
        if geo:
            lat, lon, target_city = geo
        else:
            st.info("Couldn't resolve that city. Falling back to IP location…")

    if (not city_query.strip()) or (not target_city):
        # Use IP lookup as default
        ip_city, ip_lat, ip_lon = ip_lookup()
        lat, lon = ip_lat, ip_lon
        target_city = target_city or ip_city

    # Initialize Folium map centered on target
    world_map = folium.Map(location=[lat, lon], zoom_start=6 if target_city else 2)
    folium.TileLayer('cartodb positron').add_to(world_map)

    folium.Marker(
        location=[lat, lon],
        popup=f"{target_city} (lat {lat:.3f}, lon {lon:.3f})",
        tooltip="Selected / Detected Location",
    ).add_to(world_map)
    folium.Circle(location=[lat, lon], radius=15000, fill=True, opacity=0.2).add_to(world_map)

    st_data = st_folium(world_map, width=420, height=420)

# ----------- Right Column: App Description + Live Weather -------------
with col2:
    st.title("🌧️ RunMeter — Runoff Estimation Web App")
    st.markdown("---")

    st.subheader("💡 About RunMeter")
    st.write(
        """
        **RunMeter** is an intelligent web application that estimates surface runoff
        using two widely accepted hydrological models:
        - **SCS Curve Number (CN) Method**
        - **Stranger’s Method**

        The app simplifies runoff estimation by allowing users to input rainfall data manually
        or through a CSV file, automatically generating **hydrographs**, **discharge tables**, and **runoff volumes**.
        """
    )

    st.markdown("---")
    st.subheader("🧭 How It Works")
    st.markdown(
        """
        1. Choose the desired estimation method.  
        2. Upload or input your rainfall and catchment data.  
        3. The system calculates runoff and displays graphs and tables instantly.  
        4. All results can be saved for future comparison.  
        """
    )

    st.markdown("---")
    st.subheader("🌦️ Live Weather & Rainfall")
    if not OWM_KEY:
        st.error(
            "OpenWeatherMap API key not found. Add it in **.streamlit/secrets.toml** under `[openweather] api_key = "
            "\"YOUR_KEY\"` to enable live weather.")
    else:
        try:
            wx = get_weather(lat, lon, OWM_KEY, units=units)
            last_updated = datetime.utcfromtimestamp(wx["dt"]).strftime("%Y-%m-%d %H:%M UTC") if wx.get("dt") else "—"

            colA, colB, colC, colD = st.columns(4)
            with colA:
                st.metric(label=f"Temperature {wx['emoji']}", value=f"{wx['temp']:.1f}°{'C' if units=='metric' else 'F'}",
                          delta=f"Feels {wx['feels_like']:.1f}°")
            with colB:
                st.metric(label="Humidity", value=f"{wx['humidity']}%")
            with colC:
                rain_val = wx.get("rain_1h") if wx.get("rain_1h") is not None else (wx.get("rain_3h") if wx.get("rain_3h") is not None else None)
                rain_label = "Rain (1h)" if wx.get("rain_1h") is not None else ("Rain (3h)" if wx.get("rain_3h") is not None else "Rain")
                st.metric(label=rain_label, value=f"{rain_val:.2f} mm" if rain_val is not None else "—")
            with colD:
                st.metric(label="Wind", value=f"{wx['wind']} {'m/s' if units=='metric' else 'mph'}")

            st.caption(f"{wx['weather']} · {wx['desc']} · Updated: {last_updated}")
            if refresh:
                st.cache_data.clear()
                st.rerun()
        except Exception as e:
            st.warning("Couldn't fetch live weather right now. Please try Refresh.")

    st.markdown("---")
    st.subheader("👩‍💻 Developed By")
    st.markdown(
        """
        - **Suveetha M**  
        - **Vishnu Sri M**  
        - **Sangeetha R**  
        Under the guidance of **[Your Guide’s Name]**  
        Department of Civil Engineering, [Your College Name]
        """
    )

    if st.button("➡️ Proceed to Method Selection"):
        st.switch_page("pages/1_Method_Selection.py")
