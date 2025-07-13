import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Echoes of the Void", page_icon="🌌")

# --- Load credentials from secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gspread"]["credentials_json"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# --- Google Sheet Setup ---
SHEET_ID = st.secrets["gspread"]["sheet_id"]
worksheet = client.open_by_key(SHEET_ID).sheet1

# --- Game Logic Functions ---
def load_user_data(username):
    try:
        records = worksheet.get_all_records()
    except Exception as e:
        st.error("Failed to read user data from Google Sheet.")
        st.exception(e)
        return None

    for row in records:
        if row["username"] == username:
            return row

    # New user
    return {
        "username": username,
        "current_level": "start",
        "inventory": "",
        "history": ""
    }


def update_user_data(row_num, game_state, progress):
    worksheet.update(f"B{row_num}", [[game_state]])
    worksheet.update(f"C{row_num}", [[progress]])

# --- UI: Username input and session setup ---
if "username" not in st.session_state:
    st.title("🌌 Echoes of the Void")
    st.markdown("Enter your name to begin your journey into the unknown...")
    username = st.text_input("Enter your name:")
    if st.button("Start"):
        if username.strip():
            st.session_state.username = username.strip()
            st.rerun()
        else:
            st.warning("Name cannot be empty.")
    st.stop()

# --- Load user data ---
user_data = load_user_data(st.session_state.username)
st.session_state.row_num = user_data["row"]
st.session_state.game_state = user_data["game_state"]
st.session_state.progress = user_data["progress"]

# --- Intro if new player ---
if not st.session_state.game_state:
    intro = (
        f"Welcome, **{st.session_state.username}**.\n\n"
        "You awaken in a dimly lit spacecraft. The hum of machinery vibrates through the walls.\n"
        "A blinking console awaits your command.\n\n"
        "*What will you do?*"
    )
    st.session_state.game_state = intro
    st.session_state.progress = "intro"
    update_user_data(st.session_state.row_num, st.session_state.game_state, st.session_state.progress)
    st.rerun()

# --- Game Display and Input ---
st.markdown("#### 👁️ Current Scene")
st.write(st.session_state.game_state)

user_input = st.text_input(">> What do you do?", key="game_input")

if st.button("Submit"):
    if user_input.strip():
        # Append input to story for now (later can replace with Groq logic)
        new_state = st.session_state.game_state + "\n\n> " + user_input + "\nYou did something important..."
        st.session_state.game_state = new_state
        st.session_state.progress = "updated"
        update_user_data(st.session_state.row_num, st.session_state.game_state, st.session_state.progress)
        st.rerun()
    else:
        st.warning("Please type a command before submitting.")

