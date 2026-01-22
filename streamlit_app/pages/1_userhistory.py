import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import os
from datetime import datetime, timedelta, date
from dotenv import load_dotenv

load_dotenv()

# --- CONFIGURATION ---
st.set_page_config(page_title="User History", layout="wide")
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# --- AUTH CHECK ---
if "token" not in st.session_state:
    st.warning("🔒 Please login first from the main page.")
    st.stop()

# --- HELPER ---
def authenticated_request(method, endpoint, params=None):
    token = st.session_state.get("token")
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.request(method, f"{API_BASE_URL}{endpoint}", headers=headers, params=params)
        if response.status_code >= 400:
            return None
        return response.json()
    except:
        return None

# --- PAGE HEADER ---
st.title("📋 User History")

# --- FILTERS ROW ---
st.markdown("### 🔍 Filters")
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.5])

with col1:
    date_from = st.date_input("📅 Date From", value=date.today() - timedelta(days=30))

with col2:
    date_to = st.date_input("📅 Date To", value=date.today())

# Fetch data first to populate project/role dropdowns
all_history = authenticated_request("GET", "/time/history")

# Get unique projects and roles for dropdown
projects_list = ["All Projects"]
roles_list = ["All Roles"]

if all_history:
    df_all = pd.DataFrame(all_history)
    if 'project_name' in df_all.columns:
        projects_list += list(df_all['project_name'].dropna().unique())
    if 'work_role' in df_all.columns:
        roles_list += list(df_all['work_role'].dropna().unique())

with col3:
    project_filter = st.selectbox("🏢 Project (Optional)", projects_list)

with col4:
    role_filter = st.selectbox("👤 Role (Optional)", roles_list)

with col5:
    st.markdown("<br>", unsafe_allow_html=True)
    apply_btn = st.button("🔍 Apply", type="primary", use_container_width=True)

st.markdown("---")

# --- FETCH & FILTER DATA ---
params = {}
if date_from:
    params["start_date"] = str(date_from)
if date_to:
    params["end_date"] = str(date_to)

time_history = authenticated_request("GET", "/time/history", params=params)

if time_history:
    df = pd.DataFrame(time_history)
    
    # Apply project filter
    if project_filter != "All Projects" and 'project_name' in df.columns:
        df = df[df['project_name'] == project_filter]
    
    # Apply role filter
    if role_filter != "All Roles" and 'work_role' in df.columns:
        df = df[df['work_role'] == role_filter]
    
    if df.empty:
        st.info("📭 No records found for the selected filters.")
    else:
        # --- SUMMARY STATS ---
        total_minutes = df['minutes_worked'].sum() if 'minutes_worked' in df.columns else 0
        total_hours = total_minutes / 60
        total_tasks = int(df['tasks_completed'].sum()) if 'tasks_completed' in df.columns else 0
        unique_projects = df['project_name'].dropna().nunique() if 'project_name' in df.columns else 0
        
        col_s1, col_s2, col_s3 = st.columns(3)
        col_s1.metric("⏱️ Total Hours", f"{total_hours:.1f}h")
        col_s2.metric("✅ Tasks Completed", total_tasks)
        col_s3.metric("🏢 Projects", unique_projects)
        
        st.markdown("---")
        
        # --- TIMESHEET TABLE WITH PRODUCTIVITY ---
        st.subheader("📋 Timesheet History")
        
        # Prepare display dataframe
        display_cols = ['sheet_date', 'project_name', 'work_role', 'clock_in_at', 'clock_out_at', 
                       'minutes_worked', 'tasks_completed', 'status']
        available = [c for c in display_cols if c in df.columns]
        
        df_display = df[available].copy()
        
        # Calculate hours from minutes
        if 'minutes_worked' in df_display.columns:
            df_display['hours'] = (df_display['minutes_worked'] / 60).round(1)
        
        # Add productivity rating based on tasks
        if 'tasks_completed' in df_display.columns:
            def get_productivity(tasks):
                if pd.isna(tasks):
                    return "⚪ N/A"
                if tasks >= 7:
                    return "🟢 Good"
                elif tasks >= 4:
                    return "🟡 Average"
                else:
                    return "🔴 Bad"
            df_display['Productivity'] = df_display['tasks_completed'].apply(get_productivity)
        
        # Rename columns
        rename_map = {
            'sheet_date': 'Date',
            'project_name': 'Project',
            'work_role': 'Role',
            'clock_in_at': 'Clock In',
            'clock_out_at': 'Clock Out',
            'hours': 'Hours',
            'tasks_completed': 'Tasks',
            'status': 'Status'
        }
        df_display.rename(columns={k: v for k, v in rename_map.items() if k in df_display.columns}, inplace=True)
        
        # Format time columns
        for col in ['Clock In', 'Clock Out']:
            if col in df_display.columns:
                try:
                    df_display[col] = pd.to_datetime(df_display[col], format='ISO8601').dt.strftime('%H:%M')
                except:
                    pass
        
        # Remove minutes_worked (we show hours instead)
        if 'minutes_worked' in df_display.columns:
            df_display.drop('minutes_worked', axis=1, inplace=True)
        
        # Reorder columns
        preferred_order = ['Date', 'Project', 'Role', 'Clock In', 'Clock Out', 'Hours', 'Tasks', 'Productivity', 'Status']
        final_cols = [c for c in preferred_order if c in df_display.columns]
        df_display = df_display[final_cols]
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        # --- PROJECT BREAKDOWN ---
        st.subheader("🏢 Time by Project")
        
        if 'project_name' in df.columns:
            project_stats = df.groupby('project_name').agg({
                'minutes_worked': 'sum',
                'tasks_completed': 'sum'
            }).reset_index()
            project_stats['Hours'] = (project_stats['minutes_worked'] / 60).round(1)
            project_stats = project_stats.rename(columns={'project_name': 'Project', 'tasks_completed': 'Tasks'})
            project_stats = project_stats[['Project', 'Hours', 'Tasks']].sort_values('Hours', ascending=False)
            
            col_chart, col_table = st.columns([1, 1])
            
            with col_chart:
                if len(project_stats) > 0:
                    fig = px.pie(project_stats, values='Hours', names='Project', hole=0.4,
                                 color_discrete_sequence=px.colors.qualitative.Set2)
                    fig.update_layout(showlegend=True, height=300, margin=dict(t=20, b=20, l=20, r=20))
                    st.plotly_chart(fig, use_container_width=True)
            
            with col_table:
                st.dataframe(project_stats, use_container_width=True, hide_index=True, height=300)
        
        st.markdown("---")
        
        # --- EXPORT ---
        csv = df.to_csv(index=False)
        st.download_button("📥 Download CSV", csv, f"work_history_{date.today()}.csv", "text/csv")

else:
    st.info("📭 No work history found. Start clocking in to track your time!")
    st.caption("Make sure you're logged in and have time entries recorded.")
