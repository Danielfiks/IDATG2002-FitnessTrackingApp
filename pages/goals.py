import streamlit as st
import pandas as pd

# --- GOALS AND PROGRESS PAGE ---
def show_goals_page(conn):
    st.title("Goals and Progress Tracking")
    try:
        # Load all goals for the current user
        goals_df = pd.read_sql("SELECT * FROM Goal WHERE UserID = %s", conn, params=(st.session_state['user_id'],))
        
        st.subheader("Management Hub")
        t1, t2, t3, t4 = st.tabs(["New Goal", "Edit Goal", "Log Progress", "Edit Progress"])

        # Form to create a new fitness goal
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

        # Update existing goal details
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

        # Log an incremental progress entry for a goal
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

        # Correct or update past progress entries
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
        # Fetch all progress notes sorted by date
        all_progress = pd.read_sql("SELECT * FROM Progress WHERE UserID = %s ORDER BY RecordedDate DESC, ProgressID DESC", conn, params=(st.session_state['user_id'],))

        # Iteratively calculate and display progress bars for each goal
        if not goals_df.empty:
            for _, goal in goals_df.iterrows():
                goal_id = goal['GoalID']
                goal_progress = all_progress[all_progress['GoalID'] == goal_id]
                # Get the most recent value to compare against target
                current_val = goal_progress.iloc[0]['ProgressValue'] if not goal_progress.empty else 0
                target = goal['TargetValue']
                # Calculate percentage capped at 100%
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
                    # Allow user to see historical updates for this specific goal
                    if not goal_progress.empty:
                        with st.expander(f"View Update History for {goal['GoalType']}"):
                            st.table(goal_progress[['ProgressID', 'ProgressValue', 'RecordedDate']])
                    st.divider()
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")