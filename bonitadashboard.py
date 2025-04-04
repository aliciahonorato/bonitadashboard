import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import plotly.express as px

def set_custom_css():
    st.markdown("""
        <style>
            body, .stText, .stTitle, .stHeader, .stMarkdown {
                color: #faf6f5 !important;  
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
        </style>
    """, unsafe_allow_html=True)

set_custom_css()

st.title("Bonita Brazilian Braids Performance Indicator Dashboard")

# Google Sheets URLs
CUSTOMER_FEEDBACK_URL = "https://docs.google.com/spreadsheets/d/1ONZmz4ZLIw8-IzjeNvdJzMMKJZ0EoJuLxUQqCeMzm5E/edit?resourcekey=&gid=1459096233#gid=1459096233"
INVENTORY_URL = "https://docs.google.com/spreadsheets/d/1g28kftFDBk6nrgpj8qgmEH5QId5stT1p55saBTsctaU/edit?resourcekey=&gid=375516129#gid=375516129"

SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
gc = gspread.authorize(credentials)

@st.cache_data
def load_google_sheet(sheet_url):
    try:
        sheet = gc.open_by_url(sheet_url).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        data.columns = data.columns.str.strip()  # Clean up column names
        return data
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return None

data_type = st.selectbox("Select Data Type", ["Customer Feedback", "Inventory Management"])

if data_type == "Customer Feedback":
    data = load_google_sheet(CUSTOMER_FEEDBACK_URL)
else:
    data = load_google_sheet(INVENTORY_URL)

if data is not None and not data.empty:
    st.write(f"### Loaded Data: {data_type}")
    st.dataframe(data)
    
    if data_type == "Inventory Management":
        required_columns = [
            "Carimbo de data/hora",
            "Total Revenue for the day ($)",
            "Total Expenses for the day ($)",
            "Net Profit for the day ($)",
            "Number of appointments completed today:",
            "Total number of returning customers today:",
            "Total number of new customers today:"
        ]
        
        if not all(col in data.columns for col in required_columns):
            st.error(f"The data must contain: {', '.join(required_columns)}")
        else:
            # Data preprocessing
            data["Carimbo de data/hora"] = pd.to_datetime(data["Carimbo de data/hora"], errors='coerce')
            total_revenue = pd.to_numeric(data["Total Revenue for the day ($)"], errors='coerce').sum()
            total_expenses = pd.to_numeric(data["Total Expenses for the day ($)"], errors='coerce').sum()
            net_profit = pd.to_numeric(data["Net Profit for the day ($)"], errors='coerce').sum()
            total_appointments = pd.to_numeric(data["Number of appointments completed today:"], errors='coerce').sum()
            total_returning = pd.to_numeric(data["Total number of returning customers today:"], errors='coerce').sum()
            total_new = pd.to_numeric(data["Total number of new customers today:"], errors='coerce').sum()
            retention_rate = (total_returning / (total_returning + total_new)) * 100 if (total_returning + total_new) > 0 else 0

            # Display key metrics using columns
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Revenue", f"${total_revenue:,.2f}")
            col2.metric("Total Expenses", f"${total_expenses:,.2f}")
            col3.metric("Net Profit", f"${net_profit:,.2f}")
            
            col4, col5 = st.columns(2)
            col4.metric("Total Appointments", f"{total_appointments:.0f}")
            col5.metric("Customer Retention Rate", f"{retention_rate:.2f}%")
            
            # Interactive Revenue Over Time chart using Plotly
            st.write("### Revenue Over Time")
            timeframe = st.selectbox("Choose timeframe", ["Daily", "Weekly", "Monthly"], key="timeframe")
            if timeframe == "Daily":
                revenue_over_time = data.groupby(data["Carimbo de data/hora"].dt.date)["Total Revenue for the day ($)"].sum().reset_index()
                revenue_over_time.columns = ["Date", "Revenue"]
            elif timeframe == "Weekly":
                revenue_over_time = data.groupby(data["Carimbo de data/hora"].dt.to_period("W"))["Total Revenue for the day ($)"].sum().reset_index()
                revenue_over_time["Date"] = revenue_over_time["Carimbo de data/hora"].astype(str)
                revenue_over_time.columns = ["Period", "Revenue", "Date"]
            else:
                revenue_over_time = data.groupby(data["Carimbo de data/hora"].dt.to_period("M"))["Total Revenue for the day ($)"].sum().reset_index()
                revenue_over_time["Date"] = revenue_over_time["Carimbo de data/hora"].astype(str)
                revenue_over_time.columns = ["Period", "Revenue", "Date"]
            
            fig = px.line(revenue_over_time, x="Date", y="Revenue", title=f"Revenue ({timeframe})", markers=True)
            st.plotly_chart(fig, use_container_width=True)
    
    else:
        # For Customer Feedback, consider visualizations like satisfaction ratings distribution, etc.
        st.write("### Customer Feedback Insights")
        if "How satisfied are you with our services?" in data.columns:
            # Example: Distribution of satisfaction ratings
            satisfaction_counts = data["How satisfied are you with our services?"].value_counts().reset_index()
            satisfaction_counts.columns = ["Satisfaction", "Count"]
            fig2 = px.bar(satisfaction_counts, x="Satisfaction", y="Count", title="Satisfaction Ratings Distribution")
            st.plotly_chart(fig2, use_container_width=True)
else:
    st.write("No data to display.")
