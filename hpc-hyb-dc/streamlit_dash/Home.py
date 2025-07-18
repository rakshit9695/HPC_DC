import sys
import os

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import math
import numpy as np
import time
import plotly.express as px
import altair as alt
import plotly.graph_objects as go

from streamlit_option_menu import option_menu

from Battery_Management import render_battery_page
from data_combine import wind_load_combi
from data_combine import solar_load_combi
from data_combine import energy_sum_profile

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
# Add root dir to sys.path
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

from src.hpp_core.hpc_dc_config import build_load_profile
WIND_FILE = "/Users/sarthak/Desktop/LHE Digitial Twin/Final_Implementation/hpc-hyb-dc/src/hpp_core/csv_files/wind_farm_hpc_max_output.csv"
SOLAR_FILE = "/Users/sarthak/Desktop/LHE Digitial Twin/Final_Implementation/hpc-hyb-dc/src/hpp_core/csv_files/solar_out.csv"

st.set_page_config(page_title="LHE Dashboard", layout="wide")

# Hide default Streamlit page navigation
st.markdown("""
    <style>
    [data-testid="stSidebarNav"] {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

# Sidebar with icon menu
with st.sidebar:

    st.markdown("""
        <h3 style='
        font-family: "Times New Roman", Times, serif;
        color: white;
        font-size: 30px;
        margin-top: -40px;
        margin-bottom: 30px;
    '>Navigation</h3>
                
    <hr style='
        border: 1px solid white;
        margin-top: -30px;
        margin-bottom: 100px;
    '>
    """, unsafe_allow_html=True)


    selected = option_menu(
        menu_title=None,
        options=["Home", "Battery Management", "Renewable Intake", "HPP Core", "Simulation Overview"],
        icons=["house", "battery-full", "sun", "cpu", "bar-chart-line"],
        default_index=0,
        styles={
            "container": {"padding": "10px", "background-color": "#000000"},
            "icon": {"color": "white", "font-size": "18px"},
            "nav-link": {"color": "white", "font-size": "16px", "text-align": "left", "margin": "5px 0"},
            "nav-link-selected": {"background-color": "#808080", "color": "#ffffff", "border-radius": "8px"},
        }
    )
    

# Main content
if selected == "Home":

    st.markdown("""
    <div style='
        padding: 20px;
        text-align: center;
        color: white;
        font-size: 60px;
        border-radius: 8px;
        margin-top: -70px; 
    '>
    Energy Dashboard
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 20px;'></div>", unsafe_allow_html=True)

    # Row 1: 30% and 70% boxes
    col11, col_divider1, col12 = st.columns([2.5,0.1,7.5])

    with col11:
        with st.container():
            # Parameters Heading
            st.markdown("""
                <h5 style='
                    font-family: "Segoe UI", sans-serif;
                    color: white;
                    margin-bottom: 1px;
                '>Parameters:</h5>
            """, unsafe_allow_html=True)   

            # Load value slider
            load_value = st.slider("Load Value (in MW)", min_value=1, max_value=10, value=5)

            #Wind and Solar farm inputs
            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            col111, col112 = st.columns(2)
            with col111: 
                # Windfrms input
                windfarms = st.number_input("Windfarms", min_value=1, max_value=100, step=1)
            with col112:
                # Solarfarms input
                solarfarms = st.number_input("Solarfarms", min_value=1, max_value=100, step=1)

            #Percentage ratio
            st.markdown("<div style='height: 25px;'></div>", unsafe_allow_html=True)
            farm_ratio = st.slider("Contribution Ratio", min_value=1, max_value=100, step=1, value=50)
            col121, col122 = st.columns(2)
            with col121: 
                st.markdown(
                f"<div style='margin-top: -10px; font-size: 12px; color: #11fbf4;'>Windfarm: <b>{farm_ratio}</b>%</div>",
                unsafe_allow_html=True
                )
            with col122:
                st.markdown(
                f"<div style='margin-top: -10px; font-size: 12px; color: #fb3a11 ; text-align: right; '>Solarfarm: <b>{100-farm_ratio}%</b></div>",
                unsafe_allow_html=True
                )

    with col_divider1:
        st.markdown("""
            <div style='
                border-left: 2px solid #ccc;
                height: 400px;
                margin: auto;
            '></div>
        """, unsafe_allow_html=True)

    #Represents the load graph
    with col12:
        # Build the profile and save to CSV
        profile_df = build_load_profile(load_value)
        filename = f"dc_{int(load_value)}MW_load_profile.csv"
        profile_df.to_csv(filename, index=False)

        #Loading the load csv file.
        load_df = pd.read_csv(filename)
        load_df["Timestamp"] = pd.to_datetime(load_df["Timestamp"])
        load_df["Time"] = load_df["Timestamp"].dt.strftime("%H:%M")

        #Loading the wind file 
        load_df["Timestamp"] = pd.to_datetime(load_df["Timestamp"])

        #Combining wind and load file 
        wind_load_df = wind_load_combi(load_df, farm_ratio*0.01, windfarms)

        #Combining Solar file
        solar_load_df = solar_load_combi(wind_load_df, farm_ratio*0.01, solarfarms)

        #Getting net Energy profile
        net_output_df = energy_sum_profile(solar_load_df)

        plot_df = net_output_df[["Time", "Load_MW", "wind_output", "solar_output", "net_output"]].copy()
        plot_df = plot_df.set_index("Time")

        st.subheader("⚡︎ Energy Required v/s Renewables Output")

        # Create a Plotly line chart with Load_kW and wind_output
        fig = go.Figure()

        fig.add_trace(go.Scatter(
            x=net_output_df["Time"],
            y=net_output_df["Load_MW"],
            mode='lines',
            name='Load (MW)',
            line=dict(color='blue')
        ))

        fig.add_trace(go.Scatter(
            x=net_output_df["Time"],
            y=net_output_df["wind_output"],
            mode='lines',
            name='Wind Output (MW)',
            line=dict(color='white')
        ))

        fig.add_trace(go.Scatter(
            x=net_output_df["Time"],
            y=net_output_df["solar_output"],
            mode='lines',
            name='Solar Output (MW)',
            line=dict(color='red')
        ))

        fig.add_trace(go.Scatter(
            x=net_output_df["Time"],
            y=net_output_df["net_output"],
            mode='lines',
            name='Net Output (MW)',
            line=dict(color='green')
        ))

        fig.update_layout(
            xaxis_title='Time',
            yaxis_title='Power (MW)',
            legend=dict(orientation="h", y=1.1, x=0),
            height=400,
            template='plotly_white',
            margin=dict(l=20, r=20, t=30, b=20)
        )

        st.plotly_chart(fig, use_container_width=True)

        st.markdown("</div>", unsafe_allow_html=True)


    # Row 2: 50% and 50% boxes
    col21, col_divider2, col22 = st.columns([5,0.1,5])

    with col21:
        st.subheader("✇ Wind Output Profile")

        # Load wind CSV
        wind_df = pd.read_csv(WIND_FILE)
        wind_df["Timestamp"] = pd.to_datetime(wind_df["Timestamp"])
        wind_df["Time"] = wind_df["Timestamp"].dt.strftime("%H:%M")

        # Auto-detect the wind column
        wind_col = next((col for col in wind_df.columns if "HPC_Max_MW" in col), None)
        if wind_col is None:
            st.error("⚠️ Could not find wind power column in file.")
        else:
            # Rename and scale based on number of windfarms
            wind_df["Wind_MW"] = wind_df[wind_col] * windfarms

            # Plot
            st.line_chart(wind_df.set_index("Time")["Wind_MW"])  

    with col_divider2: 
        st.markdown("""
            <div style='
                border-left: 2px solid #ccc;
                height: 400px;
                margin: auto;
            '></div>
        """, unsafe_allow_html=True)

    with col22:     
        st.subheader("☀︎ Solar Output Profile")

        # Load wind CSV
        solar_df = pd.read_csv(SOLAR_FILE)
        solar_df["Timestamp"] = pd.to_datetime(solar_df["Timestamp"])
        solar_df["Time"] = solar_df["Timestamp"].dt.strftime("%H:%M")

        # Auto-detect the wind column
        solar_col = next((col for col in solar_df.columns if "AC_kW" in col), None)
        if wind_col is None:
            st.error("⚠️ Could not find solar power column in file.")
        else:
            # Rename and scale based on number of windfarms
            solar_df["Solar_MW"] = solar_df[solar_col] * solarfarms * 0.001

            # Plot
            st.line_chart(solar_df.set_index("Time")["Solar_MW"]) 

elif selected == "Battery Management":
    render_battery_page()