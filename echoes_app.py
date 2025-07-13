import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

# --- Google Sheets Setup ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gspread"]["credentials_json"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Use sheet ID directly
SHEET_ID = st.secrets["gspread"]["sheet_id"]
worksheet = client.open_by_key(SHEET_ID).sheet1

# --- Load user data from sheet ---
def load_user_data(username):
    records = worksheet.get_all_records()
    for idx, row in enumerate(records, start=2):  # Account for header row
        if row["username"] == username:
            return {
                "username": row["username"],
                "current_level": row["current_level"],
                "inventory": row["inventory"],
                "history": row["history"],
                "row": idx
            }
    return None

# --- Save user data to sheet ---
def save_user_data(row_num, username, current_level, inventory, history):
    worksheet.update(f"A{row_num}", [[username, current_level, inventory, history]])

# --- Initialize Session State ---
if "username" not in st.session_state:
    st.session_state.username = ""
if "user_data" not in st.session_state:
    st.session_state.user_data = None
if "row_num" not in st.session_state:
    st.session_state.row_num = None

# --- Login ---
st.title("Echoes of the Void 🌌")
if "login_submitted" not in st.session_state:
    st.session_state.login_submitted = False

if not st.session_state.login_submitted:
    st.session_state.username = st.text_input("Enter your username to begin:")
    if st.button("Start Game"):
        if st.session_state.username.strip():
            st.session_state.login_submitted = True
            st.rerun()
        else:
            st.warning("Please enter a valid username.")
    st.stop()

# --- Load or Create User ---
if not st.session_state.user_data:
    user_data = load_user_data(st.session_state.username)
    if user_data:
        st.session_state.user_data = user_data
        st.session_state.row_num = user_data["row"]
    else:
        # Create new user at the end of the sheet
        next_row = len(worksheet.get_all_values()) + 1
        save_user_data(next_row, st.session_state.username, "intro", "", "")
        st.session_state.row_num = next_row
        st.session_state.user_data = {
            "username": st.session_state.username,
            "current_level": "intro",
            "inventory": "",
            "history": ""
        }
        st.rerun()

# --- Game Logic ---
user = st.session_state.user_data
st.subheader(f"Welcome back, {user['username']}")

st.markdown(f"**Current Level:** {user['current_level']}")
st.markdown(f"**Inventory:** {user['inventory']}")
st.markdown(f"**History:** {user['history']}")

# User input
user_input = st.text_input("What do you want to do next?")

if st.button("Submit"):
    # Append input to history
    user["history"] += f"\n> {user_input}"
    # Mock logic: Advance level for now
    user["current_level"] = "next_level"
    user["inventory"] += ", key" if "key" not in user["inventory"] else ""
    
    # Save to Google Sheets
    save_user_data(
        st.session_state.row_num,
        user["username"],
        user["current_level"],
        user["inventory"],
        user["history"]
    )
    
    st.success("Progress saved!")
    st.rerun()
