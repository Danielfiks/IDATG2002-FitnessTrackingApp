import streamlit as st

# --- REGISTRATION PAGE ---
def show_registration_page(conn):
    # Create a centered layout using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Registration screen UI
        st.title("Register for Workout and Exercise")
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Email")
        new_pw = st.text_input("Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")
        
        # Button to create an account
        if st.button("Create Account", use_container_width=True):
            # Every field is Required: validation check
            if not new_name.strip() or not new_email.strip() or not new_pw.strip():
                st.error("All fields are required.")
            # Passwords should match: validation check
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            # If input is accepted: create a new user in the database
            else:
                # Check if a user with the email address exists. If not: create new user
                try:
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM User WHERE Email=%s", (new_email,))
                    if cursor.fetchone():
                        st.error("An account with this email already exists.")
                    else:
                        # Insert new user record into User table
                        cursor.execute("INSERT INTO User (Name, Email, Password) VALUES (%s, %s, %s)", 
                                       (new_name.strip(), new_email.strip(), new_pw))
                        conn.commit()
                        st.success("Registration successful! Please log in.")
                        # Toggle back to login mode and refresh app
                        st.session_state['reg_mode'] = False
                        st.rerun()
                    conn.close()
                # Catch unexpected database or connection errors
                except Exception as e:
                    st.error(f"Error during registration: {e}")
        
        # If the "Back to Login" button is pressed: return user to login screen
        if st.button("Back to Login", use_container_width=True):
            st.session_state['reg_mode'] = False
            # Go to main loop
            st.rerun()

# --- LOGIN PAGE ---
def show_login_page(conn):
    # Create a centered layout using columns
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        # Set up log in screen UI
        st.title("Workout and Exercise Login")
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        
        # Authorization logic
        if st.button("Access Dashboard", use_container_width=True):
            # Check if a field is empty
            if not email.strip() or not pw.strip():
                st.error("Please enter both email and password.")
            else:
                # Query database for matching user credentials
                try:
                    cursor = conn.cursor(dictionary=True)
                    cursor.execute("SELECT * FROM User WHERE Email=%s AND Password=%s", (email, pw))
                    user = cursor.fetchone()
                    conn.close()
                    # If user exists, initialize session state variables
                    if user:
                        st.session_state['logged_in'] = True
                        st.session_state['user_id'] = user['UserID']
                        st.session_state['user_name'] = user['Name']
                        # Send to main loop to display dashboard
                        st.rerun()
                    # Error handling for incorrect credentials
                    else:
                        st.error("Invalid credentials.")
                # Catch connection or SQL errors
                except Exception as e:
                    st.error(f"Connection Error: {e}")
        
        st.divider()
        st.write("New here?")
        # Toggle to registration mode
        if st.button("Register New User", use_container_width=True):
            st.session_state['reg_mode'] = True
            st.rerun()