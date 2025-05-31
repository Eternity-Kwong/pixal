# pixal_login_signup.py

import streamlit as st
import pandas as pd
import os
import random
from datetime import date
from matplotlib.colors import to_rgb
import numpy as np
import matplotlib.pyplot as plt
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
from io import BytesIO

st.set_page_config(page_title="Pixal", layout="centered")

# ------------------- SETUP -------------------
analyzer = SentimentIntensityAnalyzer()
today = str(date.today())
USERS_FILE = "users.csv"

# ------------------- FUNCTIONS -------------------
def vary_color(hex_color):
    r, g, b = [int(x * 255) for x in to_rgb(hex_color)]
    r = min(255, max(0, r + random.randint(-15, 15)))
    g = min(255, max(0, g + random.randint(-15, 15)))
    b = min(255, max(0, b + random.randint(-15, 15)))
    return f'#{r:02x}{g:02x}{b:02x}'

def mood_to_color(mood_text):
    score = analyzer.polarity_scores(mood_text)["compound"]

    # Define aesthetic green-to-red gradient stops
    if score >= 0.6:
        return "#b7e4c7", "Very Positive 😄"      # Soft sage green
    elif score >= 0.2:
        return "#d8f3dc", "Positive 🙂"           # Mint cream
    elif score > -0.2:
        return "#fefae0", "Neutral 😐"            # Warm beige
    elif score > -0.6:
        return "#fbc4ab", "Negative 😕"           # Soft coral
    else:
        return "#f4978e", "Very Negative 😔"      # Muted terracotta red

def get_resources(emotion):
    return {
        "Very Positive 😄": {"quote": "Keep shining! ✨", "song": "https://open.spotify.com/track/7Ee6XgP8EHKDhTMYLIndu9"},
        "Positive 🙂": {"quote": "You’re doing amazing.", "song": "https://open.spotify.com/track/7KXJLrMlgQbGMY8kr6yJlB"},
        "Neutral 😐": {"quote": "Stillness is powerful.", "song": "https://open.spotify.com/track/6Kfd3XrgqJ0M50O3Z5KN9c"},
        "Negative 😕": {"quote": "It’s okay to not be okay.", "song": "https://open.spotify.com/album/6YgL1xiXpuBsTUK5y1MYuP"},
        "Very Negative 😔": {"quote": "You’re not alone 💜", "song": "https://open.spotify.com/track/2el4Mzv6ctmCk0pTco3xTz"},
    }.get(emotion, {})

def plot_blended_gradient(color_list):
    width, height = 800, 50
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    for i in range(width):
        pos = (i / width) * (len(color_list) - 1)
        left, right = int(pos), min(int(pos) + 1, len(color_list) - 1)
        blend = (1 - (pos - left)) * np.array(to_rgb(color_list[left])) + (pos - left) * np.array(to_rgb(color_list[right]))
        gradient[:, i] = (blend * 255).astype(np.uint8)
    fig, ax = plt.subplots(figsize=(10, 1))
    ax.imshow(gradient)
    ax.axis("off")
    return fig

def load_users():
    if os.path.exists(USERS_FILE):
        return pd.read_csv(USERS_FILE)
    return pd.DataFrame(columns=["username", "password"])

def save_user(username, password):
    users = load_users()
    if username in users["username"].values:
        return False
    new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
    users = pd.concat([users, new_user], ignore_index=True)
    users.to_csv(USERS_FILE, index=False)
    return True

def authenticate(username, password):
    users = load_users()
    return ((users["username"] == username) & (users["password"] == password)).any()

# ------------------- LOGIN/SIGNUP -------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

def do_login(username, password):
    if username and password:
        if authenticate(username, password):
            st.session_state.logged_in = True
            st.session_state.user_id = username
            st.experimental_rerun()
        else:
            st.error("Invalid username or password.")
    else:
        st.error("Please enter a username and password.")

def do_signup(username, password):
    if username and password:
        if save_user(username, password):
            st.success("Account created and logged in!")
            st.session_state.logged_in = True
            st.session_state.user_id = username
            st.experimental_rerun()
        else:
            st.error("Username already exists.")
    else:
        st.error("Please enter a username and password.")

if not st.session_state.get("logged_in", False):
    st.title("🔐 Welcome to Pixal")
    auth_mode = st.radio("Choose an option:", ["Login", "Sign Up"])
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if auth_mode == "Login":
        st.button("Login", on_click=do_login, args=(username, password))
    else:
        st.button("Sign Up", on_click=do_signup, args=(username, password))

    st.stop()
# ------------------- MAIN APP -------------------
user_id = st.session_state.user_id
USER_DATA_FILE = f"{user_id}_mood_log.csv"
if os.path.exists(USER_DATA_FILE):
    df = pd.read_csv(USER_DATA_FILE)
    color_log = list(df.itertuples(index=False, name=None))
else:
    df = pd.DataFrame(columns=["date", "color", "text"])
    color_log = []

st.title("🎨 Pixal")
st.subheader("Your mood, visualized as color 🌈")
mood_input = st.text_input("How are you feeling today?", "")

if st.button("🎨 Color My Mood"):
    if mood_input:
        color, emotion = mood_to_color(mood_input)
        varied = vary_color(color)
        st.markdown(f"### Your color for today is: `{varied}`")
        st.markdown(f"**Emotion detected:** {emotion}")
        st.color_picker("Mood Color", varied, disabled=True)
        # Save this final color
        color_log.append((today, chosen_color, mood_input))
        pd.DataFrame(color_log, columns=["date", "color", "text"]).to_csv(USER_DATA_FILE, index=False)

        color_log.append((today, varied, mood_input))
        pd.DataFrame(color_log, columns=["date", "color", "text"]).to_csv(USER_DATA_FILE, index=False)
        r = get_resources(emotion)
        if r: st.markdown(f"> 💬 *{r['quote']}*\n\n[🎧 Mood Music]({r['song']})")

st.subheader("History Controls")
col1, col2 = st.columns([1, 2])
with col1:
    if st.button("🔄 Reset Mood History"):
        pd.DataFrame(columns=["date", "color", "text"]).to_csv(USER_DATA_FILE, index=False)
        st.success("History cleared!")
        st.rerun()
with col2:
    time_filter = st.selectbox("Filter by Time Range", ["All", "Week", "Month", "Year"], index=0)

if color_log:
    st.subheader("Your Mood History 🌈")
    df = pd.read_csv(USER_DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    now = pd.to_datetime(date.today())
    if time_filter == "Week":
        df = df[df["date"] >= now - pd.Timedelta(days=7)]
    elif time_filter == "Month":
        df = df[df["date"] >= now - pd.DateOffset(months=1)]
    elif time_filter == "Year":
        df = df[df["date"] >= now - pd.DateOffset(years=1)]
    colors = df["color"].tolist()
    if colors:
        fig = plot_blended_gradient(colors)
        st.pyplot(fig)
        buf = BytesIO()
        fig.savefig(buf, format="png")
        st.download_button("📥 Download Mood Gradient", data=buf.getvalue(), file_name="mood_gradient.png", mime="image/png")
    else:
        st.info("No entries for this time range.")
