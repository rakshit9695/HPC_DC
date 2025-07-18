import streamlit as st
import pandas as pd

def render_battery_page():
    st.markdown("""
        <h1 style='
            text-align: center;
            font-size: 48px;
            font-weight: bold;
            font-family: "Segoe UI", "Times New Roman", serif;
        '>Battery Management</h1>
        <hr style='border: 1px solid #ccc; margin-top: 10px; margin-bottom: 30px;'>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)
    col1.metric("Battery Health", "92%", "▲ 1.2%")
    col2.metric("Charge Level", "76%", "▼ 4%")
    col3.metric("Temperature", "34°C", "▲ 2°C")

    st.markdown("---")

    st.subheader("📈 Charge History (Past 7 Days)")
    data = {
        "Day": ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
        "Charge %": [80, 85, 82, 78, 75, 77, 76]
    }
    df = pd.DataFrame(data)
    st.line_chart(df.set_index("Day"))

    st.markdown("### ⚙️ Battery Controls")
    mode = st.radio("Select Battery Mode", ["Performance", "Balanced", "Eco"])
    toggle = st.checkbox("Enable Auto-Discharge Protection", value=True)

    if toggle:
        st.success("Auto-discharge protection is ON.")
    else:
        st.warning("Auto-discharge protection is OFF.")

    st.button("Run Diagnostics 🔍")