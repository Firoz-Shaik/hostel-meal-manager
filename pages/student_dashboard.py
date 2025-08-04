import streamlit as st
from datetime import datetime, time, timedelta
from core import services as serv
import pandas as pd
from utils import helpers as help

st.set_page_config(page_title="Student Dashboard", page_icon="🎓", layout="wide")

def load_css():
    st.markdown("""
        <style>
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
            @import url('https://fonts.googleapis.com/icon?family=Material+Icons');
            html, body, [class*="st-"], [class*="css-"] {
                font-family: 'Inter', sans-serif;
            }
            
            /* Fix for icon rendering issues */
            .stButton > button {
                font-family: 'Inter', sans-serif;
            }
            
            /* Ensure emoji icons render properly */
            .stMarkdown {
                font-family: 'Inter', sans-serif;
            }
            
            /* Sidebar styling */
            .css-1d391kg {
                font-family: 'Inter', sans-serif;
            }
            
            /* Fix Material Icons in sidebar */
            .material-icons {
                font-family: 'Material Icons';
                font-weight: normal;
                font-style: normal;
                font-size: 24px;
                line-height: 1;
                letter-spacing: normal;
                text-transform: none;
                display: inline-block;
                white-space: nowrap;
                word-wrap: normal;
                direction: ltr;
                -webkit-font-feature-settings: 'liga';
                -webkit-font-smoothing: antialiased;
            }
            
            /* Override any broken icon display */
            [class*="css-"] .material-icons {
                font-family: 'Material Icons' !important;
            }
        </style>
    """, unsafe_allow_html=True)

load_css()

if not st.session_state.get("logged_in"):
    st.error("Please log in to access this page.")
    st.page_link("app.py", label="Go to Login", icon="🏠")
    st.stop()

# Use the safe async runner
hostel_name = help.run_async(serv.get_hostel_name(st.session_state.hostel_id))
with st.sidebar:
    st.markdown("### Hostel Information")
    st.markdown(f"**Hostel:** {hostel_name}")
    st.markdown(f"**User:** `{st.session_state.user_id}`")
    st.divider()
    if st.button("Logout", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.switch_page("app.py")

st.title(f"🎓 Welcome, {st.session_state['user_id']}!")

CUTOFF_TIME = time(18, 0)
now = datetime.now()
next_day_str = (now + timedelta(days=1)).strftime("%A, %B %d")

st.info(f"Meal choices for **{next_day_str}** are managed below.", icon="🕒")

with st.container(border=True):
    if now.time() < CUTOFF_TIME:
        st.write("#### Update Your Meal Choices for Tomorrow")
        with st.form("meal_form"):
            cols = st.columns(3)
            b = cols[0].checkbox("🍳 Breakfast", value=True)
            l = cols[1].checkbox("🥗 Lunch", value=True)
            d = cols[2].checkbox("🍲 Dinner", value=True)
            if st.form_submit_button("Confirm My Choices", use_container_width=True, type="primary"):
                help.run_async(serv.submit_meal_response(st.session_state.hostel_id, st.session_state.user_id, b, l, d))
                st.toast("Your choices have been saved!", icon="✅")
    else:
        st.write("#### Your Meal Passes for Tomorrow")
        st.warning("The selection deadline has passed. Show these passes at the mess.", icon="🎟️")
        
        meal_info = help.run_async(serv.get_student_meal_info(st.session_state.hostel_id, st.session_state.user_id))
        if meal_info:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.subheader("🍳 Breakfast")
                if meal_info['breakfast']:
                    st.code(meal_info['breakfast_pass'], language=None)
                else:
                    st.info("Not Attending")
            with col2:
                st.subheader("🥗 Lunch")
                if meal_info['lunch']:
                    st.code(meal_info['lunch_pass'], language=None)
                else:
                    st.info("Not Attending")
            with col3:
                st.subheader("🍲 Dinner")
                if meal_info['dinner']:
                    st.code(meal_info['dinner_pass'], language=None)
                else:
                    st.info("Not Attending")
        else:
            st.info("You did not make a selection for tomorrow. It is assumed you are attending all meals, but no passes were generated. Please contact your admin.")