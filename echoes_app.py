import streamlit as st
import gspread
import json
import requests
from oauth2client.service_account import ServiceAccountCredentials

# =====================
# CONFIG
# =====================
sheet_id = "1An5D_KHWenIR8vQTwqeHU7xnoSayu8Zh5EfZuxYG3Rc"
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# =====================
# GOOGLE SHEETS SETUP
# =====================
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
credentials = ServiceAccountCredentials.from_json_keyfile_dict(
    json.loads(st.secrets["gspread"]["credentials_json"]), scope
)
client = gspread.authorize(credentials)
worksheet = client.open_by_key(sheet_id).sheet1

# =====================
# GAME LOGIC
# =====================
INITIAL_STORY = (
    "You awaken in the smoking remains of your escape pod. "
    "The planet is unfamiliar — barren, stormy, but oddly structured. "
    "To the north, shattered ruins. To the east, a broken AI relay tower. "
    "Your suit HUD flickers."
)

class EchoesOfTheVoid:
    def __init__(self, level=1, inventory=None, history=None):
        self.level = level
        self.inventory = inventory if inventory else []
        self.history = history if history else [INITIAL_STORY]
        self.objectives = ["Locate a power cell", "Stabilize your suit", "Understand the repeating transmission"]

    def prompt_llm(self, user_input):
        context = f"""
You are a text-based RPG engine generating the next scene of a sci-fi survival story. The player is exploring an ancient alien planet after a crash. Inject occasional dry humor, danger, and mystery.

Current level: {self.level}
Inventory: {', '.join(self.inventory) or 'None'}
Objectives: {', '.join(self.objectives)}
Recent history: {' | '.join(self.history[-4:])}

Player typed: "{user_input}"

Describe what happens next. Add choices, discoveries, or threats if relevant. Advance the story or escalate tension as levels progress.
"""
        headers = {
            "Authorization": f"Bearer {GROQ_API_KEY}",
            "Content-Type": "application/json"
        }

        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a sci-fi game engine narrating Echoes of the Void, a survival mystery game."},
                {"role": "user", "content": context}
            ]
        }

        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        return res.json()["choices"][0]["message"]["content"] if res.ok else f"⚠️ Error: {res.status_code}"

# =====================
# DATA UTILS
# =====================
def load_user_data(username):
    records = worksheet.get_all_records()
    for idx, row in enumerate(records):
        if row["username"] == username:
            inventory = json.loads(row["inventory"]) if row["inventory"] else []
            history = json.loads(row["history"]) if row["history"] else [INITIAL_STORY]
            return {
                "row": idx + 2,
                "current_level": int(row["current_level"]),
                "inventory": inventory,
                "history": history
            }
    return None

def save_user_data(row, level, inventory, history):
    try:
        worksheet.update(f"B{row}", [[level]])
        worksheet.update(f"C{row}", [[json.dumps(inventory)]])
        worksheet.update(f"D{row}", [[json.dumps(history)]])
    except Exception as e:
        st.error(f"Error saving user data: {e}")

def create_new_user(username):
    records = worksheet.get_all_records()
    row = len(records) + 2
    worksheet.update(f"A{row}", [[username]])
    worksheet.update(f"B{row}", [[1]])
    worksheet.update(f"C{row}", [[json.dumps([])]])
    worksheet.update(f"D{row}", [[json.dumps([INITIAL_STORY])]])
    return row

# =====================
# STREAMLIT APP
# =====================
st.set_page_config("Echoes of the Void", layout="centered")
st.title("🌌 Echoes of the Void")

# === LOGIN FLOW ===
if "username" not in st.session_state:
    username = st.text_input("Enter your codename to begin:", key="login_input")
    if st.button("🚀 Begin"):
        if username.strip():
            st.session_state.username = username.strip()
            st.rerun()
        else:
            st.warning("Please enter a codename.")
    st.stop()

# === INIT USER ===
if "game" not in st.session_state:
    user_data = load_user_data(st.session_state.username)
    if user_data:
        st.session_state.row = user_data["row"]
        st.session_state.game = EchoesOfTheVoid(
            level=user_data["current_level"],
            inventory=user_data["inventory"],
            history=user_data["history"]
        )
    else:
        st.session_state.row = create_new_user(st.session_state.username)
        st.session_state.game = EchoesOfTheVoid()

game = st.session_state.game

# === SHOW STORY ===
for line in game.history[-6:]:
    st.markdown(f"📝 {line}")

# === INPUT FIELD + HANDLING ===
user_input = st.text_input(
    "What do you do next?",
    placeholder="e.g. examine HUD, go east...",
    key="user_input",
)

# Process only if user hit Enter or typed something
if user_input.strip():
    game.history.append(f"You: {user_input}")
    response = game.prompt_llm(user_input)
    game.history.append(response)

    if len(game.history) % 6 == 0:
        game.level += 1
        game.history.append(f"🔺 You’ve advanced to Level {game.level}.")

    save_user_data(st.session_state.row, game.level, game.inventory, game.history)

    # Clear the input after submission
    st.session_state.user_input = ""
    st.rerun()
