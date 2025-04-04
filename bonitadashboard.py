import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
import altair as alt

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

# Set scopes and authenticate via your service account credentials
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
        # Clean up column names
        data.columns = data.columns.str.strip()
        return data
    except Exception as e:
        st.error(f"Error loading Google Sheet: {e}")
        return None

# Let the user choose which data type to view
data_type = st.selectbox("Select Data Type", ["Customer Feedback", "Inventory Management"])

if data_type == "Customer Feedback":
    data = load_google_sheet(CUSTOMER_FEEDBACK_URL)
else:
    data = load_google_sheet(INVENTORY_URL)

if data is not None and not data.empty:
    st.write(f"### Loaded Data: {data_type}")
    st.dataframe(data)

    if data_type == "Inventory Management":
        # Define required columns for Inventory Management data
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

            # Display key metrics in columns
            col1, col2, col3 = st.columns(3)
            col1.metric("Total Revenue", f"${total_revenue:,.2f}")
            col2.metric("Total Expenses", f"${total_expenses:,.2f}")
            col3.metric("Net Profit", f"${net_profit:,.2f}")

            col4, col5 = st.columns(2)
            col4.metric("Total Appointments", f"{total_appointments:.0f}")
            col5.metric("Customer Retention Rate", f"{retention_rate:.2f}%")

            # Revenue Over Time chart using Altair
            st.write("### Revenue Over Time")
            timeframe = st.selectbox("Choose timeframe", ["Daily", "Weekly", "Monthly"], key="timeframe")
            if timeframe == "Daily":
                rev_time = data.groupby(data["Carimbo de data/hora"].dt.date)["Total Revenue for the day ($)"].sum().reset_index()
                rev_time.columns = ["Date", "Revenue"]
                x_field = "Date"
            elif timeframe == "Weekly":
                rev_time = data.groupby(data["Carimbo de data/hora"].dt.to_period("W"))["Total Revenue for the day ($)"].sum().reset_index()
                rev_time["Date"] = rev_time["Carimbo de data/hora"].astype(str)
                rev_time = rev_time.drop("Carimbo de data/hora", axis=1)
                rev_time.columns = ["Revenue", "Date"]
                x_field = "Date"
            else:
                rev_time = data.groupby(data["Carimbo de data/hora"].dt.to_period("M"))["Total Revenue for the day ($)"].sum().reset_index()
                rev_time["Date"] = rev_time["Carimbo de data/hora"].astype(str)
                rev_time = rev_time.drop("Carimbo de data/hora", axis=1)
                rev_time.columns = ["Revenue", "Date"]
                x_field = "Date"

            chart_rev = alt.Chart(rev_time).mark_line(point=True).encode(
                x=alt.X(f"{x_field}:T", title="Time"),
                y=alt.Y("Revenue:Q", title="Revenue")
            ).properties(
                title=f"Revenue Over Time ({timeframe})",
                width=700,
                height=400
            )
            st.altair_chart(chart_rev, use_container_width=True)

            # ---------------- Recommendations Section ----------------
            st.write("### Recommendations & Action Items")
            # Calculate current and previous week performance based on ISO week numbers
            current_week = pd.Timestamp.now().isocalendar().week
            weekly_data = data[data["Carimbo de data/hora"].dt.isocalendar().week == current_week]
            current_week_revenue = pd.to_numeric(weekly_data["Total Revenue for the day ($)"], errors='coerce').sum()
            current_week_appointments = pd.to_numeric(weekly_data["Number of appointments completed today:"], errors='coerce').sum()
            
            previous_week = current_week - 1
            previous_week_data = data[data["Carimbo de data/hora"].dt.isocalendar().week == previous_week]
            previous_week_revenue = pd.to_numeric(previous_week_data["Total Revenue for the day ($)"], errors='coerce').sum()
            previous_week_appointments = pd.to_numeric(previous_week_data["Number of appointments completed today:"], errors='coerce').sum()
            
            # Recommendations based on revenue
            if current_week_revenue < previous_week_revenue:
                st.write("- **Revenue Decline:** Your revenue for the current week (${:.2f}) is lower than last week (${:.2f}). Consider boosting your marketing efforts, running promotions or discounts, and reviewing customer feedback to identify service improvements.".format(current_week_revenue, previous_week_revenue))
            else:
                st.write("- **Revenue is stable or improving.** Keep up the good work!")
            
            # Recommendations based on customer appointments
            if current_week_appointments < previous_week_appointments:
                st.write("- **Customer Visits Decline:** The number of appointments this week ({:.0f}) is lower than last week ({:.0f}). Consider targeted promotions, sending reminder emails to loyal customers, or offering referral incentives.".format(current_week_appointments, previous_week_appointments))
            else:
                st.write("- **Customer appointments are stable or increasing.** Great job!")
    else:
        # Customer Feedback Insights
        st.write("### Customer Feedback Insights")
        
        # 1. Overall Satisfaction
        if "How satisfied are you with our services?" in data.columns:
            satisfaction = data["How satisfied are you with our services?"].value_counts().reset_index()
            satisfaction.columns = ["Satisfaction", "Count"]
            chart_sat = alt.Chart(satisfaction).mark_bar().encode(
                x=alt.X("Satisfaction:N", title="Satisfaction Rating"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Satisfaction Ratings Distribution", width=700, height=400)
            st.altair_chart(chart_sat, use_container_width=True)
        
        # 2. Service Preferences
        if "What services do you usually get? (Check all that apply)" in data.columns:
            # Assume responses are comma-separated values
            service_series = data["What services do you usually get? (Check all that apply)"].dropna().apply(lambda x: [s.strip() for s in x.split(",")])
            services = [item for sublist in service_series for item in sublist]
            service_counts = pd.Series(services).value_counts().reset_index()
            service_counts.columns = ["Service", "Count"]
            chart_services = alt.Chart(service_counts).mark_bar().encode(
                x=alt.X("Service:N", title="Service"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Service Preferences", width=700, height=400)
            st.altair_chart(chart_services, use_container_width=True)
        
        # 3. Opportunity for New Services (free text responses)
        if "Is there a service you wish we offered but currently don’t?" in data.columns:
            st.write("### Opportunity for New Services")
            new_services = data["Is there a service you wish we offered but currently don’t?"].dropna().tolist()
            if new_services:
                st.write("Some customer suggestions:")
                for suggestion in new_services[:5]:
                    st.write("- " + suggestion)
            else:
                st.write("No suggestions provided.")
        
        # 4. Net Promoter Insights
        if "Would you recommend us to a friend?" in data.columns:
            promoter = data["Would you recommend us to a friend?"].value_counts().reset_index()
            promoter.columns = ["Response", "Count"]
            chart_promoter = alt.Chart(promoter).mark_bar().encode(
                x=alt.X("Response:N", title="Response"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Would you recommend us to a friend?", width=700, height=400)
            st.altair_chart(chart_promoter, use_container_width=True)
        
        # 5. Customer Demographics
        st.write("### Customer Demographics")
        if "Age Range" in data.columns:
            age = data["Age Range"].value_counts().reset_index()
            age.columns = ["Age Range", "Count"]
            chart_age = alt.Chart(age).mark_bar().encode(
                x=alt.X("Age Range:N", title="Age Range"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Age Distribution", width=700, height=400)
            st.altair_chart(chart_age, use_container_width=True)
        if "Gender Identity" in data.columns:
            gender = data["Gender Identity"].value_counts().reset_index()
            gender.columns = ["Gender", "Count"]
            chart_gender = alt.Chart(gender).mark_bar().encode(
                x=alt.X("Gender:N", title="Gender Identity"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Gender Distribution", width=700, height=400)
            st.altair_chart(chart_gender, use_container_width=True)
        if "Which area do you live in?" in data.columns:
            area = data["Which area do you live in?"].value_counts().reset_index()
            area.columns = ["Area", "Count"]
            chart_area = alt.Chart(area).mark_bar().encode(
                x=alt.X("Area:N", title="Area"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Geographic Distribution", width=700, height=400)
            st.altair_chart(chart_area, use_container_width=True)
        
        # 6. Visit Frequency Analysis
        if "How often do you visit a hair salon?" in data.columns:
            freq = data["How often do you visit a hair salon?"].value_counts().reset_index()
            freq.columns = ["Frequency", "Count"]
            chart_freq = alt.Chart(freq).mark_bar().encode(
                x=alt.X("Frequency:N", title="Visit Frequency"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Visit Frequency Distribution", width=700, height=400)
            st.altair_chart(chart_freq, use_container_width=True)
        
        # 7. Qualitative Feedback for Improvements
        if "What could we improve to enhance your experience?" in data.columns:
            st.write("### Qualitative Feedback for Improvements")
            improvements = data["What could we improve to enhance your experience?"].dropna().tolist()
            if improvements:
                st.write("Some suggestions:")
                for feedback in improvements[:5]:
                    st.write("- " + feedback)
            else:
                st.write("No feedback provided.")
        
        # 8. Marketing Channel Effectiveness
        if "How did you hear about us?" in data.columns:
            channel = data["How did you hear about us?"].value_counts().reset_index()
            channel.columns = ["Channel", "Count"]
            chart_channel = alt.Chart(channel).mark_bar().encode(
                x=alt.X("Channel:N", title="Channel"),
                y=alt.Y("Count:Q", title="Count")
            ).properties(title="Marketing Channel Effectiveness", width=700, height=400)
            st.altair_chart(chart_channel, use_container_width=True)
else:
    st.write("No data to display.")
