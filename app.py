import streamlit as st
from core import services as serv

st.set_page_config(page_title="Hostel Meal System", page_icon="🏠", layout="centered", initial_sidebar_state="collapsed")

def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            html, body, [class*="st-"], [class*="css-"] { font-family: 'Inter', sans-serif; }
            .st-emotion-cache-1y4p8pa { padding-top: 2rem; }
        </style>
    """, unsafe_allow_html=True)

load_css()
serv.setup_database()

def register_hostel_page():
    st.title("Hostel Registration")
    with st.form("hostel_reg_form"):
        st.header("Create Your Hostel's Account")
        hostel_name = st.text_input("Hostel Name", placeholder="e.g., North Star Hostel")
        admin_user_id = st.text_input("Choose an Admin User ID", placeholder="e.g., admin_john")
        admin_password = st.text_input("Choose an Admin Password", type="password")
        submitted = st.form_submit_button("Register Hostel", use_container_width=True, type="primary")
        if submitted:
            if all([hostel_name, admin_user_id, admin_password]):
                with st.spinner("Registering..."):
                    hostel_id = serv.register_hostel(hostel_name, admin_user_id, admin_password)
                if hostel_id:
                    st.session_state.page = 'registration_success'
                    st.session_state.new_hostel_id = hostel_id
                    st.session_state.new_hostel_name = hostel_name
                    st.rerun()
                else:
                    st.error("Registration failed. A hostel with this name or an admin with this User ID might already exist.")
            else:
                st.warning("All fields are required.")
    if st.button("← Back to Welcome", use_container_width=True):
        st.session_state.page = 'welcome'
        st.rerun()

def login_page():
    st.title("Hostel Login")
    if 'hostel_id' not in st.session_state:
        st.header("Step 1: Enter Your Hostel ID")
        hostel_id_input = st.text_input("Hostel ID", key='hostel_id_input', placeholder="e.g., NORT1234")
        if st.button("Continue", use_container_width=True, type="primary"):
            if not hostel_id_input:
                st.error("Hostel ID cannot be empty.")
            elif serv.check_hostel_id_exists(hostel_id_input):
                st.session_state.hostel_id = hostel_id_input
                st.rerun()
            else:
                st.error("Hostel ID not found.")
        if st.button("← Back", use_container_width=True):
            st.session_state.page = 'welcome'
            st.rerun()
        return

    hostel_name = serv.get_hostel_name(st.session_state.hostel_id)
    st.header(f"Step 2: Login to {hostel_name}")
    with st.form("login_form"):
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login", use_container_width=True, type="primary")
        if submitted:
            if not user_id or not password:
                st.error("User ID and Password are required.")
            else:
                role = serv.authenticate_user(st.session_state.hostel_id, user_id, password)
                if role:
                    st.session_state.logged_in = True
                    st.session_state.user_id = user_id.upper()
                    st.session_state.role = role
                    st.toast(f"Welcome, {user_id}!", icon="👋")
                    st.switch_page("pages/student_dashboard.py" if role == 'student' else "pages/admin_dashboard.py")
                else:
                    st.error("Invalid credentials.")
    if st.button("← Use a different Hostel ID", use_container_width=True):
        del st.session_state.hostel_id
        st.rerun()

def welcome_page():
    # ... (welcome_page and registration_success_page are unchanged)
    st.title("Welcome to the Hostel Meal Management Platform")
    st.write("A smart solution to reduce food waste and manage hostel messes efficiently.")
    col1, col2 = st.columns(2)
    with col1:
        with st.container(border=True):
            st.subheader("Existing User?")
            if st.button("Login to Your Hostel", use_container_width=True):
                st.session_state.page = 'login'
                st.rerun()
    with col2:
        with st.container(border=True):
            st.subheader("New Hostel?")
            if st.button("Register Your Hostel", use_container_width=True, type="primary"):
                st.session_state.page = 'register'
                st.rerun()

def registration_success_page():
    st.title("Registration Successful")
    st.success(f"Your hostel, **{st.session_state.new_hostel_name}**, has been registered.")
    st.subheader("Your Unique Hostel ID")
    st.code(st.session_state.new_hostel_id, language=None)
    st.warning("**IMPORTANT:** Save this Hostel ID. You and your students need it to log in.")
    if st.button("Proceed to Login", use_container_width=True, type="primary"):
        st.session_state.page = 'login'
        st.session_state.hostel_id_input = st.session_state.new_hostel_id
        st.rerun()

# --- Main App Router ---
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if st.session_state.logged_in:
    st.switch_page("pages/student_dashboard.py" if st.session_state.role == 'student' else "pages/admin_dashboard.py")
else:
    page = st.session_state.get('page', 'welcome')
    if page == 'register':
        register_hostel_page()
    elif page == 'registration_success':
        registration_success_page()
    elif page == 'login':
        login_page()
    else:
        welcome_page()
