import streamlit as st
import pandas as pd
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

# File paths for local Excel files
CUSTOMER_FEEDBACK_FILE = "/mnt/data/Bonita Brazilian Braids Customer Experience (Responses)"
BUSINESS_TRACKING_FILE = "/mnt/data/Bonita Brazilian Braids -  Salon Business & Financial Tracking  (respostas)"

@st.cache_data
def load_excel_file(file_path):
    try:
        data = pd.read_excel(file_path)
        # Remove any extra whitespace from the column names
        data.columns = data.columns.str.strip()
        return data
    except Exception as e:
        st.error(f"Error loading file {file_path}: {e}")
        return None

# Select the data type to display
data_type = st.selectbox("Select Data Type", ["Customer Feedback", "Inventory Management"])

if data_type == "Customer Feedback":
    data = load_excel_file(CUSTOMER_FEEDBACK_FILE)
else:
    data = load_excel_file(BUSINESS_TRACKING_FILE)

if data is not None and not data.empty:
    st.write(f"### Loaded Data: {data_type}")
    st.dataframe(data)
    
    if data_type == "Inventory Management":
        # Define required columns for the Salon Business Tracking data
        required_columns = [
            "Carimbo de data/hora",
            "Total Revenue for the day ($)",
            "Total Expenses for the day ($)",
            "Net Profit for the day ($)",
            "Number of appointments completed today:",
            "Total number of returning customers today:",
            "Total number of new customers today:"
        ]
        
        # Check if all required columns exist
        if not all(col in data.columns for col in required_columns):
            st.error(f"The data must contain: {', '.join(required_columns)}")
        else:
            # Convert the timestamp column to datetime
            data["Carimbo de data/hora"] = pd.to_datetime(data["Carimbo de data/hora"], errors='coerce')
            
            # Calculate key metrics (ensuring numeric conversion)
            total_revenue = pd.to_numeric(data["Total Revenue for the day ($)"], errors='coerce').sum()
            total_expenses = pd.to_numeric(data["Total Expenses for the day ($)"], errors='coerce').sum()
            net_profit = pd.to_numeric(data["Net Profit for the day ($)"], errors='coerce').sum()
            total_appointments = pd.to_numeric(data["Number of appointments completed today:"], errors='coerce').sum()
            
            total_returning = pd.to_numeric(data["Total number of returning customers today:"], errors='coerce').sum()
            total_new = pd.to_numeric(data["Total number of new customers today:"], errors='coerce').sum()
            if (total_returning + total_new) > 0:
                retention_rate = (total_returning / (total_returning + total_new)) * 100
            else:
                retention_rate = 0
            
            st.metric("Total Revenue", f"${total_revenue:,.2f}")
            st.metric("Total Expenses", f"${total_expenses:,.2f}")
            st.metric("Net Profit", f"${net_profit:,.2f}")
            st.metric("Total Appointments", f"{total_appointments:.0f}")
            st.metric("Customer Retention Rate", f"{retention_rate:.2f}%")
            
            # Chart: Revenue over time
            st.write("### Revenue Over Time")
            timeframe = st.selectbox("Choose timeframe", ["Daily", "Weekly", "Monthly"])
            if timeframe == "Daily":
                rev_over_time = data.groupby(data["Carimbo de data/hora"].dt.date)["Total Revenue for the day ($)"].sum()
            elif timeframe == "Weekly":
                rev_over_time = data.groupby(data["Carimbo de data/hora"].dt.to_period("W"))["Total Revenue for the day ($)"].sum()
            else:
                rev_over_time = data.groupby(data["Carimbo de data/hora"].dt.to_period("M"))["Total Revenue for the day ($)"].sum()
            
            fig, ax = plt.subplots()
            rev_over_time.plot(ax=ax, kind="line")
            ax.set_title(f"Revenue ({timeframe})")
            ax.set_xlabel("Time")
            ax.set_ylabel("Revenue")
            st.pyplot(fig)
else:
    st.write("No data to display.")
