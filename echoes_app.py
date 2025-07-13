import streamlit as st
import requests
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Retrieve your GROQ API key
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Example: use in request headers
headers = {
    "Authorization": f"Bearer {GROQ_API_KEY}",
    "Content-Type": "application/json"
}


# ========== CONFIGURATION ==========
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# ========== SESSION STATE INIT ==========
if "level" not in st.session_state:
    st.session_state.level = 1
    st.session_state.location = "escape pod crash site"
    st.session_state.inventory = []
    st.session_state.history = [
        "You awaken in the smoking remains of your escape pod. The planet is unfamiliar — barren, stormy, but oddly structured. To the north, shattered ruins. To the east, a broken AI relay tower. Your suit HUD flickers."
    ]
    st.session_state.objectives = [
        "Locate a power cell",
        "Stabilize your suit",
        "Understand the repeating transmission"
    ]


# ========== FUNCTION: CALL GROQ MODEL ==========
def prompt_llm(user_input):
    context = f"""
You are a text-based RPG engine generating the next scene of a sci-fi survival story. The player is exploring an ancient alien planet after a crash. Inject occasional dry humor, danger, and mystery.

Current level: {st.session_state.level}
Location: {st.session_state.location}
Inventory: {', '.join(st.session_state.inventory) or 'None'}
Objectives: {', '.join(st.session_state.objectives)}
Recent history: {' | '.join(st.session_state.history[-4:])}

Player typed: "{user_input}"

Describe what happens next. Add choices, discoveries, or threats if relevant. Advance the story or escalate tension as levels progress.
"""

    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "You are a sci-fi game engine narrating Echoes of the Void, a survival mystery game."},
            {"role": "user", "content": context}
        ]
    }

    response = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json=payload
    )

    if response.status_code != 200:
        return f"Error: {response.status_code} - {response.text}"

    return response.json()["choices"][0]["message"]["content"]


# ========== STREAMLIT UI ==========
st.set_page_config(page_title="Echoes of the Void", page_icon="🌌")
st.title("🌌 Echoes of the Void")
st.markdown("A sci-fi text adventure powered by Groq AI")

# Sidebar
with st.sidebar:
    st.header("🧠 Game Stats")
    st.markdown(f"**Level:** {st.session_state.level}")
    st.markdown(f"**Location:** {st.session_state.location}")
    st.markdown(f"**Inventory:** {', '.join(st.session_state.inventory) or 'None'}")
    st.markdown("**Objectives:**")
    for obj in st.session_state.objectives:
        st.markdown(f"- {obj}")

# Story display
st.markdown("### 📜 Story So Far")
for entry in st.session_state.history[-10:]:
    st.markdown(entry)

# Input form
st.markdown("### ✍️ What will you do?")
with st.form(key="input_form", clear_on_submit=True):
    user_input = st.text_input("Enter your command", placeholder="e.g. go north, examine ruins...")
    submitted = st.form_submit_button("Send")

if submitted and user_input:
    response = prompt_llm(user_input)
    st.session_state.history.append(f"**You:** {user_input}")
    st.session_state.history.append(f"**Game:** {response}")

    # Simple level-up mechanic
    if len(st.session_state.history) % 6 == 0:
        st.session_state.level += 1
        st.session_state.objectives.append(f"Unlock secrets of Level {st.session_state.level}")
        st.success(f"🔺 You’ve reached Level {st.session_state.level}!")

    st.rerun()
