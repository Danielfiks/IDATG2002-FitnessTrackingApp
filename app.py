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

# --- 2. REGISTRATION PAGE ---
def show_registration_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.title("Register for Workout and Exercise")
        new_name = st.text_input("Full Name")
        new_email = st.text_input("Email")
        new_pw = st.text_input("Password", type="password")
        confirm_pw = st.text_input("Confirm Password", type="password")
        
        if st.button("Create Account", use_container_width=True):
            if not new_name.strip() or not new_email.strip() or not new_pw.strip():
                st.error("All fields are required.")
            elif new_pw != confirm_pw:
                st.error("Passwords do not match.")
            else:
                try:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("SELECT * FROM User WHERE Email=%s", (new_email,))
                    if cursor.fetchone():
                        st.error("An account with this email already exists.")
                    else:
                        cursor.execute("INSERT INTO User (Name, Email, Password) VALUES (%s, %s, %s)", 
                                       (new_name.strip(), new_email.strip(), new_pw))
                        conn.commit()
                        st.success("Registration successful! Please log in.")
                        st.session_state['reg_mode'] = False
                        st.rerun()
                    conn.close()
                except Exception as e:
                    st.error(f"Error during registration: {e}")
        
        if st.button("Back to Login", use_container_width=True):
            st.session_state['reg_mode'] = False
            st.rerun()

# --- 3. LOGIN PAGE ---
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
        
        st.divider()
        st.write("New here?")
        if st.button("Register New User", use_container_width=True):
            st.session_state['reg_mode'] = True
            st.rerun()

# --- 4. TRAINING LOG PAGE ---
def show_training_log():
    st.title("Training Dashboard")
    try:
        conn = get_connection()
        types_df = pd.read_sql("SELECT DISTINCT WorkoutType FROM Workout", conn)
        existing_types = sorted(types_df['WorkoutType'].tolist())
        create_new_label = "Create New Type..."
        
        workouts_df = pd.read_sql(
            "SELECT * FROM Workout WHERE UserID = %s", 
            conn, params=(st.session_state['user_id'],)
        )
        # Ensure Date column is datetime objects for comparison
        workouts_df['Date'] = pd.to_datetime(workouts_df['Date']).dt.date

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
                types_for_select = existing_types.copy()
                if create_new_label not in types_for_select:
                    types_for_select.append(create_new_label)
                selected_type = st.selectbox("Type", types_for_select)
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
                        w_opts = {f"ID {r['WorkoutID']} | {r['Date']}": int(r['WorkoutID']) for _, r in workouts_df.sort_values('WorkoutID', ascending=False).iterrows()}
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
                        e_opts = {f"{r['ExerciseName']} ({r['Date']})": int(r['EntryID']) for _, r in exercises_df.iterrows()}
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
                                               (en.strip(), es, er, ew, e_opts[e_target_id]))
                                conn.commit()
                                st.rerun()
                
                with tab_del_ex:
                    if not exercises_df.empty:
                        ex_del_opts = {f"{r['ExerciseName']} ({r['Date']})": int(r['EntryID']) for _, r in exercises_df.iterrows()}
                        target_del = st.selectbox("Remove Exercise", list(ex_del_opts.keys()))
                        if st.button("Delete Exercise", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ExerciseEntry WHERE EntryID = %s", (ex_del_opts[target_del],))
                            conn.commit()
                            st.rerun()
                with tab_del_w:
                    if not workouts_df.empty:
                        del_id = int(st.selectbox("Remove Workout ID", workouts_df['WorkoutID']))
                        if st.button("Delete Workout", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ExerciseEntry WHERE WorkoutID = %s", (del_id,))
                            cursor.execute("DELETE FROM Workout WHERE WorkoutID = %s", (del_id,))
                            conn.commit()
                            st.rerun()

        st.divider()
        st.subheader("Training History")
        
        # Filtering and Sorting Logic
        with st.expander("Filters and Sorting"):
            col_f1, col_s1 = st.columns(2)
            with col_f1:
                filter_type = st.multiselect("Filter by Type", existing_types)
            with col_s1:
                sort_by = st.selectbox("Sort By", ["Date (Newest)", "Date (Oldest)", "Workout ID (desc)", "Workout ID (asc)"])

        # Apply Filters
        filtered_df = workouts_df.copy()
        
        if filter_type:
            filtered_df = filtered_df[filtered_df['WorkoutType'].isin(filter_type)]

        # Apply Sorting
        if sort_by == "Date (Newest)":
            filtered_df = filtered_df.sort_values('Date', ascending=False)
        elif sort_by == "Date (Oldest)":
            filtered_df = filtered_df.sort_values('Date', ascending=True)
        elif sort_by == "Workout ID (desc)":
            filtered_df = filtered_df.sort_values('WorkoutID', ascending=False)
        else:
            filtered_df = filtered_df.sort_values('WorkoutID', ascending=True)

        # Display Loop
        if filtered_df.empty:
            st.info("No workouts found matching the current filters.")
        else:
            for _, workout in filtered_df.iterrows():
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

# --- 5. GOALS AND PROGRESS PAGE ---
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
                g_id = int(st.selectbox("Select Goal to Edit", goals_df['GoalID'], format_func=lambda x: f"{x} - {goals_df[goals_df['GoalID']==x]['GoalType'].values[0]}"))
                curr_g = goals_df[goals_df['GoalID'] == g_id].iloc[0]
                with st.form("edit_goal_form", border=False):
                    up_gt = st.text_input("Type", value=curr_g['GoalType'])
                    up_tv = st.number_input("Target", 1, value=int(curr_g['TargetValue']))
                    up_st = st.text_input("Status", value=curr_g['Status'])
                    if st.form_submit_button("Update Goal", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE Goal SET GoalType=%s, TargetValue=%s, Status=%s WHERE GoalID=%s", 
                                       (up_gt.strip(), up_tv, up_st.strip(), g_id))
                        conn.commit()
                        st.rerun()

        with t3:
            if not goals_df.empty:
                with st.form("log_progress_form", border=False):
                    g_target = int(st.selectbox("For Goal", goals_df['GoalID'], format_func=lambda x: goals_df[goals_df['GoalID']==x]['GoalType'].values[0]))
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
                p_to_edit = int(st.selectbox("Entry ID to Edit", progress_df['ProgressID']))
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
                current_val = goal_progress.iloc[0]['ProgressValue'] if not goal_progress.empty else 0
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
                    st.divider()
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")

# --- 6. HEALTH METRICS PAGE ---
def show_health_metrics_page():
    st.title("Health Metrics Tracking")
    try:
        conn = get_connection()
        metrics_df = pd.read_sql(
            "SELECT * FROM HealthMetric WHERE UserID = %s ORDER BY RecordedDate DESC", 
            conn, params=(st.session_state['user_id'],)
        )

        tab_new, tab_edit, tab_delete = st.tabs(["Log Metric", "Edit Entry", "Remove Entry"])

        with tab_new:
            with st.form("new_metric_form", border=False):
                m_type = st.text_input("Metric Type")
                m_val = st.number_input("Value", value=0)
                m_date = st.date_input("Date Recorded")
                if st.form_submit_button("Add Metric", use_container_width=True):
                    if not m_type.strip():
                        st.error("Metric Type is required.")
                    else:
                        cursor = conn.cursor()
                        cursor.execute("INSERT INTO HealthMetric (UserID, MetricType, MetricValue, RecordedDate) VALUES (%s, %s, %s, %s)",
                                       (st.session_state['user_id'], m_type.strip(), m_val, m_date))
                        conn.commit()
                        st.rerun()

        with tab_edit:
            if not metrics_df.empty:
                m_options = {f"{r['MetricType']} - {r['RecordedDate']} (ID: {r['MetricID']})": int(r['MetricID']) for _, r in metrics_df.iterrows()}
                selected_m_id = st.selectbox("Select Entry to Update", list(m_options.keys()))
                curr_m = metrics_df[metrics_df['MetricID'] == m_options[selected_m_id]].iloc[0]
                with st.form("edit_metric_form", border=False):
                    up_type = st.text_input("Type", value=curr_m['MetricType'])
                    up_val = st.number_input("Value", value=int(curr_m['MetricValue']))
                    up_date = st.date_input("Date", value=curr_m['RecordedDate'])
                    if st.form_submit_button("Save Changes", use_container_width=True):
                        cursor = conn.cursor()
                        cursor.execute("UPDATE HealthMetric SET MetricType=%s, MetricValue=%s, RecordedDate=%s WHERE MetricID=%s",
                                       (up_type.strip(), up_val, up_date, int(curr_m['MetricID'])))
                        conn.commit()
                        st.rerun()

        with tab_delete:
            if not metrics_df.empty:
                del_options = {f"{r['MetricType']} - {r['RecordedDate']} (ID: {r['MetricID']})": int(r['MetricID']) for _, r in metrics_df.iterrows()}
                target_del = st.selectbox("Select Entry to Remove", list(del_options.keys()))
                if st.button("Delete Entry", type="primary", use_container_width=True):
                    cursor = conn.cursor()
                    cursor.execute("DELETE FROM HealthMetric WHERE MetricID = %s", (del_options[target_del],))
                    conn.commit()
                    st.rerun()

        st.divider()
        st.subheader("Metric History")
        if not metrics_df.empty:
            counts = metrics_df['MetricType'].value_counts()
            graphable_types = counts[counts > 1].index.tolist()
            if graphable_types:
                selected_chart = st.selectbox("View Trend For:", graphable_types)
                chart_data = metrics_df[metrics_df['MetricType'] == selected_chart].sort_values('RecordedDate')
                st.line_chart(chart_data.set_index('RecordedDate')['MetricValue'])
            st.table(metrics_df[['MetricType', 'MetricValue', 'RecordedDate']])
        else:
            st.caption("No metrics found.")
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")

# --- 7. MAIN APP ---
def main():
    st.set_page_config(page_title="Workout and Exercise", layout="wide")
    if 'logged_in' not in st.session_state:
        st.session_state['logged_in'] = False
    if 'reg_mode' not in st.session_state:
        st.session_state['reg_mode'] = False

    if not st.session_state['logged_in']:
        if st.session_state['reg_mode']:
            show_registration_page()
        else:
            show_login_page()
    else:
        with st.sidebar:
            st.title("Workout and Exercise")
            st.write(f"Logged in: **{st.session_state.get('user_name')}**")
            st.divider()
            choice = st.radio("Navigation", ["Training Log", "Goals and Progress", "Health Metrics"])
            st.divider()
            if st.button("Logout", use_container_width=True):
                st.session_state.clear()
                st.rerun()

        if choice == "Training Log":
            show_training_log()
        elif choice == "Goals and Progress":
            show_goals_page()
        elif choice == "Health Metrics":
            show_health_metrics_page()

if __name__ == "__main__":
    main()