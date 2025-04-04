import streamlit as st
import pandas as pd
import altair as alt
import gspread
from google.oauth2.service_account import Credentials
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import string

# --------------------- Custom CSS & Branding ---------------------
def set_custom_css():
    st.markdown("""
        <style>
            body, .stText, .stTitle, .stHeader, .stMarkdown {
                color: #faf6f5 !important;
                font-family: 'Helvetica Neue', sans-serif;
            }
            .stApp {
                background-color: #3b5c3d !important;
            }
            .stMetric {
                color: #f5e7cc !important;
            }
            .stDataFrame {
                background-color: #7c7f46 !important;
            }
            .header-title {
                font-size: 2.5rem;
                font-weight: bold;
                text-align: center;
                margin-bottom: 1rem;
            }
            .subheader {
                font-size: 1.5rem;
                margin-top: 1rem;
                margin-bottom: 0.5rem;
            }
        </style>
    """, unsafe_allow_html=True)

set_custom_css()

# --------------------- Dashboard Title ---------------------
st.markdown("<div class='header-title'>Customer Feedback Dashboard</div>", unsafe_allow_html=True)

# --------------------- Google Sheets Configuration ---------------------
CUSTOMER_FEEDBACK_URL = (
    "https://docs.google.com/spreadsheets/d/1ONZmz4ZLIw8-IzjeNvdJzMMKJZ0EoJuLxUQqCeMzm5E/"
    "edit?resourcekey=&gid=1459096233#gid=1459096233"
)

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"], 
    scopes=SCOPES
)
gc = gspread.authorize(credentials)

@st.cache_data
def load_google_sheet(sheet_url):
    """Loads the first worksheet from the given Google Sheet URL into a DataFrame."""
    try:
        sheet = gc.open_by_url(sheet_url).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        data.columns = data.columns.str.strip()
        return data
    except Exception as e:
        st.error(f"Error loading the Google Sheet: {e}")
        return None

@st.cache_data
def process_text(text_list):
    """
    Basic text processing:
      - Lowercasing
      - Tokenizing
      - Removing stopwords and punctuation
      - Counting word frequencies
    Returns a DataFrame with 'word' and 'count'.
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

    # Count frequencies
    freq_dist = nltk.FreqDist(all_tokens)
    df_freq = pd.DataFrame(freq_dist.items(), columns=["word", "count"])
    df_freq = df_freq.sort_values("count", ascending=False).reset_index(drop=True)
    return df_freq

# --------------------- Load Data ---------------------
data = load_google_sheet(CUSTOMER_FEEDBACK_URL)
if data is None or data.empty:
    st.error("No customer feedback data available.")
    st.stop()

# --------------------- Data Preview & Download ---------------------
st.subheader("Data Preview")
st.dataframe(data.head(5))

csv_data = data.to_csv(index=False).encode("utf-8")
st.download_button(
    label="Download Full CSV",
    data=csv_data,
    file_name="customer_feedback.csv",
    mime="text/csv"
)

# --------------------- Key Insights ---------------------
st.subheader("Key Metrics")
total_responses = len(data)
st.metric("Total Responses", f"{total_responses}")

# If we have a satisfaction column, we can show distribution
if "How satisfied are you with our services?" in data.columns:
    sat_counts = data["How satisfied are you with our services?"].value_counts().reset_index()
    sat_counts.columns = ["Satisfaction", "Count"]
    # Create a donut chart for satisfaction distribution
    chart_satisfaction = (
        alt.Chart(sat_counts)
        .mark_arc(innerRadius=50, stroke="#fff")
        .encode(
            theta=alt.Theta(field="Count", type="quantitative"),
            color=alt.Color("Satisfaction:N", scale=alt.Scale(range=["#F7B26A", "#C17544", "#FFD700"])),
            tooltip=["Satisfaction:N", "Count:Q"]
        )
        .properties(title="Satisfaction Distribution", width=400, height=400)
        .interactive()
    )
    st.altair_chart(chart_satisfaction, use_container_width=True)
else:
    st.write("No satisfaction data available.")

# --------------------- Visit Frequency ---------------------
if "How often do you visit a hair salon?" in data.columns:
    freq_counts = data["How often do you visit a hair salon?"].value_counts().reset_index()
    freq_counts.columns = ["Frequency", "Count"]
    chart_freq = (
        alt.Chart(freq_counts)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Frequency:N", title="Visit Frequency"),
            y=alt.Y("Count:Q", title="Count"),
            tooltip=["Frequency:N", "Count:Q"]
        )
        .properties(title="Visit Frequency Distribution", width=700, height=400)
        .interactive()
    )
    st.altair_chart(chart_freq, use_container_width=True)

# --------------------- Marketing Channel ---------------------
if "How did you hear about us?" in data.columns:
    st.subheader("Marketing Channel Effectiveness")
    channel_counts = data["How did you hear about us?"].value_counts().reset_index()
    channel_counts.columns = ["Channel", "Count"]
    chart_channel = (
        alt.Chart(channel_counts)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Channel:N", title="Channel"),
            y=alt.Y("Count:Q", title="Count"),
            tooltip=["Channel:N", "Count:Q"]
        )
        .properties(title="Channels Used by Customers", width=700, height=400)
        .interactive()
    )
    st.altair_chart(chart_channel, use_container_width=True)

# --------------------- Would You Recommend Us? ---------------------
if "Would you recommend us to a friend?" in data.columns:
    st.subheader("Recommendation (NPS-like) Insight")
    rec_counts = data["Would you recommend us to a friend?"].value_counts().reset_index()
    rec_counts.columns = ["Recommend", "Count"]
    chart_recommend = (
        alt.Chart(rec_counts)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X("Recommend:N", title="Response"),
            y=alt.Y("Count:Q", title="Count"),
            tooltip=["Recommend:N", "Count:Q"]
        )
        .properties(title="Would You Recommend Us?", width=700, height=400)
        .interactive()
    )
    st.altair_chart(chart_recommend, use_container_width=True)

# --------------------- Opportunity for New Services ---------------------
if "Is there a service you wish we offered but currently don’t?" in data.columns:
    st.subheader("Requested Services")
    new_services = data["Is there a service you wish we offered but currently don’t?"].dropna().tolist()
    if new_services:
        st.write("Top customer suggestions for new services:")
        # Convert list to a small DataFrame with counts
        df_new_services = pd.Series(new_services).value_counts().reset_index()
        df_new_services.columns = ["Suggested Service", "Count"]
        st.dataframe(df_new_services.head(5))
    else:
        st.write("No suggestions provided.")

# --------------------- Text Analysis for Improvements ---------------------
if "What could we improve to enhance your experience?" in data.columns:
    st.subheader("Top Words in Improvement Suggestions")
    improvements = data["What could we improve to enhance your experience?"].dropna().tolist()
    if improvements:
        # Process text to get top words
        df_word_freq = process_text(improvements)
        if not df_word_freq.empty:
            # Show top 10 words
            top_words = df_word_freq.head(10)
            chart_words = (
                alt.Chart(top_words)
                .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
                .encode(
                    x=alt.X("word:N", sort=None, title="Word"),
                    y=alt.Y("count:Q", title="Count"),
                    tooltip=["word:N", "count:Q"]
                )
                .properties(title="Most Common Words in Suggestions", width=700, height=400)
                .interactive()
            )
            st.altair_chart(chart_words, use_container_width=True)
        else:
            st.write("No valid words found after processing. (Check for stopwords/punctuation)")
    else:
        st.write("No improvement suggestions provided.")

# --------------------- Additional Insights or Suggestions ---------------------
st.subheader("Additional Observations")
st.write(
    "Based on the data above, you can identify key areas for service expansion, understand "
    "customer satisfaction trends, and see which marketing channels are most effective. "
    "Use the word frequency analysis of open-ended feedback to pinpoint common themes and "
    "address them directly for a better customer experience."
)
