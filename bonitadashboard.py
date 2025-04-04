import streamlit as st
import pandas as pd
import altair as alt
import gspread
from google.oauth2.service_account import Credentials
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# Set page configuration for a wide, modern layout
st.set_page_config(page_title="Bonita Customer Feedback Dashboard", layout="wide", initial_sidebar_state="expanded")

# --------------------- Custom CSS & Branding ---------------------
def set_custom_css():
    st.markdown("""
        <style>
            /* Global styles */
            body, .stText, .stTitle, .stHeader, .stMarkdown {
                font-family: 'Helvetica Neue', sans-serif;
                color: #ecf0f1;
            }
            .stApp {
                background-color: #2c3e50;
            }
            /* Header styling */
            .header-title {
                font-size: 3rem;
                font-weight: bold;
                text-align: center;
                margin-bottom: 1rem;
                color: #e74c3c;
            }
            .subheader {
                font-size: 1.75rem;
                margin-top: 1rem;
                margin-bottom: 0.5rem;
                color: #f39c12;
            }
            /* Metric card styling */
            .metric-card {
                background-color: #34495e;
                padding: 1rem;
                border-radius: 8px;
                box-shadow: 2px 2px 10px rgba(0, 0, 0, 0.2);
                margin-bottom: 1rem;
            }
            .metric-card h3 {
                margin: 0;
                color: #f39c12;
            }
            .metric-card p {
                margin: 0;
                font-size: 1.25rem;
            }
        </style>
    """, unsafe_allow_html=True)

set_custom_css()

# --------------------- Dashboard Title ---------------------
st.markdown("<div class='header-title'>Customer Feedback Dashboard</div>", unsafe_allow_html=True)

# --------------------- Google Sheets Configuration ---------------------
CUSTOMER_FEEDBACK_URL = "https://docs.google.com/spreadsheets/d/1ONZmz4ZLIw8-IzjeNvdJzMMKJZ0EoJuLxUQqCeMzm5E/edit?resourcekey=&gid=1459096233#gid=1459096233"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
gc = gspread.authorize(credentials)

@st.cache_data
def load_google_sheet(sheet_url):
    """Load the first worksheet from the given Google Sheet URL into a DataFrame."""
    try:
        sheet = gc.open_by_url(sheet_url).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        data.columns = data.columns.str.strip()  # Clean up column names
        return data
    except Exception as e:
        st.error(f"Error loading the Google Sheet: {e}")
        return None

@st.cache_data
def process_text(text_list):
    """
    Process text by:
    - Lowercasing
    - Tokenizing
    - Removing stopwords, punctuation, and non-alphabetic tokens
    - Returning word frequency as a DataFrame
    """
    all_tokens = []
    stop_words = set(stopwords.words('english'))
    punctuation_set = set(string.punctuation)
    
    for text in text_list:
        text = text.lower()
        tokens = word_tokenize(text)
        for token in tokens:
            if token not in stop_words and token not in punctuation_set and token.isalpha():
                all_tokens.append(token)
    
    freq_dist = nltk.FreqDist(all_tokens)
    df_freq = pd.DataFrame(freq_dist.items(), columns=["word", "count"]).sort_values("count", ascending=False).reset_index(drop=True)
    return df_freq

# --------------------- Load Customer Feedback Data ---------------------
data = load_google_sheet(CUSTOMER_FEEDBACK_URL)
if data is None or data.empty:
    st.error("No customer feedback data available.")
    st.stop()

# Sidebar with data preview and download option
st.sidebar.markdown("### Data Preview")
st.sidebar.dataframe(data.head(5))
csv_data = data.to_csv(index=False).encode("utf-8")
st.sidebar.download_button(label="Download CSV", data=csv_data, file_name="customer_feedback.csv", mime="text/csv")

# --------------------- Tab Layout ---------------------
tabs = st.tabs(["Overview", "Detailed Analysis", "Improvement Insights"])

# ---------- Tab 1: Overview ----------
with tabs[0]:
    st.markdown("## Overview")
    total_responses = len(data)
    st.markdown(f"**Total Responses:** {total_responses}")
    
    # Satisfaction distribution donut chart
    if "How satisfied are you with our services?" in data.columns:
        sat_counts = data["How satisfied are you with our services?"].value_counts().reset_index()
        sat_counts.columns = ["Satisfaction", "Count"]
        donut_chart = alt.Chart(sat_counts).mark_arc(innerRadius=50, stroke="#ffffff").encode(
            theta=alt.Theta("Count:Q", stack=True),
            color=alt.Color("Satisfaction:N", scale=alt.Scale(range=["#e74c3c", "#f1c40f", "#2ecc71", "#3498db"])),
            tooltip=["Satisfaction:N", "Count:Q"]
        ).properties(title="Customer Satisfaction", width=400, height=400).interactive()
        st.altair_chart(donut_chart, use_container_width=True)
    else:
        st.write("No satisfaction data available.")
    
    # Visit Frequency Bar Chart
    if "How often do you visit a hair salon?" in data.columns:
        freq_counts = data["How often do you visit a hair salon?"].value_counts().reset_index()
        freq_counts.columns = ["Frequency", "Count"]
        freq_chart = alt.Chart(freq_counts).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Frequency:N", title="Visit Frequency"),
            y=alt.Y("Count:Q", title="Count"),
            tooltip=["Frequency:N", "Count:Q"]
        ).properties(title="Visit Frequency Distribution", width=700, height=400).interactive()
        st.altair_chart(freq_chart, use_container_width=True)
    else:
        st.write("No visit frequency data available.")

# ---------- Tab 2: Detailed Analysis ----------
with tabs[1]:
    st.markdown("## Detailed Analysis")
    
    # Marketing Channel Effectiveness
    if "How did you hear about us?" in data.columns:
        channel_counts = data["How did you hear about us?"].value_counts().reset_index()
        channel_counts.columns = ["Channel", "Count"]
        channel_chart = alt.Chart(channel_counts).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Channel:N", title="Channel"),
            y=alt.Y("Count:Q", title="Count"),
            tooltip=["Channel:N", "Count:Q"]
        ).properties(title="Marketing Channels", width=700, height=400).interactive()
        st.altair_chart(channel_chart, use_container_width=True)
    else:
        st.write("No marketing channel data available.")
    
    # Recommendation (NPS-like) Analysis
    if "Would you recommend us to a friend?" in data.columns:
        recommend_counts = data["Would you recommend us to a friend?"].value_counts().reset_index()
        recommend_counts.columns = ["Recommendation", "Count"]
        recommend_chart = alt.Chart(recommend_counts).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
            x=alt.X("Recommendation:N", title="Response"),
            y=alt.Y("Count:Q", title="Count"),
            tooltip=["Recommendation:N", "Count:Q"]
        ).properties(title="Would You Recommend Us?", width=700, height=400).interactive()
        st.altair_chart(recommend_chart, use_container_width=True)
    else:
        st.write("No recommendation data available.")

# ---------- Tab 3: Improvement Insights ----------
with tabs[2]:
    st.markdown("## Improvement Insights")
    
    # New Services Requests
    if "Is there a service you wish we offered but currently don’t?" in data.columns:
        new_services = data["Is there a service you wish we offered but currently don’t?"].dropna().tolist()
        if new_services:
            st.markdown("### Top Requested New Services")
            df_new_services = pd.Series(new_services).value_counts().reset_index()
            df_new_services.columns = ["Service", "Count"]
            st.dataframe(df_new_services.head(5))
        else:
            st.write("No new service requests provided.")
    else:
        st.write("No data on new service requests.")
    
    # Text Analysis for Improvement Suggestions
    if "What could we improve to enhance your experience?" in data.columns:
        improvements = data["What could we improve to enhance your experience?"].dropna().tolist()
        if improvements:
            st.markdown("### Common Improvement Suggestions")
            df_word_freq = process_text(improvements)
            if not df_word_freq.empty:
                top_words = df_word_freq.head(10)
                words_chart = alt.Chart(top_words).mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5).encode(
                    x=alt.X("word:N", title="Word", sort="-y"),
                    y=alt.Y("count:Q", title="Count"),
                    tooltip=["word:N", "count:Q"]
                ).properties(title="Most Common Words in Suggestions", width=700, height=400).interactive()
                st.altair_chart(words_chart, use_container_width=True)
            else:
                st.write("No significant words found.")
        else:
            st.write("No improvement suggestions provided.")
    
    st.markdown("## Final Observations")
    st.write("This dashboard provides a clear overview of customer feedback. Use the insights on satisfaction, visit frequency, and common suggestions to drive improvements in your services and marketing strategies.")
