import streamlit as st
import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. DATABASE CONNECTION ---
def get_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="Oblig4",
        unix_socket="/opt/lampp/var/mysql/mysql.sock"
    )

# --- 2. LOGIN PAGE ---
def show_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Training App Login")
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if st.button("Access Dashboard", use_container_width=True):
            try:
                conn = get_connection()
                cursor = conn.cursor(dictionary=True)
                cursor.execute("SELECT * FROM User WHERE Email=%s AND Password=%s", (email, pw))
                user = cursor.fetchone()
                conn.close()
                if user:
                    st.session_state['logged_in'] = True
                    st.session_state['user_id'] = user['UserID']
                    st.session_state['user_name'] = user['Name']
                    st.rerun()
                else:
                    st.error("Invalid credentials.")
            except Exception as e:
                st.error(f"Connection Error: {e}")

# --- 3. TRAINING LOG PAGE (CRUD) ---
def show_training_log():
    st.title("Training Dashboard")
    
    try:
        conn = get_connection()
        
        # 3.1 Fetch Data
        types_df = pd.read_sql("SELECT DISTINCT WorkoutType FROM Workout", conn)
        existing_types = sorted(types_df['WorkoutType'].tolist())
        create_new_label = "Create New Type..."
        if create_new_label not in existing_types:
            existing_types.append(create_new_label)

        workouts_df = pd.read_sql(
            "SELECT * FROM Workout WHERE UserID = %s ORDER BY WorkoutID DESC", 
            conn, params=(st.session_state['user_id'],)
        )
        
        exercises_df = pd.read_sql(
            """SELECT ee.*, w.Date FROM ExerciseEntry ee 
               JOIN Workout w ON ee.WorkoutID = w.WorkoutID 
               WHERE w.UserID = %s""", 
            conn, params=(st.session_state['user_id'],)
        )

        # 3.2 Management Hub
        st.subheader("Management")
        c1, c2, c3 = st.columns(3)

        with c1:
            with st.expander("New Workout"):
                selected_type = st.selectbox("Type", existing_types)
                new_type_name = ""
                if selected_type == create_new_label:
                    new_type_name = st.text_input("New Type Name")

                with st.form("new_w_form", border=False):
                    wd = st.date_input("Date")
                    dur = st.number_input("Duration (min)", 1, 300, 45)
                    if st.form_submit_button("Create Workout", use_container_width=True):
                        final_type = new_type_name if selected_type == create_new_label else selected_type
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO Workout (UserID, WorkoutType, Date, Duration) VALUES (%s, %s, %s, %s)",
                                       (st.session_state['user_id'], final_type.strip(), wd, dur))
                        conn.commit()
                        st.rerun()

        with c2:
            with st.expander("Add Exercise"):
                if not workouts_df.empty:
                    with st.form("new_e_form", border=False):
                        w_opts = {f"ID {r['WorkoutID']} | {r['Date']}": r['WorkoutID'] for _, r in workouts_df.iterrows()}
                        target = st.selectbox("To Workout", list(w_opts.keys()))
                        ename = st.text_input("Exercise Name")
                        sets = st.number_input("Sets", 1, 20, 3)
                        reps = st.number_input("Reps", 1, 100, 10)
                        weight = st.number_input("Kg", 0, 500, 0)
                        if st.form_submit_button("Log Exercise", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("INSERT INTO ExerciseEntry (WorkoutID, ExerciseName, Sets, Reps, Weight) VALUES (%s, %s, %s, %s, %s)",
                                           (w_opts[target], ename, sets, reps, weight))
                            conn.commit()
                            st.rerun()
                else:
                    st.info("Log a workout first.")

        with c3:
            with st.expander("Edit / Delete"):
                tab_edit, tab_del_ex, tab_del_w = st.tabs(["Edit", "Del Exercise", "Del Workout"])
                
                with tab_edit:
                    if not exercises_df.empty:
                        e_opts = {f"{r['ExerciseName']} ({r['Date']})": r['EntryID'] for _, r in exercises_df.iterrows()}
                        e_target_id = st.selectbox("Select", list(e_opts.keys()))
                        curr = exercises_df[exercises_df['EntryID'] == e_opts[e_target_id]].iloc[0]
                        with st.form("edit_form", border=False):
                            en = st.text_input("Name", value=curr['ExerciseName'])
                            es = st.number_input("Sets", 1, 20, value=int(curr['Sets']))
                            er = st.number_input("Reps", 1, 100, value=int(curr['Reps']))
                            ew = st.number_input("Kg", 0, 500, value=int(curr['Weight']))
                            if st.form_submit_button("Save", use_container_width=True):
                                cursor = conn.cursor()
                                cursor.execute("UPDATE ExerciseEntry SET ExerciseName=%s, Sets=%s, Reps=%s, Weight=%s WHERE EntryID=%s", 
                                               (en, es, er, ew, e_opts[e_target_id]))
                                conn.commit()
                                st.rerun()

                with tab_del_ex:
                    if not exercises_df.empty:
                        ex_del_opts = {f"{r['ExerciseName']} ({r['Date']})": r['EntryID'] for _, r in exercises_df.iterrows()}
                        target_del = st.selectbox("Remove Exercise", list(ex_del_opts.keys()))
                        if st.button("Delete Exercise", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ExerciseEntry WHERE EntryID = %s", (ex_del_opts[target_del],))
                            conn.commit()
                            st.rerun()

                with tab_del_w:
                    if not workouts_df.empty:
                        del_id = st.selectbox("Remove Workout ID", workouts_df['WorkoutID'])
                        if st.button("Delete Workout", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ExerciseEntry WHERE WorkoutID = %s", (del_id,))
                            cursor.execute("DELETE FROM Workout WHERE WorkoutID = %s", (del_id,))
                            conn.commit()
                            st.rerun()

        st.divider()

        # 3.3 Training Diary Display
        st.subheader("Training History")
        for _, workout in workouts_df.iterrows():
            st.markdown(f"### [#{workout['WorkoutID']}] {workout['Date']} - {workout['WorkoutType']}")
            spec_ex = exercises_df[exercises_df['WorkoutID'] == workout['WorkoutID']]
            if not spec_ex.empty:
                st.table(spec_ex[['ExerciseName', 'Sets', 'Reps', 'Weight']])
            else:
                st.caption("No exercises recorded.")
            st.divider()

        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 4. DATA INSIGHTS PAGE ---
def show_insights_page():
    st.title("Performance Analytics")
    query = """
    SELECT u.Name, SUM(ee.Weight * ee.Sets * ee.Reps) as Volume 
    FROM User u 
    JOIN Workout w ON u.UserID = w.UserID 
    JOIN ExerciseEntry ee ON w.WorkoutID = ee.WorkoutID 
    GROUP BY u.Name
    """
    try:
        conn = get_connection()
        df = pd.read_sql(query, conn)
        conn.close()
        if not df.empty:
            fig, ax = plt.subplots(figsize=(10, 5))
            sns.barplot(data=df, x='Name', y='Volume', ax=ax, palette='muted')
            st.pyplot(fig)
            st.table(df)
        else:
            st.info("Insufficient data for charts.")
    except Exception as e:
        st.error(f"Error: {e}")

# --- 5. MAIN ORCHESTRATOR ---
def main():
    st.set_page_config(page_title="Training App", layout="wide")

    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        show_login_page()
    else:
        with st.sidebar:
            st.title("Workout and Exercise")
            st.write(f"Logged in as: **{st.session_state.get('user_name')}**")
            st.divider()
            choice = st.radio("Go to:", ["Training Log", "Insights"])
            st.divider()
            if st.button("Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        if choice == "Training Log":
            show_training_log()
        elif choice == "Insights":
            show_insights_page()

if __name__ == "__main__":
    main()