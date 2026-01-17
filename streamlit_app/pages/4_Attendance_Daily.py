import streamlit as st
import requests
from datetime import date, datetime

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(page_title="Attendance Daily", layout="wide")

API_BASE_URL = "http://127.0.0.1:8000"

# ---------------------------------------------------------
# HELPER: SPLIT ISO DATETIME INTO DATE + TIME
# ---------------------------------------------------------
def split_datetime(ts):
    if not ts:
        return "-", "-"
    try:
        dt = datetime.fromisoformat(ts.replace("Z", ""))
        return dt.date().isoformat(), dt.strftime("%I:%M %p")
    except Exception:
        return "-", "-"

# ---------------------------------------------------------
# API HELPERS
# ---------------------------------------------------------
def api_request(method, endpoint, token=None, json=None, params=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"

    try:
        response = requests.request(
            method=method,
            url=f"{API_BASE_URL}{endpoint}",
            headers=headers,
            json=json,
            params=params,
        )
        if response.status_code >= 400:
            return None
        return response.json()
    except Exception as e:
        st.error(f"Backend connection error: {e}")
        return None


def authenticated_request(method, endpoint, data=None, params=None):
    token = st.session_state.get("token")

    if not token:
        st.warning("🔒 Please login first from the App page.")
        st.page_link("app.py", label="➡️ Go to App → Login")
        st.stop()

    return api_request(
        method=method,
        endpoint=endpoint,
        token=token,
        json=data,
        params=params,
    )

# ---------------------------------------------------------
# AUTH GUARD (DO NOT REMOVE)
# ---------------------------------------------------------
authenticated_request("GET", "/me/")

# ---------------------------------------------------------
# UI HEADER
# ---------------------------------------------------------
st.title("🗓 Attendance Daily")
st.caption("Your daily attendance across projects")
st.markdown("---")

# ---------------------------------------------------------
# FILTERS
# ---------------------------------------------------------
col1, col2 = st.columns(2)

with col1:
    selected_date = st.date_input("Select Date", date.today())

with col2:
    status_filter = st.selectbox(
        "Attendance Status",
        ["ALL", "PRESENT", "ABSENT", "LEAVE"]
    )

# ---------------------------------------------------------
# FETCH ATTENDANCE DATA
# ---------------------------------------------------------
attendance_records = authenticated_request(
    "GET",
    "/attendance-daily",
    params={"attendance_date": selected_date.isoformat()},
)

if not attendance_records:
    st.info("No attendance records found.")
    st.stop()

# Optional client-side filtering
if status_filter != "ALL":
    attendance_records = [
        a for a in attendance_records
        if a.get("status") == status_filter
    ]

if not attendance_records:
    st.info("No attendance records found for selected status.")
    st.stop()

# ---------------------------------------------------------
# FETCH PROJECTS (ID → NAME MAPPING)
# ---------------------------------------------------------
projects = authenticated_request("GET", "/admin/projects") or []
project_map = {p["id"]: p["name"] for p in projects}

# ---------------------------------------------------------
# RENDER ATTENDANCE RECORDS
# ---------------------------------------------------------
st.subheader("📋 Attendance Records")

for record in attendance_records:
    with st.container(border=True):
        cols = st.columns(7)

        project_id = record.get("project_id")
        project_name = project_map.get(project_id, project_id)

        clock_in_date, clock_in_time = split_datetime(
            record.get("first_clock_in_at")
        )
        clock_out_date, clock_out_time = split_datetime(
            record.get("last_clock_out_at")
        )

        cols[0].markdown(f"**Project**\n\n{project_name}")
        cols[1].markdown(f"**Status**\n\n{record.get('status')}")
        cols[2].markdown(
            f"**Minutes Worked**\n\n{record.get('minutes_worked', 0)}"
        )
        cols[3].markdown(f"**Clock In Date**\n\n{clock_in_date}")
        cols[4].markdown(f"**Clock In Time**\n\n{clock_in_time}")
        cols[5].markdown(f"**Clock Out Date**\n\n{clock_out_date}")
        cols[6].markdown(f"**Clock Out Time**\n\n{clock_out_time}")
