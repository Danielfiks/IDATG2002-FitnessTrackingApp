import streamlit as st
import mysql.connector
from pages.login_registration import show_login_page,show_registration_page
from pages.training_log import show_training_log
from pages.goals import show_goals_page
from pages.health_metrics import show_health_metrics_page

# --- DATABASE CONNECTION ---
def get_connection():
    # Establish connection to the local MySQL database using provided credentials and socket
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Oblig4",
        unix_socket="/opt/lampp/var/mysql/mysql.sock"
    )

# --- MAIN APP CONTROL FLOW ---
def main():
    # Set wide layout and title for the browser tab
    st.set_page_config(page_title="Fitness Tracking App", layout="wide")
    
    # Initialize session state for user authentication status
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'reg_mode' not in st.session_state:
        st.session_state['reg_mode'] = False

    # Logic to switch between Login, Registration, and the Dashboard
    if not st.session_state['logged_in']:
        if st.session_state['reg_mode']:
            show_registration_page(get_connection())
        else:
            show_login_page(get_connection())
    else:
        # Sidebar for navigation and logout
        with st.sidebar:
            st.title("Fitness Tracking App")
            st.write(f"Logged in: **{st.session_state.get('user_name')}**")
            st.divider()
            choice = st.radio("Navigation", ["Training Log", "Goals and Progress", "Health Metrics"])
            st.divider()
            # Clear session state on logout
            if st.button("Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        # Page routing based on sidebar selection
        if choice == "Training Log":
            show_training_log(get_connection())
        elif choice == "Goals and Progress":
            show_goals_page(get_connection())
        elif choice == "Health Metrics":
            show_health_metrics_page(get_connection())

# Execution entry point
if __name__ == "__main__":
    main()