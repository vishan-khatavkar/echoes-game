import streamlit as st
import gspread
import json
from oauth2client.service_account import ServiceAccountCredentials
import requests

# ========== Setup ==========
st.set_page_config(page_title="Echoes of the Void", layout="centered")
st.title("🌀 Echoes of the Void")

# ========== Google Sheets Auth ==========
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds_dict = json.loads(st.secrets["gspread"]["credentials_json"])
credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
client = gspread.authorize(credentials)

# Use Sheet ID instead of name for reliability
SHEET_ID = st.secrets["gspread"]["sheet_id"]
sheet_url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}"
worksheet = client.open_by_key(SHEET_ID).sheet1

# ========== GROQ Configuration ==========
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ========== Game Engine ==========
class EchoesOfTheVoid:
    def __init__(self, level, inventory, history):
        self.level = level
        self.inventory = inventory
        self.history = history
        self.location = "escape pod crash site"
        self.objectives = ["Locate a power cell", "Stabilize your suit", "Understand the repeating transmission"]

    def prompt_llm(self, user_input):
        context = f"""
You are a text-based RPG engine generating the next scene of a sci-fi survival story. The player is exploring an ancient alien planet after a crash. Inject occasional dry humor, danger, and mystery.

Current level: {self.level}
Location: {self.location}
Inventory: {', '.join(self.inventory) if self.inventory else 'None'}
Objectives: {', '.join(self.objectives)}
Recent history: {' | '.join(self.history[-4:])}

Player typed: "{user_input}"

Describe what happens next. Add choices, discoveries, or threats if relevant. Advance the story or escalate tension as levels progress.
"""

        headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
        data = {
            "model": MODEL,
            "messages": [
                {"role": "system", "content": "You are a sci-fi game engine narrating Echoes of the Void, a survival mystery game."},
                {"role": "user", "content": context}
            ]
        }

        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=data)
        return res.json()["choices"][0]["message"]["content"] if res.status_code == 200 else "Error contacting GROQ API."


# ========== Sheet Helpers ==========
def get_user_row(username):
    records = worksheet.get_all_records()
    for i, row in enumerate(records, start=2):  # start=2 because first row is headers
        if row["username"] == username:
            return i
    return None


def load_user_data(username):
    row = get_user_row(username)
    if row:
        data = worksheet.row_values(row)
        current_level = int(data[1]) if len(data) > 1 and data[1].isdigit() else 1

        # Safely parse inventory
        try:
            inventory = json.loads(data[2]) if len(data) > 2 and data[2] else []
        except json.JSONDecodeError:
            inventory = []

        # Safely parse history
        try:
            history = json.loads(data[3]) if len(data) > 3 and data[3] else [
                "You awaken in the smoking remains of your escape pod. The planet is unfamiliar — barren, stormy, but oddly structured. To the north, shattered ruins. To the east, a broken AI relay tower. Your suit HUD flickers."
            ]
        except json.JSONDecodeError:
            history = [
                "You awaken in the smoking remains of your escape pod. The planet is unfamiliar — barren, stormy, but oddly structured. To the north, shattered ruins. To the east, a broken AI relay tower. Your suit HUD flickers."
            ]

        return {
            "row": row,
            "username": username,
            "current_level": current_level,
            "inventory": inventory,
            "history": history
        }

    else:
        # New user — create starting row
        starting_history = [
            "You awaken in the smoking remains of your escape pod. The planet is unfamiliar — barren, stormy, but oddly structured. To the north, shattered ruins. To the east, a broken AI relay tower. Your suit HUD flickers."
        ]
        worksheet.append_row([username, 1, "[]", json.dumps(starting_history)])
        return load_user_data(username)

def save_user_data(row, level, inventory, history):
    worksheet.update(f"B{row}", [[level]])
    worksheet.update(f"C{row}", [[json.dumps(inventory)]])
    worksheet.update(f"D{row}", [[json.dumps(history)]])


# ========== Login ==========
if "username" not in st.session_state:
    st.session_state.username = st.text_input("Enter your codename to begin:", placeholder="e.g. Spectre-41")
    st.stop()

user_data = load_user_data(st.session_state.username)
st.session_state.row = user_data["row"]

# ========== Game Setup ==========
game = EchoesOfTheVoid(user_data["current_level"], user_data["inventory"], user_data["history"])

# ========== Show Game History ==========
st.markdown("### 📜 Story So Far")
for entry in game.history[-4:]:
    st.markdown(f"> {entry}")

# ========== User Input ==========
user_input = st.text_input("What do you do next?", placeholder="e.g. examine HUD, go east...")

if st.button("▶ Continue") and user_input.strip():
    game.history.append(f"You: {user_input}")
    response = game.prompt_llm(user_input)
    game.history.append(f"{response}")

    # Simple level-up every 6 messages
    if len(game.history) % 6 == 0:
        game.level += 1
        game.history.append(f"🔺 You’ve advanced to Level {game.level}.")

    # Save state
    save_user_data(st.session_state.row, game.level, game.inventory, game.history)
    st.rerun()
