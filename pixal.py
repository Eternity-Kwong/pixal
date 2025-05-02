# pixal_2.0.py

from datetime import datetime, timedelta  # Add this at the top with other imports
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from datetime import date
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd
import os
from io import BytesIO
import numpy as np
import random

# ------------------- SETUP -------------------
st.set_page_config(page_title="Pixal 2.0", layout="centered")
analyzer = SentimentIntensityAnalyzer()
today = str(date.today())
DATA_FILE = "mood_log.csv"

# ------------------- FUNCTIONS -------------------
def vary_color(hex_color):
    # Slightly vary the RGB values from the original hex
    r, g, b = [int(x * 255) for x in to_rgb(hex_color)]
    r = min(255, max(0, r + random.randint(-15, 15)))
    g = min(255, max(0, g + random.randint(-15, 15)))
    b = min(255, max(0, b + random.randint(-15, 15)))
    return f'#{r:02x}{g:02x}{b:02x}'

def mood_to_color(mood_text):
    score = analyzer.polarity_scores(mood_text)["compound"]
    if score >= 0.6:
        return "#70e000", "Very Positive 😄"
    elif score >= 0.2:
        return "#a3f07c", "Positive 🙂"
    elif score > -0.2:
        return "#f3f3a1", "Neutral 😐"
    elif score > -0.6:
        return "#f38e7f", "Negative 😕"
    else:
        return "#d00000", "Very Negative 😔"

def get_resources(emotion):
    resources = {
        "Very Positive 😄": {
            "quote": "Keep shining! ✨",
            "song": "https://open.spotify.com/track/7Ee6XgP8EHKDhTMYLIndu9"
        },
        "Positive 🙂": {
            "quote": "You’re doing amazing.",
            "song": "https://open.spotify.com/track/7KXJLrMlgQbGMY8kr6yJlB"
        },
        "Neutral 😐": {
            "quote": "Stillness is powerful.",
            "song": "https://open.spotify.com/track/6Kfd3XrgqJ0M50O3Z5KN9c"
        },
        "Negative 😕": {
            "quote": "It’s okay to not be okay.",
            "song": "https://open.spotify.com/album/6YgL1xiXpuBsTUK5y1MYuP"
        },
        "Very Negative 😔": {
            "quote": "You’re not alone 💜",
            "song": "https://open.spotify.com/track/2el4Mzv6ctmCk0pTco3xTz"
        },
    }
    return resources.get(emotion, {})

def plot_blended_gradient(color_list):
    width = 800
    height = 50
    gradient = np.zeros((height, width, 3), dtype=np.uint8)
    num_colors = len(color_list)

    for i in range(width):
        pos = (i / width) * (num_colors - 1)
        left_idx = int(pos)
        right_idx = min(left_idx + 1, num_colors - 1)
        ratio = pos - left_idx

        c1 = np.array(to_rgb(color_list[left_idx])) * 255
        c2 = np.array(to_rgb(color_list[right_idx])) * 255
        blended = (1 - ratio) * c1 + ratio * c2
        gradient[:, i, :] = blended.astype(np.uint8)

    fig, ax = plt.subplots(figsize=(10, 1))
    ax.imshow(gradient)
    ax.axis("off")
    return fig

# ------------------- LOAD LOG -------------------
if os.path.exists(USER_DATA_FILE):
    df = pd.read_csv(USER_DATA_FILE)
    color_log = list(df.itertuples(index=False, name=None))
else:
    df = pd.DataFrame(columns=["date", "color", "text"])
    color_log = []

# ------------------- UI -------------------
st.title("🎨 Pixal 2.0")
st.subheader("Your mood, visualized as color 🌈")

st.sidebar.header("👤 User Login")
user_id = st.sidebar.text_input("Enter your name or ID to begin:", "")

if not user_id:
    st.warning("Please enter your user ID to continue.")
    st.stop()

USER_DATA_FILE = f"{user_id}_mood_log.csv"

mood_input = st.text_input("How are you feeling today?", "")

if st.button("Generate Mood Color"):
    if mood_input:
        base_color, emotion = mood_to_color(mood_input)
        varied = vary_color(base_color)

        st.markdown(f"### Your color for today is: `{varied}`")
        st.markdown(f"**Emotion detected:** {emotion}")
        st.color_picker("Mood Color", varied, disabled=True)

        # Add to log
        color_log.append((today, varied, mood_input))
        df = pd.DataFrame(color_log, columns=["date", "color", "text"])
        df.to_csv(USER_DATA_FILE, index=False)

        # Show quote + song
        resources = get_resources(emotion)
        if resources:
            st.markdown(f"> 💬 **Quote**: *{resources['quote']}*")
            st.markdown(f"[🎧 Mood Music]({resources['song']})")

# ------------------- FILTERS & RESET -------------------
st.subheader("History Controls")
col1, col2 = st.columns([1, 2])

with col1:
    if st.button("🔄 Reset Mood History"):
        df = pd.DataFrame(columns=["date", "color", "text"])
        df.to_csv(USER_DATA_FILE, index=False)
        color_log = []
        st.success("Mood history reset. Refreshing...")
        st.experimental_rerun()

with col2:
    time_filter = st.selectbox("Filter by Time Range", ["All", "Week", "Month", "Year"], index=0)

# ------------------- SHOW FILTERED HISTORY -------------------
if color_log:
    st.subheader("Your Mood History 🌈")

    df = pd.read_csv(DATA_FILE)
    df["date"] = pd.to_datetime(df["date"])
    today_dt = pd.to_datetime(date.today())

    if time_filter == "Week":
        filtered_df = df[df["date"] >= today_dt - pd.Timedelta(days=7)]
    elif time_filter == "Month":
        filtered_df = df[df["date"] >= today_dt - pd.DateOffset(months=1)]
    elif time_filter == "Year":
        filtered_df = df[df["date"] >= today_dt - pd.DateOffset(years=1)]
    else:
        filtered_df = df

    color_list = filtered_df["color"].tolist()

    if color_list:
        gradient_fig = plot_blended_gradient(color_list)
        st.pyplot(gradient_fig)

        buf = BytesIO()
        gradient_fig.savefig(buf, format="png")
        st.download_button("📥 Download Mood Gradient", data=buf.getvalue(),
                           file_name=f"pixal_gradient_{time_filter.lower()}.png",
                           mime="image/png", key=f"download_{time_filter.lower()}")
    else:
        st.info(f"No mood entries found for: **{time_filter}**.")
