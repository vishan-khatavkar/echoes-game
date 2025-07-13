import streamlit as st
import json
import gspread
import requests
from oauth2client.service_account import ServiceAccountCredentials

# --- Load Secrets ---
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"


# --- Setup Google Sheets client from secrets ---
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gspread"]["credentials_json"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

SHEET_ID = st.secrets["gspread"]["sheet_id"]
worksheet = client.open_by_key(SHEET_ID).worksheet("EchoesOfTheVoid") 
# --- User login ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:
    st.title("🔑 Echoes of the Void")
    username = st.text_input("Enter your username:")
    if st.button("Enter Game") and username.strip():
        st.session_state.username = username.strip().lower()
        st.session_state.logged_in = True
        st.rerun()
    st.stop()

# --- Load or initialize user data ---
def load_user_data(username):
    records = sheet.get_all_records()
    for row in records:
        if row["username"] == username:
            return {
                "username": row["username"],
                "current_level": int(row["current_level"]),
                "inventory": json.loads(row["inventory"]),
                "history": json.loads(row["history"])
            }
    return {
        "username": username,
        "current_level": 1,
        "inventory": [],
        "history": []
    }

def save_user_data(user_data):
    records = sheet.get_all_records()
    for i, row in enumerate(records):
        if row["username"] == user_data["username"]:
            sheet.update(f"B{i+2}:E{i+2}", [[
                user_data["current_level"],
                json.dumps(user_data["inventory"]),
                json.dumps(user_data["history"])
            ]])
            return
    sheet.append_row([
        user_data["username"],
        user_data["current_level"],
        json.dumps(user_data["inventory"]),
        json.dumps(user_data["history"])
    ])

# --- Initialize session state ---
if "user_data" not in st.session_state:
    st.session_state.user_data = load_user_data(st.session_state.username)
if "game_history" not in st.session_state:
    st.session_state.game_history = []
if "user_command" not in st.session_state:
    st.session_state.user_command = ""
if "submitted_command" not in st.session_state:
    st.session_state.submitted_command = ""
if "intro_shown" not in st.session_state:
    st.session_state.intro_shown = False

# --- Intro Story ---
if not st.session_state.intro_shown:
    st.markdown("## 🌌 Echoes of the Void")
    st.markdown("""
    *The year is 3217. Humanity has long abandoned Earth, scattered across the stars.*

    In the vast emptiness of Sector E-89, a distress signal pulses from a long-forgotten colony ship: **The Virelia**.

    You awaken from cryo-sleep. Systems are unstable. AI is corrupted. Crew is missing.

    You remember only your name, and the echo of a voice saying:

    *"Find the Core... or they all perish."*

    What will you do?
    """)
    if st.button("Begin Your Journey"):
        st.session_state.intro_shown = True
        st.rerun()
    st.stop()

# --- Game UI ---
st.title("🌀 Echoes of the Void")
user_data = st.session_state.user_data
st.markdown(f"**Player:** `{user_data['username']}`")
st.markdown(f"**Level:** {user_data['current_level']}")
st.markdown(f"**Inventory:** {', '.join(user_data['inventory']) or 'Empty'}")

for msg in st.session_state.game_history:
    st.markdown(msg, unsafe_allow_html=True)

def submit():
    st.session_state.submitted_command = st.session_state.user_command
    st.session_state.user_command = ""

st.text_input("What will you do next?", key="user_command", on_change=submit)

# --- Game Engine ---
if st.session_state.submitted_command:
    user_command = st.session_state.submitted_command.strip()
    st.session_state.submitted_command = ""

    if user_command != "":
        user_data["history"].append(user_command)

        prompt = (
            f"You are the AI narrator for a space-fantasy game. The player is at level {user_data['current_level']} "
            f"with inventory: {user_data['inventory']}. Their command: '{user_command}'. "
            f"Respond with the result and continue the narrative."
        )

        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": GROQ_MODEL,
            "messages": [
                {"role": "system", "content": "You are a creative AI game engine."},
                {"role": "user", "content": prompt}
            ]
        }

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            reply = response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            reply = f"⚠️ Error: {e}"

        st.session_state.game_history.append(f"🧍 You: {user_command}")
        st.session_state.game_history.append(f"🤖 Narrator: {reply}")

        # Level up or give items (basic logic)
        if "level up" in reply.lower():
            user_data["current_level"] += 1
        if "received" in reply.lower() and "item" in reply.lower():
            user_data["inventory"].append("Mystery Item")

        save_user_data(user_data)
        st.rerun()
