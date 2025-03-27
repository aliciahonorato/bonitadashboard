import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

# Define Custom Colors
PRIMARY_COLOR = "#3b5c3d"  # Títulos e destaques
SECONDARY_COLOR = "#ffbb7c"  # Gráficos
ACCENT_COLOR = "#e59153"  # Números importantes
BACKGROUND_COLOR = "#faf6f5"  # Fundo geral
TEXT_COLOR = "#7c7f46"  # Texto principal

# Apply Custom Styling
st.markdown(
    f"""
    <style>
        body {{
            background-color: {BACKGROUND_COLOR};
            color: {TEXT_COLOR};
            font-family: 'Arial', sans-serif;
        }}
        .stApp {{
            background-color: {BACKGROUND_COLOR};
        }}
        .stTitle {{
            color: {PRIMARY_COLOR};
            font-size: 2.2em;
            font-weight: bold;
        }}
        .stMetric {{
            background-color: {SECONDARY_COLOR};
            color: {ACCENT_COLOR};
            border-radius: 10px;
            padding: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# Dashboard Title
st.title("🌿 Bonita Brazilian Braids Performance Dashboard")

# Google Sheets Setup
SHEET_URL = "YOUR_GOOGLE_SHEET_URL_HERE"
SERVICE_ACCOUNT_FILE = "your-service-account.json"

@st.cache_data
def load_google_sheets():
    try:
        scopes = ["https://www.googleapis.com/auth/spreadsheets"]
        credentials = Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=scopes)
        gc = gspread.authorize(credentials)
        sheet = gc.open_by_url(SHEET_URL).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        return data
    except Exception as e:
        st.error(f"⚠️ Error loading Google Sheet: {e}")
        return None

# File Upload Option
uploaded_file = st.file_uploader("📤 Upload CSV file", type=["csv"])

if uploaded_file:
    data = pd.read_csv(uploaded_file, delimiter=';')
elif SHEET_URL:
    data = load_google_sheets()
else:
    data = None

if data is not None and not data.empty:
    st.write("### 📊 Loaded Data:")
    st.dataframe(data)

    required_columns = ["Date", "Sales", "Revenue", "Customer_ID", "Region", "Retention Status"]
    if not all(col in data.columns for col in required_columns):
        st.error(f"🚨 The data must contain: {', '.join(required_columns)}")
    else:
        data["Date"] = pd.to_datetime(data["Date"])
        total_sales = data["Sales"].sum()
        total_revenue = data["Revenue"].sum()
        customer_retention_rate = (data["Retention Status"].str.lower() == "yes").mean() * 100

        # Metrics with Custom Styling
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Sales", f"{total_sales}", help="Total number of sales")
        with col2:
            st.metric("Total Revenue", f"${total_revenue:,.2f}", help="Total revenue generated")
        with col3:
            st.metric("Customer Retention", f"{customer_retention_rate:.2f}%", help="Percentage of returning customers")

        # Sales Over Time
        st.write("### 📈 Sales Performance Over Time")
        sales_timeframe = st.selectbox("⏳ Choose timeframe", ["Daily", "Weekly", "Monthly"])
        if sales_timeframe == "Daily":
            sales_over_time = data.groupby(data["Date"].dt.date)["Sales"].sum()
        elif sales_timeframe == "Weekly":
            sales_over_time = data.groupby(data["Date"].dt.to_period("W"))["Sales"].sum()
        else:
            sales_over_time = data.groupby(data["Date"].dt.to_period("M"))["Sales"].sum()

        fig, ax = plt.subplots()
        sales_over_time.plot(ax=ax, kind="line", color=SECONDARY_COLOR)
        ax.set_title(f"Sales ({sales_timeframe})", color=PRIMARY_COLOR)
        ax.set_ylabel("Sales", color=TEXT_COLOR)
        ax.set_xlabel("Time", color=TEXT_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        st.pyplot(fig)

        # Sales by Region
        st.write("### 🏠 Sales by Region")
        sales_by_region = data.groupby("Region")["Sales"].sum()
        fig, ax = plt.subplots()
        sales_by_region.plot(ax=ax, kind="bar", color=SECONDARY_COLOR)
        ax.set_title("Sales by Region", color=PRIMARY_COLOR)
        ax.set_ylabel("Sales", color=TEXT_COLOR)
        ax.set_xlabel("Region", color=TEXT_COLOR)
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        st.pyplot(fig)

        # Growth Rate
        if "Growth Rate" not in data.columns:
            data["Growth Rate"] = data["Revenue"].pct_change() * 100
        avg_growth_rate = data["Growth Rate"].mean()
        st.metric("📈 Average Growth Rate", f"{avg_growth_rate:.2f}%", help="Average revenue growth over time")

        # Insights
        st.write("### 🔎 Additional Insights")
        st.write("🏆 **Top 5 Customers by Revenue:**")
        top_customers = data.groupby("Customer_ID")["Revenue"].sum().nlargest(5)
        st.table(top_customers)
else:
    st.write("🚀 Upload a CSV file or connect a Google Sheet to get started.")
