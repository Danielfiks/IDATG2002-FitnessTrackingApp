import streamlit as st
import pandas as pd

# --- TRAINING LOG PAGE ---
def show_training_log(conn):
    st.title("Training Dashboard")
    try:
        # Fetch unique workout categories for selection lists
        types_df = pd.read_sql("SELECT DISTINCT WorkoutType FROM Workout", conn)
        existing_types = sorted(types_df['WorkoutType'].tolist())
        create_new_label = "Create New Type..."
        
        # Fetch all workouts belonging to the logged-in user
        workouts_df = pd.read_sql(
            "SELECT * FROM Workout WHERE UserID = %s", 
            conn, params=(st.session_state['user_id'],)
        )

        # Convert Date column to standard Python date objects for UI consistency
        workouts_df['Date'] = pd.to_datetime(workouts_df['Date']).dt.date

        # Fetch individual exercise entries linked to the user's workouts
        exercises_df = pd.read_sql(
            """SELECT ee.*, w.Date FROM ExerciseEntry ee 
               JOIN Workout w ON ee.WorkoutID = w.WorkoutID 
               WHERE w.UserID = %s""", 
            conn, params=(st.session_state['user_id'],)
        )

        st.subheader("Management")
        c1, c2, c3 = st.columns(3)

        with c1:
            # Section for logging a brand new workout session
            with st.expander("New Workout"):
                # Prepare list including existing types and option to add new one
                types_for_select = existing_types.copy()
                if create_new_label not in types_for_select:
                    types_for_select.append(create_new_label)
                
                # Dropdown for selecting the workout category
                selected_type = st.selectbox("Type", types_for_select)

                new_type_name = ""

                # Show text input if "Create New Type..." is selected
                if selected_type == create_new_label:
                    new_type_name = st.text_input("New Type Name")

                # Form for inputting session details
                with st.form("new_w_form", border=False):
                    wd = st.date_input("Date")
                    dur = st.number_input("Duration (min)", 1, 300, 45)

                    # Submission logic for the new workout
                    if st.form_submit_button("Create Workout", use_container_width=True):
                        # Determine if we use an existing type or a custom text input
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
            # Section for adding specific exercises to an existing workout session
            with st.expander("Add Exercise"):
                if not workouts_df.empty:
                    with st.form("new_e_form", border=False):
                        # Create a map for the selectbox display vs the underlying WorkoutID
                        w_opts = {f"ID {r['WorkoutID']} | {r['Date']}": int(r['WorkoutID']) for _, r in workouts_df.sort_values('WorkoutID', ascending=False).iterrows()}
                        target = st.selectbox("To Workout", list(w_opts.keys()))
                        ename = st.text_input("Exercise Name")
                        sets = st.number_input("Sets", 1, 20, 3)
                        reps = st.number_input("Reps", 1, 100, 10)
                        weight = st.number_input("Kg", 0, 500, 0)
                        
                        # Commit the specific exercise data to the database
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
            # Section for administrative changes: Editing or Deleting records
            with st.expander("Edit / Delete"):
                tab_edit, tab_del_ex, tab_del_w = st.tabs(["Edit", "Del Exercise", "Del Workout"])
                
                # Logic for updating an existing exercise entry
                with tab_edit:
                    if not exercises_df.empty:
                        e_opts = {f"{r['ExerciseName']} ({r['Date']})": int(r['EntryID']) for _, r in exercises_df.iterrows()}
                        e_target_id = st.selectbox("Select", list(e_opts.keys()))
                        # Populate form with current values
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
                
                # Logic for removing a single exercise entry
                with tab_del_ex:
                    if not exercises_df.empty:
                        ex_del_opts = {f"{r['ExerciseName']} ({r['Date']})": int(r['EntryID']) for _, r in exercises_df.iterrows()}
                        target_del = st.selectbox("Remove Exercise", list(ex_del_opts.keys()))
                        if st.button("Delete Exercise", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            cursor.execute("DELETE FROM ExerciseEntry WHERE EntryID = %s", (ex_del_opts[target_del],))
                            conn.commit()
                            st.rerun()
                
                # Logic for removing an entire workout session (cascades manually to exercises)
                with tab_del_w:
                    if not workouts_df.empty:
                        del_id = int(st.selectbox("Remove Workout ID", workouts_df['WorkoutID']))
                        if st.button("Delete Workout", type="primary", use_container_width=True):
                            cursor = conn.cursor()
                            # Delete children first (ExerciseEntries) to maintain integrity
                            cursor.execute("DELETE FROM ExerciseEntry WHERE WorkoutID = %s", (del_id,))
                            # Delete parent session
                            cursor.execute("DELETE FROM Workout WHERE WorkoutID = %s", (del_id,))
                            conn.commit()
                            st.rerun()

        st.divider()
        st.subheader("Training History")
        
        # Filtering and Sorting UI for history browsing
        with st.expander("Filters and Sorting"):
            col_f1, col_s1 = st.columns(2)
            with col_f1:
                filter_type = st.multiselect("Filter by Type", existing_types)
            with col_s1:
                sort_by = st.selectbox("Sort By", ["Date (Newest)", "Date (Oldest)", "Workout ID (desc)", "Workout ID (asc)"])

        # Create a copy for processing
        filtered_df = workouts_df.copy()
        
        # Apply category filter if user selected any
        if filter_type:
            filtered_df = filtered_df[filtered_df['WorkoutType'].isin(filter_type)]

        # Apply sorting logic based on dropdown selection
        if sort_by == "Date (Newest)":
            filtered_df = filtered_df.sort_values('Date', ascending=False)
        elif sort_by == "Date (Oldest)":
            filtered_df = filtered_df.sort_values('Date', ascending=True)
        elif sort_by == "Workout ID (desc)":
            filtered_df = filtered_df.sort_values('WorkoutID', ascending=False)
        else:
            filtered_df = filtered_df.sort_values('WorkoutID', ascending=True)

        # Loop through data and display each workout session with its sub-table
        if filtered_df.empty:
            st.info("No workouts found matching the current filters.")
        else:
            for _, workout in filtered_df.iterrows():
                st.markdown(f"### [#{workout['WorkoutID']}] {workout['Date']} - {workout['WorkoutType']}")
                # Get exercises belonging to this specific workout loop
                spec_ex = exercises_df[exercises_df['WorkoutID'] == workout['WorkoutID']]
                if not spec_ex.empty:
                    st.table(spec_ex[['ExerciseName', 'Sets', 'Reps', 'Weight']])
                else:
                    st.caption("No exercises recorded.")
                st.divider()
        
        conn.close()
    except Exception as e:
        st.error(f"Error: {e}")