import streamlit as st
import requests

# ============= CONFIG =============
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ============= INITIAL SETUP =============
st.set_page_config("🌌 Echoes of the Void", layout="centered")
st.title("🌌 Echoes of the Void")

INITIAL_STORY = (
    "You awaken in the smoking remains of your escape pod. "
    "The planet is unfamiliar — barren, stormy, but oddly structured. "
    "To the north, shattered ruins. To the east, a broken AI relay tower. "
    "Your suit HUD flickers."
)

# ============= GAME CLASS =============
class EchoesOfTheVoid:
    def __init__(self):
        self.level = 1
        self.inventory = []
        self.history = [INITIAL_STORY]
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

# ============= GAME INSTANCE (in session) =============
if "game" not in st.session_state:
    st.session_state.game = EchoesOfTheVoid()

game = st.session_state.game

# ============= DISPLAY HISTORY =============
for line in game.history[-6:]:
    st.markdown(f"📝 {line}")

# ============= INPUT FIELD =============
user_input = st.text_input(
    "What do you do next?",
    placeholder="e.g. examine HUD, go east...",
    key="user_input",
)

# ============= HANDLE TURN =============
if user_input.strip():
    game.history.append(f"You: {user_input}")
    response = game.prompt_llm(user_input)
    game.history.append(response)

    if len(game.history) % 6 == 0:
        game.level += 1
        game.history.append(f"🔺 You’ve advanced to Level {game.level}.")

    st.session_state.user_input = ""
    st.rerun()
