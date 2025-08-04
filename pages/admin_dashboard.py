import streamlit as st
import pandas as pd
from datetime import datetime, time
from core import services as serv

st.set_page_config(page_title="Admin Dashboard", page_icon="⚙️", layout="wide")

def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            html, body, [class*="st-"], [class*="css-"] { font-family: 'Inter', sans-serif; }
        </style>
    """, unsafe_allow_html=True)

load_css()

if not st.session_state.get("logged_in") or st.session_state.get("role") != 'admin':
    st.error("You must be an admin to access this page.")
    st.page_link("app.py", label="Go to Login", icon="�")
    st.stop()

with st.sidebar:
    st.header(f"Hostel: {serv.get_hostel_name(st.session_state.hostel_id)}")
    st.write(f"User: `{st.session_state.user_id}`")
    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

def analytics_tab(hostel_id):
    st.header("Live Meal Count for Tomorrow")
    live_counts = serv.get_live_meal_counts(hostel_id)
    with st.container(border=True):
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("🍳 Live Breakfasts", live_counts['breakfast'])
        col2.metric("🥗 Live Lunches", live_counts['lunch'])
        col3.metric("🍲 Live Dinners", live_counts['dinner'])
        col4.metric("👥 Responses So Far", f"{live_counts['responded']}/{live_counts['total']}")
        if st.button("Refresh Counts"): st.rerun()
    st.header("Final Daily Report")
    if datetime.now().time() > time(18, 0):
        if st.button("Generate Final Report & Meal Passes", type="primary"):
            with st.spinner("Generating..."):
                message = serv.generate_daily_report_and_passes(hostel_id)
                st.success(message)
    else:
        st.info("Final report generation is available after 6:00 PM.", icon="🕒")

def user_management_tab(hostel_id, current_admin_id):
    st.header("Manage Users")
    
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Add a Single Student")
            with st.form("add_student_form", clear_on_submit=True):
                new_user_id = st.text_input("New Student User ID")
                new_password = st.text_input("New Student Password", type="password")
                if st.form_submit_button("Add Student", use_container_width=True, type="primary"):
                    if serv.add_user(hostel_id, new_user_id, new_password, 'student', current_admin_id):
                        st.success(f"Student '{new_user_id}' added.")
                    else:
                        st.error(f"Student '{new_user_id}' already exists.")
        
        with st.container(border=True):
            st.subheader("Add a New Admin")
            with st.form("add_admin_form", clear_on_submit=True):
                new_admin_id = st.text_input("New Admin User ID")
                admin_password = st.text_input("New Admin Password", type="password")
                if st.form_submit_button("Add Admin", use_container_width=True, type="primary"):
                    if serv.add_user(hostel_id, new_admin_id, admin_password, 'admin', current_admin_id):
                        st.success(f"Admin '{new_admin_id}' added.")
                    else:
                        st.error(f"Admin '{new_admin_id}' already exists.")

    with col2:
        with st.container(border=True):
            st.subheader("Change a User's Password")
            with st.form("change_password_form", clear_on_submit=True):
                user_to_change = st.text_input("User ID to Change")
                new_password = st.text_input("New Password", type="password")
                if st.form_submit_button("Change Password", use_container_width=True, type="primary"):
                    if not user_to_change or not new_password:
                        st.warning("Please provide both a User ID and a new password.")
                    else:
                        if serv.change_password(hostel_id, user_to_change, new_password):
                            st.success(f"Password for '{user_to_change}' has been updated.")
                        else:
                            st.error(f"User '{user_to_change}' not found.")
        
        with st.container(border=True):
            st.subheader("Remove a User")
            st.warning("This action is permanent and cannot be undone.", icon="⚠️")
            with st.form("remove_user_form", clear_on_submit=True):
                user_to_remove = st.text_input("User ID to Remove")
                if st.form_submit_button("Remove User", use_container_width=True):
                    if not user_to_remove:
                        st.warning("Please enter a User ID to remove.")
                    elif user_to_remove.upper() == current_admin_id.upper():
                        st.error("You cannot remove yourself.")
                    else:
                        if serv.remove_user(hostel_id, user_to_remove):
                            st.success(f"User '{user_to_remove}' has been removed.")
                        else:
                            st.error(f"User '{user_to_remove}' not found.")

    with st.container(border=True):
        st.subheader("Add Students via CSV")
        st.markdown("📄 [Download Sample CSV](data:file/csv;base64,dXNlcl9pZCxwYXNzd29yZA0Kc3R1ZGVudDEscGFzczEyMw0Kc3R1ZGVudDIscGFzczQ1Ng0K)")
        uploaded_file = st.file_uploader("Upload a CSV file", type="csv")
        if uploaded_file:
            count, msg = serv.process_student_csv(hostel_id, uploaded_file, current_admin_id)
            st.success(msg) if count > 0 else st.error(msg)

def verification_tab(hostel_id):
    st.header("Meal Pass Verification")
    st.info("Mess staff can select a meal and enter the 3-digit pass code to verify.", icon="🎟️")
    
    meal_choice = st.selectbox("Select a Meal to Verify", ["Breakfast", "Lunch", "Dinner"])
    
    with st.container(border=True):
        st.subheader(f"Verify for: {meal_choice}")
        with st.form(f"{meal_choice}_verify_form"):
            pass_suffix = st.text_input("Enter 3-digit Pass Code", max_chars=3, key=f"{meal_choice}_pass")
            if st.form_submit_button("Verify Pass", use_container_width=True):
                if not pass_suffix:
                    st.warning("Pass code cannot be empty.")
                else:
                    msg, student = serv.verify_meal_pass(hostel_id, meal_choice, pass_suffix)
                    st.success(msg) if student else st.error(msg)

def bills_tab(hostel_id):
    st.header("Bills & Expenses")
    st.info("Keep a record of all mess-related expenses.", icon="💰")
    with st.container(border=True):
        st.subheader("Add New Bill")
        with st.form("add_bill_form", clear_on_submit=True):
            item_name = st.text_input("Item/Service Description")
            price = st.number_input("Price (₹)", min_value=0.0, format="%.2f")
            if st.form_submit_button("Add Bill", use_container_width=True, type="primary"):
                if item_name and price > 0:
                    serv.add_bill(hostel_id, item_name, price)
                    st.success("Bill added successfully!")
                else:
                    st.warning("Please provide both an item name and a valid price.")
    with st.container(border=True):
        st.subheader("Expense History")
        bills_df = serv.get_bills(hostel_id)
        if not bills_df.empty:
            bills_df['purchase_date'] = pd.to_datetime(bills_df['purchase_date']).dt.strftime('%d %B %Y')
            st.dataframe(bills_df, use_container_width=True, hide_index=True)
        else:
            st.info("No bills have been recorded yet.")

# --- Main Admin Dashboard ---
hostel_id = st.session_state.hostel_id
current_admin_id = st.session_state.user_id
summary = serv.get_hostel_summary(hostel_id)
st.title(f"⚙️ Admin Dashboard: {summary['name']}")
sum_col1, sum_col2, sum_col3 = st.columns(3)
sum_col1.metric("Hostel Name", summary['name'])
sum_col2.metric("Hostel ID", summary['id'])
sum_col3.metric("Total Students", summary['student_count'])

tab1, tab2, tab3, tab4 = st.tabs(["📊 Analytics", "👤 User Management", "🎟️ Meal Verification", "💰 Bills & Expenses"])
with tab1: analytics_tab(hostel_id)
with tab2: user_management_tab(hostel_id, current_admin_id)
with tab3: verification_tab(hostel_id)
with tab4: bills_tab(hostel_id)