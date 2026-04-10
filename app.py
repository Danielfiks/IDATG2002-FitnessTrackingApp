import os
import hmac
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

def check_password():
    """Returns `True` if the user had a correct password."""

    def login_form():
        """Form to collect username & password"""
        with st.form("Credentials"):
            st.text_input("Username", key="username")
            st.text_input("Password", type="password", key="password")
            st.form_submit_button("Log in", on_click=password_entered)

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if os.environ.get(f"{st.session_state["username"].upper()}_STREAMLIT_PASSWORD") \
            and hmac.compare_digest(
            st.session_state["password"],
            os.environ.get(f"{st.session_state["username"].upper()}_STREAMLIT_PASSWORD")
        ):
            st.session_state["password_correct"] = True
            # Don't store the username or password in the session
            del st.session_state["password"]
            del st.session_state["username"]
        else:
            st.session_state["password_correct"] = False

    # Return True if the username + password is validated.
    if st.session_state.get("password_correct", False):
        return True

    # Show inputs for username + password.
    login_form()
    if "password_correct" in st.session_state:
        st.error("User not known or password incorrect")
    return False

if not check_password():
    st.stop()