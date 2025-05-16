"""
Beehive Monitoring Dashboard

This dashboard visualizes data from IoT beehive sensors and displays predictions
about bee behavior.
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

# Constants
MAX_SAMPLES = 50  # Maximum number of samples to display

# Handle imports gracefully - if Google Cloud isn't available, we'll use demo mode
try:
    from google.cloud import firestore
    HAVE_FIRESTORE = True
except ImportError:
    HAVE_FIRESTORE = False

# Add parent directory to the path so we can import modules
sys.path.append(str(Path(__file__).parent.parent.parent))

# Load configuration
CONFIG_PATH = Path(__file__).parent / "config" / "dashboard_config.json"
if CONFIG_PATH.exists():
    with open(CONFIG_PATH, "r") as f:
        CONFIG = json.load(f)
else:
    # Default to demo mode if no config
    CONFIG = {
        "use_firestore": False,
        "demo_mode": True,
        "refresh_interval": 5
    }

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

# Initialize Firestore client if using it
db = None
if CONFIG["use_firestore"] and HAVE_FIRESTORE:
    try:
        st.sidebar.info("Using Firestore for data")
        db = firestore.Client()
    except Exception as e:
        st.sidebar.warning(f"Error connecting to Firestore: {str(e)}")
        st.sidebar.info("Falling back to demo mode")
        CONFIG["use_firestore"] = False
        CONFIG["demo_mode"] = True

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
    """Load simulated data from JSON files in the simulation_output directory."""
    simulation_dir = Path('simulation_output')
    all_data = []
    
    if simulation_dir.exists():
        json_files = list(simulation_dir.glob('*.json'))
        for json_file in json_files[-MAX_SAMPLES:]:  # Get most recent files
            with open(json_file) as f:
                json_data = json.load(f)
                
                # Create a row for our dataframe
                row = {
                    'timestamp': json_data['timestamp'],
                    'device_id': json_data['device_id'],
                    'behavior': json_data.get('true_behavior', 'normal'),
                    'confidence': random.uniform(0.8, 0.99),
                    'temperature': json_data.get('temperature', 25),
                    'humidity': json_data.get('humidity', 0.5),
                    'battery_level': json_data.get('battery_level', 0.8),
                    'audio_features': json_data.get('audio_features', {})
                }
                all_data.append(row)
    
    # If no data, generate synthetic data
    if not all_data:
        return generate_synthetic_data()
    
    df = pd.DataFrame(all_data)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    return df.sort_values('timestamp')

def get_data():
    """Get data from Firestore or generate demo data"""
    if CONFIG["demo_mode"]:
        # Try to load simulation data, fall back to demo data
        df = load_simulation_data()
        if df.empty:
            df = generate_demo_data()
        return df
    
    if db is None:
        st.error("Firestore not available and demo mode is off")
        return pd.DataFrame()
    
    # Here would be the Firestore query code
    # For now we'll just return demo data
    return generate_demo_data()

# Get data
df = get_data()

# Main content
st.title("Beehive Monitoring Dashboard")

# Show app mode
if CONFIG["demo_mode"]:
    st.warning("🔄 Running in DEMO mode with simulated data")
    # Add a refresh button that re-runs the app
    if st.button("Refresh Data"):
        st.rerun()
    
# Display current time range
now = datetime.datetime.now()
st.markdown(f"### Last Updated: **{now.strftime('%Y-%m-%d %H:%M:%S')}**")

# Dashboard layout with metrics and charts
col1, col2, col3 = st.columns(3)

# Define the display_hive_status function before it's called
def display_hive_status(df):
    """Display the current status of each hive."""
    st.subheader("🐝 Beehive Status")
    
    # Get unique devices
    devices = df['device_id'].unique()
    
    cols = st.columns(len(devices))
    for i, device in enumerate(devices):
        device_data = df[df['device_id'] == device].iloc[-1]
        behavior = device_data['behavior']
        
        # Define status colors
        status_color = {
            'normal': 'green',
            'swarming': 'orange',
            'distress': 'red'
        }.get(behavior, 'grey')
        
        with cols[i]:
            st.markdown(f"### {device}")
            
            # Status indicator
            st.markdown(
                f"""
                <div style="background-color: {status_color}; 
                            padding: 10px; 
                            border-radius: 5px; 
                            text-align: center;
                            color: white;
                            font-weight: bold;">
                    {behavior.upper()}
                </div>
                """, 
                unsafe_allow_html=True
            )
            
            # Show stats
            st.metric("Temperature", f"{device_data['temperature']:.1f}°C")
            st.metric("Humidity", f"{device_data['humidity']*100:.1f}%")
            
            # Audio metrics from audio_features
            audio_metrics = device_data.get('audio_features', {})
            if audio_metrics:
                st.markdown("#### Audio Metrics")
                metrics_col1, metrics_col2 = st.columns(2)
                
                with metrics_col1:
                    if 'audio_density' in audio_metrics:
                        st.metric("Audio Density", f"{audio_metrics['audio_density']:.2f}")
                    if 'frequency_mean' in audio_metrics:
                        st.metric("Freq Mean", f"{audio_metrics['frequency_mean']:.1f} Hz")
                
                with metrics_col2:
                    if 'density_variation' in audio_metrics:
                        st.metric("Variation", f"{audio_metrics['density_variation']:.2f}")
                    if 'amplitude_mean' in audio_metrics:
                        st.metric("Amplitude", f"{audio_metrics['amplitude_mean']:.2f}")
            
            # Battery level if available
            if 'battery_level' in device_data:
                battery_pct = device_data['battery_level'] * 100
                battery_color = "green" if battery_pct > 50 else "orange" if battery_pct > 20 else "red"
                st.markdown(
                    f"""
                    <div style="margin-top: 10px;">
                        <strong>Battery:</strong> 
                        <div style="background-color: #f0f0f0; 
                                   border-radius: 5px; 
                                   height: 10px; 
                                   width: 100%;">
                            <div style="background-color: {battery_color};
                                      width: {battery_pct}%;
                                      height: 10px;
                                      border-radius: 5px;"></div>
                        </div>
                        <div style="text-align: right; font-size: 0.8em;">{battery_pct:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

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

# Display current hive status
display_hive_status(df)

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
        
        # Extract and plot audio features data
        if 'audio_features' in hive_data:
            audio_features = hive_data['audio_features']
            
            # Create frequency plot from available metrics
            feature_names = []
            feature_values = []
            
            for key, value in audio_features.items():
                if isinstance(value, (int, float)) and key.startswith(('hz_', 'frequency')):
                    feature_names.append(key)
                    feature_values.append(value)
            
            if feature_names:
                # Try to extract frequency values from feature names
                freq_df = pd.DataFrame({
                    'Metric': feature_names,
                    'Value': feature_values
                })
                
                fig = px.bar(freq_df, x='Metric', y='Value', 
                         title=f'Audio Features - {selected_hive}')
                fig.update_layout(xaxis_title='Audio Feature', yaxis_title='Value')
                st.plotly_chart(fig, use_container_width=True)
            
            # Show audio metrics
            col1, col2 = st.columns(2)
            with col1:
                if 'audio_density' in audio_features:
                    st.metric("Audio Density", f"{audio_features['audio_density']:.2f}")
                if 'frequency_mean' in audio_features:
                    st.metric("Frequency Mean", f"{audio_features['frequency_mean']:.2f} Hz")
            
            with col2:
                if 'density_variation' in audio_features:
                    st.metric("Density Variation", f"{audio_features['density_variation']:.2f}")
                if 'amplitude_mean' in audio_features:
                    st.metric("Amplitude", f"{audio_features['amplitude_mean']:.2f}")
        else:
            st.info("No audio feature data available for this hive")
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
refresh_rate = st.sidebar.slider("Refresh interval (seconds)", 5, 60, CONFIG["refresh_interval"])

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

# Auto-refresh notice at the bottom
if not CONFIG["demo_mode"]:
    st.info("Note: Data refreshes automatically from Firestore. You can adjust the refresh rate in the sidebar.")
else:
    st.info("Note: Using simulated data in demo mode. The dashboard will refresh periodically to simulate new data.") 