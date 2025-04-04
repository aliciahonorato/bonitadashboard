import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import matplotlib.pyplot as plt

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

# URLs das planilhas
SHEET_URL_CUSTOMER = "https://docs.google.com/spreadsheets/d/1ONZmz4ZLIw8-IzjeNvdJzMMKJZ0EoJuLxUQqCeMzm5E/edit?usp=sharing"
SHEET_URL_INVENTORY = "https://docs.google.com/spreadsheets/d/1g28kftFDBk6nrgpj8qgmEH5QId5stT1p55saBTsctaU/edit?usp=sharing"

# Escopos para gspread
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Autenticação
credentials = Credentials.from_service_account_info(
    st.secrets["gcp_service_account"],
    scopes=SCOPES
)
gc = gspread.authorize(credentials)

@st.cache_data
def load_google_sheets(sheet_url):
    try:
        sheet = gc.open_by_url(sheet_url).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        return data
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return None

# Seleção entre tipos de dados
data_type = st.selectbox("Select Data Type", ["Customer Feedback", "Inventory Management"])

if data_type == "Customer Feedback":
    data = load_google_sheets(SHEET_URL_CUSTOMER)
else:
    data = load_google_sheets(SHEET_URL_INVENTORY)

if data is not None and not data.empty:
    st.write(f"### Loaded Data: {data_type}")
    st.dataframe(data)

    if data_type == "Inventory Management":
        required_columns = ["Date", "Sales", "Revenue", "Customer_ID", "Region", "Retention Status"]
        if not all(col in data.columns for col in required_columns):
            st.error(f"The data must contain: {', '.join(required_columns)}")
        else:
            data["Date"] = pd.to_datetime(data["Date"])

            total_sales = data["Sales"].sum()
            total_revenue = data["Revenue"].sum()
            customer_retention_rate = (data["Retention Status"].str.lower() == "yes").mean() * 100

            st.metric("Total Sales", f"{total_sales}")
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
            st.metric("Customer Retention Rate", f"{customer_retention_rate:.2f}%")

            # Gráfico de vendas ao longo do tempo
            st.write("### Sales Performance Over Time")
            sales_timeframe = st.selectbox("Choose timeframe", ["Daily", "Weekly", "Monthly"])
            if sales_timeframe == "Daily":
                sales_over_time = data.groupby(data["Date"].dt.date)["Sales"].sum()
            elif sales_timeframe == "Weekly":
                sales_over_time = data.groupby(data["Date"].dt.to_period("W"))["Sales"].sum()
            else:
                sales_over_time = data.groupby(data["Date"].dt.to_period("M"))["Sales"].sum()

            fig, ax = plt.subplots()
            sales_over_time.plot(ax=ax, kind="line", color="#e59153")
            ax.set_title(f"Sales ({sales_timeframe})")
            ax.set_ylabel("Sales")
            ax.set_xlabel("Time")
            st.pyplot(fig)

            # Gráfico de vendas por região
            st.write("### Sales by Region")
            sales_by_region = data.groupby("Region")["Sales"].sum()
            fig, ax = plt.subplots()
            sales_by_region.plot(ax=ax, kind="bar", color="#ffbb7c")
            ax.set_title("Sales by Region")
            ax.set_ylabel("Sales")
            ax.set_xlabel("Region")
            st.pyplot(fig)

            # Crescimento da receita
            if "Growth Rate" not in data.columns:
                data["Growth Rate"] = data["Revenue"].pct_change() * 100

            avg_growth_rate = data["Growth Rate"].mean()
            st.metric("Average Growth Rate", f"{avg_growth_rate:.2f}%")

            # Top 5 clientes
            st.write("### Top 5 Customers by Revenue")
            top_customers = data.groupby("Customer_ID")["Revenue"].sum().nlargest(5)
            st.table(top_customers)

# Removido o else que mostrava "Please upload a CSV..."
