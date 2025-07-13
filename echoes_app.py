import streamlit as st
import requests

# =====================
# CONFIG
# =====================
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

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
# STREAMLIT APP
# =====================
st.set_page_config("Echoes of the Void", layout="centered")
st.title("🌌 Echoes of the Void")

# === Reset Game Button ===
if st.button("🔄 Reset Game"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.rerun()

# === Init Game Once ===
if "game" not in st.session_state:
    st.session_state.game = EchoesOfTheVoid()

game = st.session_state.game

# === Show Game History ===
for line in game.history[-6:]:
    st.markdown(f"📝 {line}")

# === Input Control Flags ===
if "clear_input_box" not in st.session_state:
    st.session_state.clear_input_box = False

if "input_submitted" not in st.session_state:
    st.session_state.input_submitted = False

input_container = st.empty()

# Show input field with forced clear if needed
if st.session_state.clear_input_box:
    user_input = input_container.text_input(
        "What do you do next?",
        value="",
        placeholder="e.g. examine HUD, go east..."
    )
else:
    user_input = input_container.text_input(
        "What do you do next?",
        placeholder="e.g. examine HUD, go east..."
    )

# Handle new input
if user_input and not st.session_state.input_submitted:
    st.session_state.last_input = user_input
    st.session_state.input_submitted = True
    st.session_state.clear_input_box = True
    st.rerun()

# === Process submitted input ===
if st.session_state.input_submitted and "last_input" in st.session_state:
    user_input = st.session_state.last_input.strip()

    if user_input:
        game.history.append(f"You: {user_input}")
        game.history.append(game.prompt_llm(user_input))

        if len(game.history) % 6 == 0:
            game.level += 1
            game.history.append(f"🔺 You’ve advanced to Level {game.level}.")

    # Clear flags and rerun
    del st.session_state["last_input"]
    st.session_state.input_submitted = False
    st.session_state.clear_input_box = False
    st.rerun()
