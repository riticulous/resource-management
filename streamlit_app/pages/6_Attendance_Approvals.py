import streamlit as st
import requests
import pandas as pd
from datetime import datetime

# --- CONFIGURATION ---
st.set_page_config(page_title="Attendance Request Approvals", layout="wide")
API_BASE_URL = "http://127.0.0.1:8000"

# --- HELPER FUNCTIONS ---
def authenticated_request(method, endpoint, data=None, params=None):
    """Make authenticated API request"""
    token = st.session_state.get("token")
    if not token:
        st.warning("🔒 Please login first.")
        st.stop()
    
    headers = {"Authorization": f"Bearer {token}"}
    try:
        response = requests.request(
            method, 
            f"{API_BASE_URL}{endpoint}", 
            headers=headers, 
            json=data,
            params=params
        )
        if response.status_code >= 400:
            st.error(f"Error {response.status_code}: {response.text}")
            return None
        return response.json()
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None


def get_pending_requests(request_type=None):
    """Fetch pending attendance requests that need approval"""
    params = {"status": "PENDING"}
    if request_type and request_type != "All":
        params["request_type"] = request_type
    return authenticated_request("GET", "/admin/attendance-requests/", params=params)


def get_all_requests(status=None, request_type=None):
    """Fetch all attendance requests with optional filters"""
    params = {}
    if status and status != "All":
        params["status"] = status
    if request_type and request_type != "All":
        params["request_type"] = request_type
    return authenticated_request("GET", "/admin/attendance-requests/", params=params)


def get_approval_history():
    """Fetch approval history"""
    return authenticated_request("GET", "/admin/attendance-request-approvals/")


def submit_approval(request_id, decision, comment=""):
    """Submit approval/rejection for a request"""
    user_id = st.session_state.get("user_id")
    
    # Fallback: Get user_id from /me/ endpoint if not in session
    if not user_id:
        me_data = authenticated_request("GET", "/me/")
        if me_data and me_data.get("id"):
            user_id = str(me_data["id"])
            st.session_state["user_id"] = user_id  # Cache it
        else:
            st.error("Could not get user ID. Please log out and log back in.")
            return None
    
    payload = {
        "request_id": request_id,
        "approver_user_id": user_id,
        "decision": decision,
        "comment": comment
    }
    return authenticated_request("POST", "/admin/attendance-request-approvals/", data=payload)


def delete_approval(approval_id):
    """Delete an approval record"""
    return authenticated_request("DELETE", f"/admin/attendance-request-approvals/{approval_id}")


def update_approval(approval_id, decision, comment):
    """Update an approval record"""
    payload = {"decision": decision, "comment": comment}
    return authenticated_request("PUT", f"/admin/attendance-request-approvals/{approval_id}", data=payload)


# --- PAGE HEADER ---
st.title("📋 Attendance Request Approvals")
st.markdown("Review and approve attendance requests from your team members.")
st.markdown("---")

# --- TABS ---
tab1, tab2, tab3 = st.tabs(["📥 Pending Requests", "📜 Approval History", "⚙️ Manage Approvals"])

# =====================
# TAB 1: PENDING REQUESTS
# =====================
with tab1:
    st.subheader("Pending Attendance Requests")
    
    # Filters Row
    col_filter, col_refresh = st.columns([3, 1])
    with col_filter:
        filter_type = st.selectbox(
            "Filter by Request Type", 
            ["All", "LEAVE", "WFH", "REGULARIZATION", "SHIFT_CHANGE", "OTHER"],
            key="pending_filter"
        )
    with col_refresh:
        st.write("")  # Spacer
        if st.button("🔄 Refresh", key="refresh_pending"):
            st.rerun()
    
    pending = get_pending_requests(request_type=filter_type if filter_type != "All" else None)
    
    if not pending:
        st.success("🎉 All caught up! No pending requests to approve.")
    else:
        st.info(f"**{len(pending)}** requests waiting for your review")
        
        for req in pending:
            with st.container(border=True):
                # Layout with user info
                col_user, col_info, col_dates, col_actions = st.columns([2, 2, 2, 1])
                
                with col_user:
                    user_name = req.get('user_name', 'Unknown')
                    user_id = req.get('user_id', 'N/A')
                    st.markdown(f"### 👤 {user_name}")
                    st.caption(f"User ID: `{user_id[:8]}...`")
                    if req.get('user_email'):
                        st.caption(f"📧 {req['user_email']}")
                
                with col_info:
                    request_type = req.get('request_type', 'LEAVE')
                    type_emoji = {
                        'LEAVE': '🏖️',
                        'WFH': '🏠',
                        'REGULARIZATION': '📝',
                        'SHIFT_CHANGE': '🔄',
                        'OTHER': '📋'
                    }.get(request_type, '📋')
                    
                    st.markdown(f"**{type_emoji} {request_type}**")
                    st.caption(f"Request ID: `{req.get('id', 'N/A')[:8]}...`")
                    
                    if req.get('reason'):
                        st.write(f"**Reason:** {req['reason']}")
                
                with col_dates:
                    st.metric("Start Date", req.get('start_date', 'N/A'))
                    st.metric("End Date", req.get('end_date', 'N/A'))
                
                with col_actions:
                    st.write("")  # Spacer
                    request_id = req.get('id')
                    
                    # Approve Button
                    if st.button("✅ Approve", key=f"approve_{request_id}", use_container_width=True, type="primary"):
                        result = submit_approval(request_id, "APPROVED", "Approved")
                        if result:
                            st.toast("✅ Request approved!", icon="👍")
                            st.rerun()
                    
                    # Reject with reason
                    with st.popover("❌ Reject", use_container_width=True):
                        reason = st.text_input("Rejection reason", key=f"reason_{request_id}")
                        if st.button("Confirm Reject", key=f"conf_reject_{request_id}", type="primary"):
                            result = submit_approval(request_id, "REJECTED", reason or "Rejected")
                            if result:
                                st.toast("❌ Request rejected", icon="👎")
                                st.rerun()


# =====================
# TAB 2: APPROVAL HISTORY
# =====================
with tab2:
    st.subheader("Approval History")
    
    # Filters
    col_filter1, col_filter2, col_refresh = st.columns([2, 2, 1])
    with col_filter1:
        filter_decision = st.selectbox("Filter by Decision", ["All", "APPROVED", "REJECTED"])
    with col_filter2:
        filter_req_type = st.selectbox(
            "Filter by Request Type", 
            ["All", "LEAVE", "WFH", "REGULARIZATION", "SHIFT_CHANGE", "OTHER"],
            key="history_type_filter"
        )
    with col_refresh:
        st.write("")
        if st.button("🔄 Refresh", key="refresh_history"):
            st.rerun()
    
    # Get history and related request info
    history = get_approval_history()
    all_requests = get_all_requests()
    
    if not history:
        st.info("No approval history found.")
    else:
        # Create lookup for request info
        request_lookup = {}
        if all_requests:
            for req in all_requests:
                request_lookup[req.get('id')] = {
                    'user_name': req.get('user_name', 'Unknown'),
                    'user_id': req.get('user_id'),
                    'request_type': req.get('request_type'),
                    'reason': req.get('reason')
                }
        
        # Enrich history with request info
        enriched_history = []
        for h in history:
            req_id = h.get('request_id')
            req_info = request_lookup.get(req_id, {})
            
            # Filter by request type
            if filter_req_type != "All" and req_info.get('request_type') != filter_req_type:
                continue
            
            enriched_history.append({
                'decision': h.get('decision'),
                'user_name': req_info.get('user_name', 'Unknown'),
                'user_id': str(req_info.get('user_id', 'N/A'))[:8] + '...',
                'request_type': req_info.get('request_type', 'N/A'),
                'comment': h.get('comment'),
                'decided_at': h.get('decided_at', '')[:19],  # Truncate timestamp
                'approval_id': str(h.get('id', ''))[:8] + '...',
            })
        
        # Filter by decision
        if filter_decision != "All":
            enriched_history = [h for h in enriched_history if h.get('decision') == filter_decision]
        
        if enriched_history:
            df = pd.DataFrame(enriched_history)
            df.columns = ['Decision', 'Requester Name', 'User ID', 'Request Type', 'Comment', 'Decided At', 'Approval ID']
            
            # Add status color
            def color_decision(val):
                if val == 'APPROVED':
                    return 'background-color: #d4edda; color: #155724'
                elif val == 'REJECTED':
                    return 'background-color: #f8d7da; color: #721c24'
                return ''
            
            st.dataframe(
                df.style.applymap(color_decision, subset=['Decision']),
                use_container_width=True,
                hide_index=True
            )
            
            st.caption(f"Showing {len(df)} records")
        else:
            st.info("No records match the filters.")


# =====================
# TAB 3: MANAGE APPROVALS (CRUD)
# =====================
with tab3:
    st.subheader("Manage Approval Records")
    
    crud_action = st.radio("Action", ["Update Approval", "Delete Approval"], horizontal=True)
    
    st.markdown("---")
    
    if crud_action == "Update Approval":
        st.write("**Update an existing approval record**")
        
        with st.form("update_form"):
            approval_id = st.text_input("Approval ID (UUID)")
            new_decision = st.selectbox("New Decision", ["APPROVED", "REJECTED"])
            new_comment = st.text_area("New Comment")
            
            submitted = st.form_submit_button("Update Approval", type="primary")
            
            if submitted:
                if approval_id:
                    result = update_approval(approval_id, new_decision, new_comment)
                    if result:
                        st.success("✅ Approval updated successfully!")
                        st.json(result)
                else:
                    st.warning("Please enter an Approval ID")
    
    elif crud_action == "Delete Approval":
        st.write("**Delete an approval record**")
        st.warning("⚠️ This action cannot be undone!")
        
        with st.form("delete_form"):
            approval_id = st.text_input("Approval ID to delete (UUID)")
            confirm = st.checkbox("I confirm I want to delete this record")
            
            submitted = st.form_submit_button("Delete Approval", type="primary")
            
            if submitted:
                if approval_id and confirm:
                    result = delete_approval(approval_id)
                    if result:
                        st.success("✅ Approval deleted successfully!")
                else:
                    st.warning("Please enter an Approval ID and confirm deletion")


# --- SIDEBAR INFO ---
with st.sidebar:
    st.markdown("### ℹ️ About This Page")
    st.markdown("""
    **Attendance Request Approvals** allows managers to:
    
    - 📥 View and approve pending requests
    - 📜 See approval history with filters
    - ⚙️ Manage (update/delete) approvals
    
    ---
    
    **Filters Available:**
    - Request Type (LEAVE, WFH, etc.)
    - Decision (APPROVED, REJECTED)
    """)
