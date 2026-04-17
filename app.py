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
        st.title("Workout and Exercise Login")
        email = st.text_input("Email")
        pw = st.text_input("Password", type="password")
        if st.button("Access Dashboard", use_container_width=True):
            if not email.strip() or not pw.strip():
                st.error("Please enter both email and password.")
            else:
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

# --- 3. TRAINING LOG PAGE ---
def show_training_log():
    st.title("Training Dashboard")
    try:
        conn = get_connection()
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
                        if not final_type or not final_type.strip():
                            st.error("Workout Type is required.")
                        else:
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
                            if not ename or not ename.strip():
                                st.error("Exercise Name is required.")
                            else:
                                cursor = conn.cursor()
                                cursor.execute("INSERT INTO ExerciseEntry (WorkoutID, ExerciseName, Sets, Reps, Weight) VALUES (%s, %s, %s, %s, %s)",
                                               (w_opts[target], ename.strip(), sets, reps, weight))
                                conn.commit()
                                st.rerun()

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
                                if not en or not en.strip():
                                    st.error("Name cannot be empty.")
                                else:
                                    cursor = conn.cursor()
                                    cursor.execute("UPDATE ExerciseEntry SET ExerciseName=%s, Sets=%s, Reps=%s, Weight=%s WHERE EntryID=%s", 
                                                   (en.strip(), es, er, ew, e_opts[e_target_id]))
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

# --- 4. GOALS AND PROGRESS PAGE ---
def show_goals_page():
    st.title("Goals and Progress Tracking")
    try:
        conn = get_connection()
        goals_df = pd.read_sql("SELECT * FROM Goal WHERE UserID = %s", conn, params=(st.session_state['user_id'],))
        
        st.subheader("Management Hub")
        t1, t2, t3, t4 = st.tabs(["New Goal", "Edit Goal", "Log Progress", "Edit Progress"])

        with t1:
            with st.form("new_goal_form", border=False):
                gt = st.text_input("Goal Type")
                tv = st.number_input("Target Value", 1)
                sd = st.date_input("Start Date")
                ed = st.date_input("End Date")
                stat = st.text_input("Status", value="Active")
                if st.form_submit_button("Save Goal", use_container_width=True):
                    if not gt.strip():
                        st.error("Goal Type is required.")
                    elif not stat.strip():
                        st.error("Status is required.")
                    elif sd > ed:
                        st.error("Start Date cannot be after End Date.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO Goal (UserID, GoalType, TargetValue, StartDate, EndDate, Status) VALUES (%s, %s, %s, %s, %s, %s)", 
                                       (st.session_state['user_id'], gt.strip(), tv, sd, ed, stat.strip()))
                        conn.commit()
                        st.rerun()

        with t2:
            if not goals_df.empty:
                g_id = st.selectbox("Select Goal to Edit", goals_df['GoalID'], format_func=lambda x: f"{x} - {goals_df[goals_df['GoalID']==x]['GoalType'].values[0]}")
                curr_g = goals_df[goals_df['GoalID'] == g_id].iloc[0]
                with st.form("edit_goal_form", border=False):
                    up_gt = st.text_input("Type", value=curr_g['GoalType'])
                    up_tv = st.number_input("Target", 1, value=int(curr_g['TargetValue']))
                    up_st = st.text_input("Status", value=curr_g['Status'])
                    if st.form_submit_button("Update Goal", use_container_width=True):
                        if not up_gt.strip() or not up_st.strip():
                            st.error("All text fields must be filled.")
                        else:
                            cursor = conn.cursor()
                            cursor.execute("UPDATE Goal SET GoalType=%s, TargetValue=%s, Status=%s WHERE GoalID=%s", 
                                           (up_gt.strip(), up_tv, up_st.strip(), g_id))
                            conn.commit()
                            st.rerun()

        with t3:
            if not goals_df.empty:
                with st.form("log_progress_form", border=False):
                    g_target = st.selectbox("For Goal", goals_df['GoalID'], format_func=lambda x: goals_df[goals_df['GoalID']==x]['GoalType'].values[0])
                    p_val = st.number_input("Progress Value", 1)
                    p_date = st.date_input("Date Recorded")
                    if st.form_submit_button("Add Progress", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO Progress (UserID, GoalID, ProgressValue, RecordedDate) VALUES (%s, %s, %s, %s)", 
                                       (st.session_state['user_id'], g_target, p_val, p_date))
                        conn.commit()
                        st.rerun()

        with t4:
            progress_df = pd.read_sql("SELECT * FROM Progress WHERE UserID = %s", conn, params=(st.session_state['user_id'],))
            if not progress_df.empty:
                p_to_edit = st.selectbox("Entry ID to Edit", progress_df['ProgressID'])
                curr_p = progress_df[progress_df['ProgressID'] == p_to_edit].iloc[0]
                with st.form("edit_progress_form", border=False):
                    up_pval = st.number_input("Value", 1, value=int(curr_p['ProgressValue']))
                    up_pdate = st.date_input("Date", value=curr_p['RecordedDate'])
                    if st.form_submit_button("Update Progress Entry", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Progress SET ProgressValue=%s, RecordedDate=%s WHERE ProgressID=%s", 
                                       (up_pval, up_pdate, p_to_edit))
                        conn.commit()
                        st.rerun()

        st.divider()
        st.subheader("Your Goals and Detailed Progress")
        all_progress = pd.read_sql("SELECT * FROM Progress WHERE UserID = %s ORDER BY RecordedDate DESC, ProgressID DESC", conn, params=(st.session_state['user_id'],))

        if not goals_df.empty:
            for _, goal in goals_df.iterrows():
                goal_id = goal['GoalID']
                goal_progress = all_progress[all_progress['GoalID'] == goal_id]
                
                # --- CHANGE: Fetch most recent instead of SUM ---
                if not goal_progress.empty:
                    current_val = goal_progress.iloc[0]['ProgressValue']
                else:
                    current_val = 0
                
                target = goal['TargetValue']
                percent = min(1.0, current_val / target) if target > 0 else 0.0
                
                with st.container():
                    col_info, col_bar = st.columns([1, 2])
                    with col_info:
                        st.markdown(f"#### {goal['GoalType']}")
                        st.write(f"Status: **{goal['Status']}**")
                        st.write(f"Period: {goal['StartDate']} to {goal['EndDate']}")
                        st.write(f"Current: **{current_val}** / **{target}**")
                    with col_bar:
                        st.write("") 
                        st.progress(percent)
                    
                    if not goal_progress.empty:
                        with st.expander(f"View Update History for {goal['GoalType']}"):
                            st.table(goal_progress[['ProgressID', 'ProgressValue', 'RecordedDate']])
                    else:
                        st.caption("No progress updates yet.")
                    st.divider()
        
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 5. MAIN APP ---
def main():
    st.set_page_config(page_title="Workout and Exercise", layout="wide")
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False

    if not st.session_state['logged_in']:
        show_login_page()
    else:
        with st.sidebar:
            st.title("Workout and Exercise")
            st.write(f"Logged in: **{st.session_state.get('user_name')}**")
            st.divider()
            choice = st.radio("Navigation", ["Training Log", "Goals and Progress"])
            st.divider()
            if st.button("Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        if choice == "Training Log":
            show_training_log()
        elif choice == "Goals and Progress":
            show_goals_page()

if __name__ == "__main__":
    main()