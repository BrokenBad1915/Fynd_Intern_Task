import streamlit as st
import pandas as pd
import json
import os
import time
import plotly.express as px  # Requires pip install plotly

# --- CONFIGURATION ---
DATA_FILE = "data.json"

st.set_page_config(page_title="Admin Analytics", layout="wide", page_icon="📊")

# --- CUSTOM CSS FOR STYLING ---
st.markdown("""
    <style>
    .main {
        background-color: #f9f9f9;
    }
    div.stMetric {
        background-color: #ffffff;
        border: 1px solid #e6e6e6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("📊 Executive Feedback Console")
st.markdown("Real-time analysis of customer sentiment and AI recommendations.")

# --- LOAD DATA ---
if not os.path.exists(DATA_FILE):
    st.info("Waiting for data... No submissions yet.")
    st.stop()

with open(DATA_FILE, "r") as f:
    try:
        raw_data = json.load(f)
    except:
        raw_data = []

if not raw_data:
    st.warning("Database is empty.")
    st.stop()

# Prepare DataFrame
df = pd.DataFrame(raw_data)
df['timestamp'] = pd.to_datetime(df['timestamp']) # Convert to datetime objects for charting

# --- SIDEBAR FILTERS ---
st.sidebar.header("🔍 Filter Data")
min_rating = st.sidebar.slider("Filter by Minimum Rating", 1, 5, 1)
filtered_df = df[df['rating'] >= min_rating]

# --- KPI METRICS ---
col1, col2, col3, col4 = st.columns(4)

total_reviews = len(df)
avg_rating = df['rating'].mean()
negative_reviews = len(df[df['rating'] <= 2])
recent_trend = "Stable" # Logic can be added to compare vs yesterday

with col1:
    st.metric("Total Reviews", total_reviews, delta="All Time")
with col2:
    st.metric("Average Rating", f"{avg_rating:.1f} / 5.0", delta_color="normal")
with col3:
    st.metric("Critical Issues", negative_reviews, delta="-Alert", delta_color="inverse")
with col4:
    st.metric("Latest Review", df['timestamp'].max().strftime("%H:%M %p"))

st.divider()

# --- DETAILED CHARTS SECTION ---

# Layout: Two columns for charts
chart_col1, chart_col2 = st.columns(2)

with chart_col1:
    st.subheader("📈 Satisfaction Trend (Over Time)")
    if len(df) > 1:
        # Sort by time to make the line chart correct
        df_sorted = df.sort_values('timestamp')
        fig_trend = px.line(df_sorted, x='timestamp', y='rating', markers=True, 
                            title="Rating History", template="plotly_white")
        fig_trend.update_yaxes(range=[0, 5.5])
        st.plotly_chart(fig_trend, use_container_width=True)
    else:
        st.info("Need more data points for trend analysis.")

with chart_col2:
    st.subheader("⚖️ Rating Distribution")
    rating_counts = df['rating'].value_counts().reset_index()
    rating_counts.columns = ['Rating', 'Count']
    fig_pie = px.pie(rating_counts, values='Count', names='Rating', 
                     title="Share of Star Ratings", hole=0.4,
                     color_discrete_sequence=px.colors.sequential.RdBu)
    st.plotly_chart(fig_pie, use_container_width=True)

# --- AI INSIGHTS ANALYSIS ---
st.subheader("🤖 AI Action Analysis")
st.write("What is the AI suggesting we do most often?")

# Group by the recommended action to see patterns
if 'ai_action' in df.columns:
    action_counts = df['ai_action'].value_counts().head(5)
    st.bar_chart(action_counts, color="#FF4B4B")
else:
    st.warning("No AI Actions found in data.")

st.divider()

# --- ENHANCED DATA TABLE ---
st.subheader(f"📝 Recent Reviews (Filtered: {len(filtered_df)})")

# We create a display-friendly version
display_table = filtered_df[['timestamp', 'rating', 'review', 'ai_summary', 'ai_action']].sort_values(by='timestamp', ascending=False)

st.dataframe(
    display_table,
    use_container_width=True,
    column_config={
        "timestamp": st.column_config.DatetimeColumn("Date", format="D MMM, HH:mm"),
        "rating": st.column_config.NumberColumn(
            "Score", 
            help="User rating out of 5",
            format="%d ⭐"
        ),
        "review": st.column_config.TextColumn("Customer Review", width="medium"),
        "ai_summary": st.column_config.TextColumn("AI Summary", width="small"),
        "ai_action": st.column_config.TextColumn("Recommended Action", width="small"),
    },
    hide_index=True
)

# Download Button
@st.cache_data
def convert_df(df):
    return df.to_csv(index=False).encode('utf-8')

csv = convert_df(df)

st.download_button(
    label="📥 Download Full Report (CSV)",
    data=csv,
    file_name='feedback_report.csv',
    mime='text/csv',
)
