import streamlit as st
import os
import requests
from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")

# Initialize Supabase client
supabase = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

def login_ui():
    st.title("Login")

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        try:
            # 1. Authenticate with Supabase
            res = supabase.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            token = res.session.access_token
            st.session_state["token"] = token
            st.session_state["user"] = res.user
            st.session_state["user_email"] = res.user.email
            
            # 2. Get the DB user ID from /me/ endpoint
            try:
                headers = {"Authorization": f"Bearer {token}"}
                me_response = requests.get(f"{API_BASE_URL}/me", headers=headers)
                if me_response.status_code == 200:
                    me_data = me_response.json()
                    st.session_state["user_id"] = me_data.get("id")  # DB user ID
                    st.session_state["user_name"] = me_data.get("name")
                else:
                    st.warning("Could not fetch user details from API")
            except Exception:
                pass  # Will use fallback in approval page
            
            st.success("Logged in successfully")
            st.rerun()
        except Exception as e:
            st.error(str(e))


def require_auth():
    if "token" not in st.session_state:
        login_ui()
        st.stop()
