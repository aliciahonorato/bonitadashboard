import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt
import datetime

# --------------------- Custom CSS & Branding ---------------------
def set_custom_css():
    st.markdown("""
        <style>
            /* Modern design with custom fonts and colors */
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
            /* Header styling */
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
st.markdown("<div class='header-title'>Bonita Brazilian Braids Dashboard</div>", unsafe_allow_html=True)

# --------------------- Google Sheets Configuration ---------------------
CUSTOMER_FEEDBACK_URL = (
    "https://docs.google.com/spreadsheets/d/1ONZmz4ZLIw8-IzjeNvdJzMMKJZ0EoJuLxUQqCeMzm5E/"
    "edit?resourcekey=&gid=1459096233#gid=1459096233"
)
INVENTORY_URL = (
    "https://docs.google.com/spreadsheets/d/1g28kftFDBk6nrgpj8qgmEH5QId5stT1p55saBTsctaU/"
    "edit?resourcekey=&gid=375516129#gid=375516129"
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
    try:
        sheet = gc.open_by_url(sheet_url).sheet1
        data = pd.DataFrame(sheet.get_all_records())
        data.columns = data.columns.str.strip()  # Clean column names
        return data
    except Exception as e:
        st.error(f"Error loading the Google Sheet: {e}")
        return None

# --------------------- Data Type Selection ---------------------
data_type = st.sidebar.selectbox("Select Data Type", ["Customer Feedback", "Inventory Management"])

if data_type == "Customer Feedback":
    data = load_google_sheet(CUSTOMER_FEEDBACK_URL)
else:
    data = load_google_sheet(INVENTORY_URL)

if data is None or data.empty:
    st.error("No data available.")
    st.stop()

st.sidebar.markdown("### Data Preview")
st.dataframe(data.head(5))

# --------------------- Layout with Tabs ---------------------
tabs = st.tabs(["Summary", "Analysis", "Recommendations & Action Items"])

# ##################################################################
# --------------------- Tab 1: Summary ---------------------
with tabs[0]:
    st.markdown("## General Overview")
    if data_type == "Inventory Management":
        # Preprocess Inventory Data
        data["Carimbo de data/hora"] = pd.to_datetime(data["Carimbo de data/hora"], errors='coerce')
        total_revenue = pd.to_numeric(data["Total Revenue for the day ($)"], errors='coerce').sum()
        total_expenses = pd.to_numeric(data["Total Expenses for the day ($)"], errors='coerce').sum()
        net_profit = pd.to_numeric(data["Net Profit for the day ($)"], errors='coerce').sum()
        total_appointments = pd.to_numeric(data["Number of appointments completed today:"], errors='coerce').sum()
        total_returning = pd.to_numeric(data["Total number of returning customers today:"], errors='coerce').sum()
        total_new = pd.to_numeric(data["Total number of new customers today:"], errors='coerce').sum()
        retention_rate = (total_returning / (total_returning + total_new)) * 100 if (total_returning + total_new) > 0 else 0

        # Display key metrics in columns
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Revenue", f"${total_revenue:,.2f}")
        col2.metric("Total Expenses", f"${total_expenses:,.2f}")
        col3.metric("Net Profit", f"${net_profit:,.2f}")

        col4, col5 = st.columns(2)
        col4.metric("Total Appointments", f"{total_appointments:.0f}")
        col5.metric("Retention Rate", f"{retention_rate:.2f}%")
    
    else:
        st.markdown("## Customer Feedback Overview")
        if "How satisfied are you with our services?" in data.columns:
            satisfaction_counts = data["How satisfied are you with our services?"].value_counts().to_dict()
            st.write("### Customer Satisfaction:")
            for level, count in satisfaction_counts.items():
                st.write(f"- **{level}**: {count} responses")
        st.write("Explore the following tabs for detailed analysis and actionable recommendations.")

# ##################################################################
# --------------------- Tab 2: Analysis ---------------------
with tabs[1]:
    st.markdown("## Detailed Analysis")
    
    if data_type == "Inventory Management":
        st.markdown("### Revenue Over Time")
        timeframe = st.selectbox("Select Timeframe", ["Daily", "Weekly", "Monthly"], key="timeframe")
        if timeframe == "Daily":
            rev_time = (
                data.groupby(data["Carimbo de data/hora"].dt.date)["Total Revenue for the day ($)"]
                .sum()
                .reset_index()
            )
            rev_time.columns = ["Date", "Revenue"]
            x_field = "Date"
        elif timeframe == "Weekly":
            rev_time = (
                data.groupby(data["Carimbo de data/hora"].dt.to_period("W"))["Total Revenue for the day ($)"]
                .sum()
                .reset_index()
            )
            rev_time["Date"] = rev_time["Carimbo de data/hora"].astype(str)
            rev_time = rev_time.drop("Carimbo de data/hora", axis=1)
            rev_time.columns = ["Revenue", "Date"]
            x_field = "Date"
        else:
            rev_time = (
                data.groupby(data["Carimbo de data/hora"].dt.to_period("M"))["Total Revenue for the day ($)"]
                .sum()
                .reset_index()
            )
            rev_time["Date"] = rev_time["Carimbo de data/hora"].astype(str)
            rev_time = rev_time.drop("Carimbo de data/hora", axis=1)
            rev_time.columns = ["Revenue", "Date"]
            x_field = "Date"

        chart_rev = (
            alt.Chart(rev_time)
            .mark_line(point=alt.OverlayMarkDef(color="#C17544", size=80))
            .encode(
                x=alt.X(f"{x_field}:T", title="Date"),
                y=alt.Y("Revenue:Q", title="Revenue ($)"),
                tooltip=[f"{x_field}:T", "Revenue:Q"]
            )
            .properties(
                title=f"Revenue Over Time ({timeframe})",
                width=700,
                height=400
            )
            .interactive()
        )
        st.altair_chart(chart_rev, use_container_width=True)
    
    else:
        st.markdown("### Customer Feedback Analysis")
        # Satisfaction Chart: Using a donut chart for a modern look
        if "How satisfied are you with our services?" in data.columns:
            satisfaction = data["How satisfied are you with our services?"].value_counts().reset_index()
            satisfaction.columns = ["Satisfaction", "Count"]
            chart_sat = (
                alt.Chart(satisfaction)
                .mark_arc(innerRadius=50, stroke="#fff")
                .encode(
                    theta=alt.Theta(field="Count", type="quantitative"),
                    color=alt.Color(field="Satisfaction", type="nominal", scale=alt.Scale(range=["#F7B26A", "#C17544", "#FFD700"])),
                    tooltip=["Satisfaction:N", "Count:Q"]
                )
                .properties(title="Satisfaction Distribution", width=400, height=400)
                .interactive()
            )
            st.altair_chart(chart_sat, use_container_width=True)
        
        # Visit Frequency Chart: Bar chart with rounded corners
        if "How often do you visit a hair salon?" in data.columns:
            freq = data["How often do you visit a hair salon?"].value_counts().reset_index()
            freq.columns = ["Frequency", "Count"]
            chart_freq = (
                alt.Chart(freq)
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

# ##################################################################
# --------------------- Tab 3: Recommendations & Action Items ---------------------
with tabs[2]:
    st.markdown("## Recommendations & Action Items")
    if data_type == "Inventory Management":
        # Calculate weekly performance
        current_week = pd.Timestamp.now().isocalendar().week
        weekly_data = data[data["Carimbo de data/hora"].dt.isocalendar().week == current_week]
        current_week_revenue = pd.to_numeric(weekly_data["Total Revenue for the day ($)"], errors='coerce').sum()
        current_week_appointments = pd.to_numeric(weekly_data["Number of appointments completed today:"], errors='coerce').sum()

        previous_week = current_week - 1
        previous_week_data = data[data["Carimbo de data/hora"].dt.isocalendar().week == previous_week]
        previous_week_revenue = pd.to_numeric(previous_week_data["Total Revenue for the day ($)"], errors='coerce').sum()
        previous_week_appointments = pd.to_numeric(previous_week_data["Number of appointments completed today:"], errors='coerce').sum()

        st.markdown("### Performance Insights")
        # Revenue insight
        if current_week_revenue < previous_week_revenue:
            st.error(
                f"Current week revenue (${current_week_revenue:,.2f}) is lower than last week's (${previous_week_revenue:,.2f}).\n"
                "Recommendation: Increase marketing efforts, run promotions or discounts, and review customer feedback for service improvements."
            )
        else:
            st.success("Revenue is stable or growing. Keep up the good work!")
        
        # Appointments insight
        if current_week_appointments < previous_week_appointments:
            st.error(
                f"Current week appointments ({current_week_appointments:.0f}) are lower than last week's ({previous_week_appointments:.0f}).\n"
                "Recommendation: Send reminders, offer discounts, or launch loyalty programs to boost customer visits."
            )
        else:
            st.success("Appointments are stable or increasing. Great job!")
    
    else:
        st.markdown("### Customer Feedback Recommendations")
        if "What could we improve to enhance your experience?" in data.columns:
            improvements = data["What could we improve to enhance your experience?"].dropna().tolist()
            if improvements:
                st.write("Key improvement suggestions from customers:")
                for i, feedback in enumerate(improvements[:5], start=1):
                    st.write(f"{i}. {feedback}")
            else:
                st.success("No negative feedback detected. Keep up the excellent work!")
        else:
            st.write("Not enough data to generate recommendations.")
