import streamlit as st
import requests
import os

# 🔐 Get GROQ API Key securely
GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
GROQ_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

# 🧠 Init session state
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "username": "",
        "current_level": 1,
        "inventory": [],
        "history": [],
    }
if "game_history" not in st.session_state:
    st.session_state.game_history = []

# 🔐 Login screen
if not st.session_state.logged_in:
    st.title("🔑 Welcome to Echoes of the Void")
    username = st.text_input("Enter your name to begin:")
    if st.button("Start Game") and username.strip():
        st.session_state.logged_in = True
        st.session_state.user_data["username"] = username.strip().title()
        st.success(f"Welcome, {username.strip().title()}!")
        st.rerun()
    st.stop()

# 🧑‍🚀 Main game UI
st.title("🌀 Echoes of the Void")
st.markdown(f"**Logged in as:** `{st.session_state.user_data['username']}`")
st.markdown(f"**Current Level:** {st.session_state.user_data['current_level']}")
st.markdown(f"**Inventory:** {', '.join(st.session_state.user_data['inventory']) or 'Empty'}")

# 🧾 Display game history
for msg in st.session_state.game_history:
    st.markdown(msg, unsafe_allow_html=True)

# 🗨️ User command input
user_command = st.text_input("What will you do next?", key="user_command")

if st.button("Send"):
    if user_command.strip() != "":
        st.session_state.user_data["history"].append(user_command)

        # 🧠 Build prompt with user state
        prompt = (
            f"You are the dynamic AI narrator for a space-fantasy game called 'Echoes of the Void'. "
            f"The player is at level {st.session_state.user_data['current_level']}, "
            f"with the following inventory: {st.session_state.user_data['inventory']}. "
            f"Their last command was: '{user_command}'. "
            f"Respond with the result of that action, and continue the story dynamically."
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

        response = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        reply = response.json()["choices"][0]["message"]["content"]

        # ⬇️ Save reply
        st.session_state.game_history.append(f"🧍 You: {user_command}")
        st.session_state.game_history.append(f"🤖 Narrator: {reply}")

        # Optionally: Detect progress
        if "level up" in reply.lower():
            st.session_state.user_data["current_level"] += 1
        if "received" in reply.lower() and "item" in reply.lower():
            st.session_state.user_data["inventory"].append("Mystery Item")

        # Clear input
        st.experimental_rerun()
