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

# Título do Dashboard
st.title("Bonita Brazilian Braids Performance Indicator Dashboard")

# Identificadores das planilhas:
# Para Inventory Management, utilizamos a URL completa
SHEET_URL_INVENTORY = "https://docs.google.com/spreadsheets/d/1g28kftFDBk6nrgpj8qgmEH5QId5stT1p55saBTsctaU/edit?usp=sharing"
# Para Customer Feedback, utilizamos a chave extraída da URL
CUSTOMER_FEEDBACK_KEY = "1ONZmz4ZLIw8-IzjeNvdJzMMKJZ0EoJuLxUQqCeMzm5E"

# Escopos para acesso às APIs do Google Sheets e Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Autenticação via conta de serviço usando os secrets configurados
credentials = Credentials.from_service_account_info(st.secrets["gcp_service_account"], scopes=SCOPES)
gc = gspread.authorize(credentials)

# Função para carregar os dados da planilha
@st.cache_data
def load_google_sheets(sheet_identifier, use_key=True):
    try:
        if use_key:
            # Abre a planilha pela chave (usado para Customer Feedback)
            sheet = gc.open_by_key(sheet_identifier).sheet1
        else:
            # Abre a planilha pela URL (usado para Inventory Management)
            sheet = gc.open_by_url(sheet_identifier).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        return data
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return None

# Seleção entre os tipos de dados
data_type = st.selectbox("Select Data Type", ["Customer Feedback", "Inventory Management"])

if data_type == "Customer Feedback":
    data = load_google_sheets(CUSTOMER_FEEDBACK_KEY, use_key=True)
else:
    data = load_google_sheets(SHEET_URL_INVENTORY, use_key=False)

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

            # Gráfico: Vendas ao Longo do Tempo
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

            # Gráfico: Vendas por Região
            st.write("### Sales by Region")
            sales_by_region = data.groupby("Region")["Sales"].sum()
            fig, ax = plt.subplots()
            sales_by_region.plot(ax=ax, kind="bar", color="#ffbb7c")
            ax.set_title("Sales by Region")
            ax.set_ylabel("Sales")
            ax.set_xlabel("Region")
            st.pyplot(fig)

            # Cálculo do Crescimento da Receita
            if "Growth Rate" not in data.columns:
                data["Growth Rate"] = data["Revenue"].pct_change() * 100
            avg_growth_rate = data["Growth Rate"].mean()
            st.metric("Average Growth Rate", f"{avg_growth_rate:.2f}%")

            # Top 5 Clientes por Receita
            st.write("### Top 5 Customers by Revenue")
            top_customers = data.groupby("Customer_ID")["Revenue"].sum().nlargest(5)
            st.table(top_customers)
else:
    pass
