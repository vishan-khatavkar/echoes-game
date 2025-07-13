import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
from streamlit_authenticator import Authenticate
import yaml
from yaml.loader import SafeLoader

# Load credentials from secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gspread"]["credentials_json"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Open Google Sheet by ID
SHEET_ID = st.secrets["gspread"]["sheet_id"]
worksheet = client.open_by_key(SHEET_ID).sheet1  # Assumes first sheet

# Authenticator Setup
auth_config = {
    "credentials": {
        "usernames": {
            "demo@gmail.com": {
                "email": "demo@gmail.com",
                "name": "Demo User",
                "password": "demo"
            }
        }
    }
}
auth = Authenticate(
    auth_config["credentials"], 
    "echoes_cookie", 
    "auth_key", 
    cookie_expiry_days=1
)

name, auth_status, username = auth.login("Login", "main")

# --- Handle login
if auth_status is False:
    st.error("Invalid username or password")
elif auth_status is None:
    st.warning("Please enter your credentials")
elif auth_status:
    st.success(f"Welcome, {name}!")

    if "username" not in st.session_state:
        st.session_state.username = username
        st.rerun()  # Trigger rerun to load data with session state

# --- Load or create user data
def load_user_data(username):
    try:
        records = worksheet.get_all_records()
    except Exception as e:
        st.error("❌ Failed to read user data from Google Sheet.")
        st.exception(e)
        return None

    for idx, row in enumerate(records, start=2):  # start=2 to skip header
        if row["username"] == username:
            row["row"] = idx
            return row

    # New user
    return {
        "username": username,
        "current_level": "start",
        "inventory": "",
        "history": "",
        "row": None
    }

# --- Save user data
def save_user_data(user_data):
    row = user_data["row"]
    values = [
        user_data["username"],
        user_data["current_level"],
        user_data["inventory"],
        user_data["history"]
    ]
    if row:  # Existing user
        worksheet.update(f"A{row}:D{row}", [values])
    else:  # New user
        worksheet.append_row(values)

# --- Main game loop
if auth_status:
    user_data = load_user_data(st.session_state.username)
    st.session_state.row_num = user_data["row"]
    st.session_state.user_data = user_data

    st.title("🌌 Echoes of the Void")
    st.write("You find yourself in a dark void, echoes whispering from every direction...")

    choice = st.text_input("What would you like to do?", key="game_input")

    if st.button("Submit"):
        # Example logic to update state
        user_data["history"] += f"\n{choice}"
        user_data["current_level"] = "next_step"
        save_user_data(user_data)
        st.success("Progress saved.")
        st.rerun()
