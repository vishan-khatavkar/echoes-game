import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials

st.set_page_config(page_title="Echoes of the Void", layout="centered")
st.title("🌌 Echoes of the Void")

# Set scopes and load credentials from Streamlit secrets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gspread"]["credentials_json"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Fallback: Use spreadsheet ID directly (your link provided)
SPREADSHEET_ID = "1An5D_KHWenIR8vQTwqeHU7xnoSayu8Zh5EfZuxYG3Rc"
WORKSHEET_NAME = "EchoesOfTheVoid"

# Access worksheet safely
try:
    sheet = client.open_by_key(SPREADSHEET_ID).worksheet(WORKSHEET_NAME)
    st.success("✅ Connected to Google Sheet successfully!")
except Exception as e:
    st.error("❌ Failed to connect to Google Sheet.")
    st.exception(e)
    st.stop()

# User login simulation
st.subheader("Login")
username = st.text_input("Enter your name:")
if username:
    st.session_state.username = username

    def load_user_data(username):
        records = sheet.get_all_records()
        for record in records:
            if record.get("Username") == username:
                return record
        return None

    def save_user_data(username, data):
        records = sheet.get_all_records()
        for i, record in enumerate(records):
            if record.get("Username") == username:
                sheet.update_cell(i + 2, 2, data["progress"])
                return
        sheet.append_row([username, data["progress"]])

    # Load or initialize user
    user_data = load_user_data(username)
    if not user_data:
        user_data = {"Username": username, "progress": "beginning"}
        save_user_data(username, user_data)

    st.session_state.user_data = user_data

    # Game logic (simplified for demo)
    st.write(f"🌟 Welcome, **{username}**")
    st.write(f"📍 Current progress: `{user_data['progress']}`")
    if st.button("Advance"):
        user_data["progress"] = "next_stage"
        save_user_data(username, user_data)
        st.success("Progress saved!")
