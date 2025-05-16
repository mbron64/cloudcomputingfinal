#!/usr/bin/env python
"""
Beehive Monitoring Dashboard (Demo Version)
This version runs completely in demo mode without any cloud dependencies.
"""

import os
import json
import random
import pandas as pd
import numpy as np
import streamlit as st
import plotly.express as px
import datetime
from pathlib import Path
import sys

# Add parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Set page configuration
st.set_page_config(
    page_title="Beehive Monitoring Dashboard",
    page_icon="🐝",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom CSS for styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f7f2;
    }
    .st-emotion-cache-1n76uvr {
        background-color: #f8f7f2;
    }
    h1, h2 {
        color: #704214;
    }
    .highlight-box {
        background-color: #fcf6e8;
        border-left: 5px solid #f0c14b;
        padding: 0.5rem 1rem;
        margin: 1rem 0;
    }
    .bee-icon {
        font-size: 2rem;
    }
    </style>
    """, unsafe_allow_html=True)

# Sidebar header
st.sidebar.title("🐝 Beehive Monitor")
st.sidebar.markdown("---")
st.sidebar.info("DEMO MODE - No cloud connection required")

# Sample simulated data for demo mode
def generate_demo_data(num_records=10):
    """Generate random data for demo mode"""
    now = datetime.datetime.now()
    hives = [f"hive{i:03d}" for i in range(1, 6)]
    data = []
    
    for i in range(num_records):
        timestamp = now - datetime.timedelta(minutes=i*10)
        for hive in hives:
            behavior = random.choices(['normal', 'swarming', 'distress'], 
                                    weights=[0.85, 0.1, 0.05])[0]
            confidence = random.uniform(0.75, 0.98) if behavior == 'normal' else random.uniform(0.6, 0.85)
            
            # Generate frequencies data
            frequencies = {}
            for freq in range(120, 600, 30):
                base_value = 10
                # Higher frequencies for swarming
                if behavior == 'swarming' and freq > 300:
                    base_value = 30
                # Higher low frequencies for distress
                elif behavior == 'distress' and freq < 300:
                    base_value = 35
                
                frequencies[str(freq)] = base_value + random.uniform(-5, 5)
            
            # Create mock audio metrics
            audio_density = 25 + random.uniform(-5, 10) if behavior == 'swarming' else 10 + random.uniform(-2, 5)
            density_variation = 20 + random.uniform(-2, 15) if behavior == 'distress' else 5 + random.uniform(-1, 5)
            
            data.append({
                'timestamp': timestamp.isoformat(),
                'device_id': hive,
                'behavior': behavior,
                'confidence': confidence,
                'audio': {
                    'frequencies': frequencies,
                    'audio_density': audio_density,
                    'density_variation': density_variation
                },
                'temperature': 35 + random.uniform(-2, 2),
                'humidity': 45 + random.uniform(-5, 5)
            })
    
    df = pd.DataFrame(data)
    return df

def load_simulation_data():
    """Load data from the simulation_output directory"""
    data = []
    sim_dir = Path(__file__).parent.parent.parent / "simulation_output"
    
    if not sim_dir.exists():
        return pd.DataFrame()
    
    for file in sim_dir.glob("*.json"):
        try:
            with open(file, "r") as f:
                json_data = json.load(f)
                
                # The filename contains the behavior type
                behavior = file.stem.split("_")[-1]
                
                # Extract data
                data.append({
                    'timestamp': json_data['timestamp'],
                    'device_id': json_data['device_id'],
                    'behavior': behavior,
                    'confidence': 0.85,  # Simulated confidence
                    'audio': json_data['audio'],
                    'temperature': 35 + random.uniform(-2, 2),  # Simulated temp
                    'humidity': 45 + random.uniform(-5, 5)      # Simulated humidity
                })
        except Exception as e:
            st.warning(f"Error loading file {file}: {e}")
    
    if data:
        df = pd.DataFrame(data)
        return df
    else:
        return pd.DataFrame()

def get_data():
    """Get data from simulation output or generate demo data"""
    # Try to load simulation data, fall back to demo data
    df = load_simulation_data()
    if df.empty:
        df = generate_demo_data()
    return df

# Get data
df = get_data()

# Main content
st.title("Beehive Monitoring Dashboard")

# Show demo mode banner
st.warning("🔄 Running in DEMO mode with simulated data")

# Add a refresh button that re-runs the app
if st.button("Refresh Data"):
    st.rerun()
    
# Display current time
now = datetime.datetime.now()
st.markdown(f"### Last Updated: **{now.strftime('%Y-%m-%d %H:%M:%S')}**")

# Dashboard layout with metrics and charts
col1, col2, col3 = st.columns(3)

# Count hives by behavior
if not df.empty:
    behavior_counts = df.groupby('behavior')['device_id'].nunique().to_dict()
    total_hives = df['device_id'].nunique()
    
    # Make sure we have values for all behaviors
    for b in ['normal', 'swarming', 'distress']:
        if b not in behavior_counts:
            behavior_counts[b] = 0
    
    # Display metrics with appropriate colors and icons
    with col1:
        st.metric(
            "Normal Hives", 
            f"{behavior_counts['normal']} / {total_hives}",
            delta=None
        )
    
    with col2:
        st.metric(
            "Swarming Hives", 
            f"{behavior_counts['swarming']} / {total_hives}",
            delta=None,
            delta_color="off"
        )
    
    with col3:
        st.metric(
            "Distress Hives", 
            f"{behavior_counts['distress']} / {total_hives}",
            delta=None,
            delta_color="inverse"
        )

    # Display alerts for critical behaviors
    if behavior_counts['distress'] > 0:
        st.error(f"⚠️ ALERT: {behavior_counts['distress']} hives showing signs of distress!")
    
    if behavior_counts['swarming'] > 0:
        st.warning(f"⚠️ ALERT: {behavior_counts['swarming']} hives showing swarming behavior!")

# Main dashboard sections
st.markdown("---")

tab1, tab2, tab3 = st.tabs(["Overview", "Audio Analysis", "Behavior Trends"])

with tab1:
    st.header("Hive Status Overview")
    
    if not df.empty:
        # Create a status table
        status_df = df.drop_duplicates('device_id')[['device_id', 'behavior', 'confidence']]
        
        # Display as a styled table
        st.dataframe(
            status_df.style.apply(
                lambda x: ['background-color: #e6f7e6' if v == 'normal' 
                           else 'background-color: #fff7e6' if v == 'swarming'
                           else 'background-color: #f7e6e6' for v in x],
                axis=0, subset=['behavior']
            ).format({'confidence': '{:.2%}'}),
            use_container_width=True
        )
        
        # Chart showing hive behavior distribution
        fig = px.pie(status_df, names='behavior', title='Hive Behavior Distribution',
                    color='behavior', color_discrete_map={
                        'normal': '#4CAF50', 
                        'swarming': '#FF9800', 
                        'distress': '#F44336'})
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")

with tab2:
    st.header("Audio Frequency Analysis")
    
    if not df.empty:
        # Let user select a hive
        hives = sorted(df['device_id'].unique())
        selected_hive = st.selectbox("Select Hive", hives)
        
        # Filter to the selected hive's latest data
        hive_data = df[df['device_id'] == selected_hive].sort_values('timestamp').iloc[-1]
        
        # Extract and plot frequency data
        if 'audio' in hive_data and 'frequencies' in hive_data['audio']:
            freqs = hive_data['audio']['frequencies']
            freq_df = pd.DataFrame({
                'Frequency (Hz)': [float(k) for k in freqs.keys()],
                'Amplitude': [float(v) for v in freqs.values()]
            })
            
            fig = px.line(freq_df, x='Frequency (Hz)', y='Amplitude', 
                         title=f'Frequency Spectrum - {selected_hive}')
            fig.update_layout(xaxis_title='Frequency (Hz)', yaxis_title='Amplitude')
            st.plotly_chart(fig, use_container_width=True)
            
            # Show audio metrics
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Audio Density", f"{hive_data['audio'].get('audio_density', 0):.2f}")
            with col2:
                st.metric("Density Variation", f"{hive_data['audio'].get('density_variation', 0):.2f}")
        else:
            st.info("No audio frequency data available for this hive")
    else:
        st.info("No data available")

with tab3:
    st.header("Behavior Trends")
    
    if not df.empty:
        # Convert timestamp to datetime if it's a string
        if isinstance(df['timestamp'].iloc[0], str):
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Group by timestamp and behavior, count devices
        trend_data = df.groupby([pd.Grouper(key='timestamp', freq='h'), 'behavior']).size().reset_index(name='count')
        
        # Plot the trend
        fig = px.line(trend_data, x='timestamp', y='count', color='behavior',
                     title='Behavior Trends Over Time',
                     color_discrete_map={
                         'normal': '#4CAF50', 
                         'swarming': '#FF9800', 
                         'distress': '#F44336'
                     })
        fig.update_layout(xaxis_title='Time', yaxis_title='Number of Hives')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No data available")

# Sidebar - Configuration
st.sidebar.markdown("## Configuration")
refresh_rate = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 5)

# Add auto-refresh capability (client-side refresh)
if not st.sidebar.button("Pause Auto-refresh"):
    st.sidebar.success(f"Auto-refreshing every {refresh_rate} seconds")
    st.markdown(
        f"""
        <script>
            setTimeout(function(){{
                window.location.reload();
            }}, {refresh_rate * 1000});
        </script>
        """,
        unsafe_allow_html=True
    )
else:
    st.sidebar.info("Auto-refresh paused")

# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("### About")
st.sidebar.info(
    """
    This dashboard monitors beehives using IoT sensors and machine learning to detect abnormal behavior.
    """
)

# Show project info at the bottom
st.markdown("---")
st.markdown("### IoT Beehive Monitoring System")
st.markdown("👨‍💻 Cloud Computing Final Project")
st.info("This is a demo version that uses simulated data. The full version integrates with Google Cloud for real-time data processing.") 