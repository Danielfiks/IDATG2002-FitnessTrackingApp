import streamlit as st
import pandas as pd

# --- HEALTH METRICS PAGE ---
def show_health_metrics_page(conn):
    st.title("Health Metrics Tracking")
    try:
        # Load user's health data (weight, body fat, heart rate, etc.)
        metrics_df = pd.read_sql(
            "SELECT * FROM HealthMetric WHERE UserID = %s ORDER BY RecordedDate DESC", 
            conn, params=(st.session_state['user_id'],)
        )

        tab_new, tab_edit, tab_delete = st.tabs(["Log Metric", "Edit Entry", "Remove Entry"])

        # Form for logging new health data
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

        # Update specific health entries
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

        # Logic for deleting incorrect health records
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
        # Visual trend analysis: only graph metrics with at least two data points
        if not metrics_df.empty:
            counts = metrics_df['MetricType'].value_counts()
            graphable_types = counts[counts > 1].index.tolist()
            if graphable_types:
                selected_chart = st.selectbox("View Trend For:", graphable_types)
                chart_data = metrics_df[metrics_df['MetricType'] == selected_chart].sort_values('RecordedDate')
                # Generate a line chart for the selected metric
                st.line_chart(chart_data.set_index('RecordedDate')['MetricValue'])
            # Display full data table below chart
            st.table(metrics_df[['MetricType', 'MetricValue', 'RecordedDate']])
        else:
            st.caption("No metrics found.")
        conn.close()
    except Exception as e:
        st.error(f"Database Error: {e}")