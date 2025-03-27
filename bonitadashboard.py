import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

def set_custom_css():
    st.markdown("""
        <style>
            body, .stText, .stTitle, .stHeader, .stMarkdown {
                color: #faf6f5 !important;  /* Branco claro para as letras */
            }
            .stApp {
                background-color: #3b5c3d !important;  /* Verde escuro para o fundo */
            }
            .stMetric {
                color: #f5e7cc !important;  /* Bege claro para as métricas */
            }
            .stDataFrame {
                background-color: #7c7f46 !important; /* Verde oliva claro para a tabela */
            }
        </style>
    """, unsafe_allow_html=True)

set_custom_css()

# Dashboard Title
st.title("Bonita Brazilian Braids Performance Indicator Dashboard")

# Google Sheets Setup
SHEET_URL = "https://docs.google.com/forms/d/1XAqL--awAaFFszSMcJXNd2tb2RUv1mxie7eDsAoLZR4/edit"  # Replace with your actual Google Sheet URL
SERVICE_ACCOUNT_FILE = r"C:\Users\lica_\OneDrive\Documentos\INTERCÂMBIO CCI 2024\2024 Summer-Fall Semester\CIP\Bonita\client_secret_52289991427-88rpm95o3aic7fsk4ueb0sert5uf6l74.apps.googleusercontent.com.json"  # Replace with your JSON file path

# Authenticate and fetch data from Google Sheets
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
        st.error(f"Error loading Google Sheet: {e}")
        return None

# File Upload Option
uploaded_file = st.file_uploader("Upload CSV file", type=["csv"])

if uploaded_file:
    # Load CSV Data
    data = pd.read_csv(uploaded_file, delimiter=';')
elif SHEET_URL:
    # Load Google Sheets Data
    data = load_google_sheets()
else:
    data = None

if data is not None and not data.empty:
    st.write("### Loaded Data:")
    st.dataframe(data)

    # Ensure necessary columns exist
    required_columns = ["Date", "Sales", "Revenue", "Customer_ID", "Region", "Retention Status"]
    if not all(col in data.columns for col in required_columns):
        st.error(f"The data must contain: {', '.join(required_columns)}")
    else:
        # Convert 'Date' to datetime
        data["Date"] = pd.to_datetime(data["Date"])

        # Metrics
        total_sales = data["Sales"].sum()
        total_revenue = data["Revenue"].sum()
        customer_retention_rate = (data["Retention Status"].str.lower() == "yes").mean() * 100

        st.metric("Total Sales", f"{total_sales}")
        st.metric("Total Revenue", f"${total_revenue:,.2f}")
        st.metric("Customer Retention Rate", f"{customer_retention_rate:.2f}%")

        # Sales Over Time
        st.write("### Sales Performance Over Time")
        sales_timeframe = st.selectbox("Choose timeframe", ["Daily", "Weekly", "Monthly"])
        if sales_timeframe == "Daily":
            sales_over_time = data.groupby(data["Date"].dt.date)["Sales"].sum()
        elif sales_timeframe == "Weekly":
            sales_over_time = data.groupby(data["Date"].dt.to_period("W"))["Sales"].sum()
        else:
            sales_over_time = data.groupby(data["Date"].dt.to_period("M"))["Sales"].sum()

        fig, ax = plt.subplots()
        sales_over_time.plot(ax=ax, kind="line", color="#e59153")  # Cor laranja escuro da paleta
        ax.set_title(f"Sales ({sales_timeframe})")
        ax.set_ylabel("Sales")
        ax.set_xlabel("Time")
        st.pyplot(fig)

        # Sales by Region
        st.write("### Sales by Region")
        sales_by_region = data.groupby("Region")["Sales"].sum()
        fig, ax = plt.subplots()
        sales_by_region.plot(ax=ax, kind="bar", color="#ffbb7c")  # Cor laranja claro da paleta
        ax.set_title("Sales by Region")
        ax.set_ylabel("Sales")
        ax.set_xlabel("Region")
        st.pyplot(fig)

        # Revenue Growth Calculation
        if "Growth Rate" not in data.columns:
            data["Growth Rate"] = data["Revenue"].pct_change() * 100

        avg_growth_rate = data["Growth Rate"].mean()
        st.metric("Average Growth Rate", f"{avg_growth_rate:.2f}%")

        # Insights Section
        st.write("### Additional Insights")
        st.write("Top 5 Customers by Revenue:")
        top_customers = data.groupby("Customer_ID")["Revenue"].sum().nlargest(5)
        st.table(top_customers)
else:
    st.write("Please upload a CSV file or connect a Google Sheet to get started.")
