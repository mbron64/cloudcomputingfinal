"""
Streamlit dashboard for beehive monitoring.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from google.cloud import firestore
import time

# Initialize Firestore client
db = firestore.Client()

def load_recent_classifications(limit: int = 100) -> pd.DataFrame:
    """
    Load recent classifications from Firestore.
    
    Args:
        limit: Maximum number of records to load
        
    Returns:
        DataFrame of classifications
    """
    # Query Firestore
    docs = db.collection('hive_classifications')\
             .order_by('timestamp', direction=firestore.Query.DESCENDING)\
             .limit(limit)\
             .stream()
    
    # Convert to DataFrame
    records = []
    for doc in docs:
        data = doc.to_dict()
        if not data.get('timestamp'):
            continue
            
        # Convert timestamp to datetime
        if hasattr(data['timestamp'], 'strftime'):
            timestamp = data['timestamp']
        else:
            timestamp = datetime.fromtimestamp(data['timestamp'].timestamp())
            
        records.append({
            'timestamp': timestamp,
            'audio_file': data['audio_file'],
            'prediction': data['prediction'],
            'confidence': max(data['probabilities']),
            'duration': data['metadata']['duration']
        })
    
    return pd.DataFrame(records)

def plot_predictions(df: pd.DataFrame) -> go.Figure:
    """
    Create a time series plot of predictions.
    
    Args:
        df: DataFrame of classifications
        
    Returns:
        Plotly figure
    """
    # Create figure
    fig = go.Figure()
    
    # Add traces for each prediction type
    for pred in df['prediction'].unique():
        mask = df['prediction'] == pred
        fig.add_trace(go.Scatter(
            x=df[mask]['timestamp'],
            y=df[mask]['confidence'],
            name=pred,
            mode='lines+markers'
        ))
    
    # Update layout
    fig.update_layout(
        title='Beehive Behavior Predictions Over Time',
        xaxis_title='Time',
        yaxis_title='Confidence',
        hovermode='x unified'
    )
    
    return fig

def plot_prediction_distribution(df: pd.DataFrame) -> go.Figure:
    """
    Create a pie chart of prediction distribution.
    
    Args:
        df: DataFrame of classifications
        
    Returns:
        Plotly figure
    """
    # Count predictions
    counts = df['prediction'].value_counts()
    
    # Create figure
    fig = go.Figure(data=[go.Pie(
        labels=counts.index,
        values=counts.values,
        hole=.3
    )])
    
    # Update layout
    fig.update_layout(
        title='Distribution of Predictions',
        showlegend=True
    )
    
    return fig

def main():
    """Main dashboard function."""
    st.set_page_config(
        page_title='Beehive Monitoring Dashboard',
        page_icon='🐝',
        layout='wide'
    )
    
    st.title('🐝 Beehive Monitoring Dashboard')
    
    # Add auto-refresh
    if 'last_refresh' not in st.session_state:
        st.session_state.last_refresh = datetime.now()
    
    # Auto-refresh every 5 minutes
    if datetime.now() - st.session_state.last_refresh > timedelta(minutes=5):
        st.session_state.last_refresh = datetime.now()
        st.experimental_rerun()
    
    # Load data
    df = load_recent_classifications()
    
    if df.empty:
        st.warning('No data available yet.')
        return
    
    # Display current status
    current_status = df.iloc[0]
    st.subheader('Current Status')
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(
            'Current Behavior',
            current_status['prediction'].upper(),
            delta=None
        )
    
    with col2:
        st.metric(
            'Confidence',
            f"{current_status['confidence']:.1%}",
            delta=None
        )
    
    with col3:
        st.metric(
            'Last Update',
            current_status['timestamp'].strftime('%Y-%m-%d %H:%M:%S'),
            delta=None
        )
    
    # Display alerts if needed
    if current_status['prediction'] in ['swarming', 'distress']:
        st.error(f"⚠️ {current_status['prediction'].upper()} DETECTED!")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(['Time Series', 'Statistics'])
    
    with tab1:
        st.plotly_chart(plot_predictions(df), use_container_width=True)
        
        # Show recent events
        st.subheader('Recent Events')
        st.dataframe(
            df[['timestamp', 'prediction', 'confidence', 'audio_file']]
            .rename(columns={
                'timestamp': 'Time',
                'prediction': 'Behavior',
                'confidence': 'Confidence',
                'audio_file': 'Audio File'
            })
            .style.format({
                'Time': lambda x: x.strftime('%Y-%m-%d %H:%M:%S'),
                'Confidence': '{:.1%}'
            })
        )
    
    with tab2:
        col1, col2 = st.columns(2)
        
        with col1:
            st.plotly_chart(plot_prediction_distribution(df), use_container_width=True)
        
        with col2:
            # Calculate statistics
            stats = {
                'Total Recordings': len(df),
                'Average Duration': f"{df['duration'].mean():.1f}s",
                'Most Common Behavior': df['prediction'].mode().iloc[0],
                'Average Confidence': f"{df['confidence'].mean():.1%}"
            }
            
            st.subheader('Statistics')
            for key, value in stats.items():
                st.metric(key, value)
    
    # Add refresh button
    if st.button('🔄 Refresh Data'):
        st.session_state.last_refresh = datetime.now()
        st.experimental_rerun()

if __name__ == '__main__':
    main() 