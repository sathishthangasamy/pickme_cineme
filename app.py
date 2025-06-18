import streamlit as st
import google.generativeai as genai
import os
import markdown

# --- Configuration ---
PAGE_TITLE = "Pickme Cinime"
PAGE_ICON = "🎬"
GEMINI_MODEL_NAME = "gemini-1.5-flash"  # Stable model as of 2025

# System instruction for the AI
SYSTEM_INSTRUCTION = """You are Pickme Cinime, an expert AI assistant specializing in recommending movies and OTT series. Your goal is to help users discover content they'll love based on their preferences, mood, or specific requests.

1. **Understand User Needs**:
   - Carefully analyze the user's input for genres, actors, directors, plot themes, or moods (e.g., "something happy").
   - If the request is vague, ask clarifying questions (e.g., "What genre are you in the mood for?").
   - Prioritize cinema movies over OTT series unless specified otherwise.
   - If a location is mentioned (e.g., "in New York"), tailor cinema recommendations accordingly.

2. **Provide Diverse Recommendations**:
   - Suggest 1–3 movies or OTT series, mixing well-known and lesser-known titles.
   - For cinema movies, include:
     - **Title**, brief justification, mock ratings (e.g., IMDb 7.8/10, Rotten Tomatoes 85%), mock review snippet, mock showtimes (e.g., "Cineplex Central at 7:00 PM").
     - A booking link (e.g., Fandango search) if location is provided; otherwise, prompt for city.
   - For OTT series, include:
     - **Title**, streaming platform (mock, e.g., Netflix), brief justification, mock rating.
   - Use Markdown for formatting (e.g., **bold titles**, bullet points).

3. **Tone**:
   - Friendly, enthusiastic, and knowledgeable, like a movie buff friend.
   - Keep responses concise and engaging.

4. **Handling Moods**:
   - If a mood is selected (e.g., "Happy"), recommend content aligned with that emotion:
     - **Happy**: Comedies, feel-good movies.
     - **Thrilling**: Action, suspense, thrillers.
     - **Thoughtful**: Dramas, documentaries.
     - **Relaxing**: Light-hearted or visually soothing content.
     - **Funny**: Comedies, satirical series.

5. **Search Grounding**:
   - Use Google Search grounding for up-to-date information (e.g., cinema showtimes).
   - Cite sources as clickable URLs with titles below the response.

6. **Limitations**:
   - State that direct ticket booking is "coming soon" if asked.
   - Avoid recommending excessively violent or inappropriate content unless explicitly requested.
   - If unable to fulfill a request, suggest alternatives or ask for more details.

Let's make movie discovery fun!
"""

# Mood-based prompts
MOOD_PROMPTS = {
    "😄 Happy": "I'm in the mood for something happy and uplifting! Recommend movies or series.",
    "😨 Thrilling": "I want something thrilling and suspenseful. Suggest movies or series.",
    "🤔 Thoughtful": "I'd like a thoughtful or intriguing movie/series. What do you suggest?",
    "😌 Relaxing": "Recommend relaxing or chill movies/series for a quiet evening.",
    "😂 Funny": "I need a good laugh! Suggest funny movies or series.",
}

# Mock data for cinema and OTT
def get_mock_cinema_data(title, location=None):
    return {
        "title": title,
        "justification": f"{title} matches your preferences.",
        "rating": "IMDb: 7.8/10, Rotten Tomatoes: 85%",
        "review_snippet": f"Critics call {title} 'a must-watch!'",
        "showtimes": "Cineplex Central at 7:00 PM, 9:30 PM",
        "booking_link": (
            f"https://www.fandango.com/search?q={title.replace(' ', '+')}+{location.replace(' ', '+')}"
            if location else "https://www.fandango.com"
        ),
    }

def get_mock_ott_data(title):
    return {
        "title": title,
        "platform": "Netflix",
        "justification": f"{title} is perfect for your taste.",
        "rating": "IMDb: 8.0/10",
    }

# --- Streamlit Page Setup ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
st.title(f"{PAGE_ICON} {PAGE_TITLE}")

# --- API Key and Model Initialization ---
try:
    api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("🚨 Google API Key not found. Set GOOGLE_API_KEY in environment or Streamlit secrets.")
        st.stop()

    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(GEMINI_MODEL_NAME, system_instruction=SYSTEM_INSTRUCTION)
    st.session_state.model = model
    if "chat" not in st.session_state:
        st.session_state.chat = model.start_chat(history=[])

except Exception as e:
    st.error(f"🚨 Error initializing Gemini API: {e}")
    st.stop()

# --- Chat History Management ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_location" not in st.session_state:
    st.session_state.user_location = None

# --- Neon Noir Theme ---
st.markdown(
    """
    <style>
    .stApp {
        background-color: #1a1a1a;
        color: #e0e0e0;
        font-family: 'Poppins', sans-serif;
    }
    .user-message {
        background-color: #4a0e5e;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
        text-align: right;
        max-width: 70%;
        margin-left: auto;
    }
    .assistant-message {
        background-color: #0e4a4a;
        border-radius: 10px;
        padding: 10px;
        margin: 5px 0;
        text-align: left;
        max-width: 70%;
    }
    .stTextInput > div > div > input {
        background-color: #2a2a2a;
        color: #e0e0e0;
        border: 1px solid #9b59b6;
    }
    .stButton > button {
        background-color: #9b59b6;
        color: #e0e0e0;
        border: none;
        border-radius: 5px;
    }
    a {
        color: #1abc9c;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- UI Rendering ---
if not st.session_state.chat_history:
    st.info("Welcome to Pickme Cinime! Ask for movie/OTT recommendations or pick a mood below.")

# Display chat history
for message in st.session_state.chat_history:
    role = "user" if message["role"] == "user" else "assistant"
    with st.chat_message(role):
        st.markdown(
            f'<div class={"user-message" if role == "user" else "assistant-message"}>{message["content"]}</div>',
            unsafe_allow_html=True,
        )
        if "sources" in message and message["sources"]:
            st.caption("Sources:")
            for i, source in enumerate(message["sources"]):
                st.caption(f"{i+1}. [{source.get('title', 'N/A')}]({source.get('uri', '#')})")

# Mood buttons
st.subheader("Quick Picks by Mood:")
cols = st.columns(len(MOOD_PROMPTS))
mood_button_clicked = False
user_input_for_ai = None
for i, (mood, prompt_text) in enumerate(MOOD_PROMPTS.items()):
    if cols[i].button(mood, key=f"mood_{i}", use_container_width=True):
        mood_button_clicked = True
        user_input_for_ai = prompt_text
        break

# Chat input
user_query = st.chat_input("Ask for a movie or series recommendation...")

# --- Process Input ---
if user_query or mood_button_clicked:
    actual_input = user_query if user_query else user_input_for_ai

    # Add user message to history
    if actual_input:
        st.session_state.chat_history.append({"role": "user", "content": actual_input})
        with st.chat_message("user"):
            st.markdown(f'<div class="user-message">{actual_input}</div>', unsafe_allow_html=True)

        with st.chat_message("assistant"):
            with st.spinner("Pickme Cinime is thinking... 🤔"):
                try:
                    # Extract location
                    import re
                    location_match = re.search(r"in\s+([A-Za-z\s]+)", actual_input, re.IGNORECASE)
                    if location_match:
                        st.session_state.user_location = location_match.group(1).strip()

                    # Send message to Gemini
                    response = st.session_state.chat.send_message(
                        actual_input,
                        tools=[{"google_search_retrieval": {"disable_attribution": False}}]
                    )
                    response_text = response.text

                    # Mock recommendations for cinema/OTT
                    if "cinema" in actual_input.lower() or "movie" in actual_input.lower():
                        if not st.session_state.user_location:
                            response_text += "\n\n**Please provide your city** for cinema showtimes!"
                        else:
                            cinema_rec = get_mock_cinema_data("Dune: Part Two", st.session_state.user_location)
                            response_text += f"""
                            **Cinema Recommendation: {cinema_rec['title']}**
                            - Justification: {cinema_rec['justification']}
                            - Rating: {cinema_rec['rating']}
                            - Review: {cinema_rec['review_snippet']}
                            - Showtimes: {cinema_rec['showtimes']}
                            - Booking: [Find tickets]({cinema_rec['booking_link']}) (Booking coming soon)
                            """
                    if "series" in actual_input.lower() or "ott" in actual_input.lower():
                        ott_rec = get_mock_ott_data("Stranger Things")
                        response_text += f"""
                        **OTT Recommendation: {ott_rec['title']}**
                        - Platform: {ott_rec['platform']}
                        - Justification: {ott_rec['justification']}
                        - Rating: {ott_rec['rating']}
                        """

                    # Mock sources
                    sources = [
                        {"url": "https://www.imdb.com", "title": "IMDb"},
                        {"url": "https://www.rottentomatoes.com", "title": "Rotten Tomatoes"},
                    ]
                    response_text += "\n\n**Sources**:\n" + "\n".join([f"- [{src['title']}]({src['url']})" for src in sources])

                    # Convert to HTML
                    response_html = markdown.markdown(response_text)
                    st.markdown(f'<div class="assistant-message">{response_html}</div>', unsafe_allow_html=True)

                    # Add to history
                    st.session_state.chat_history.append({"role": "assistant", "content": response_html, "sources": sources})

                except Exception as e:
                    error_message = f"Sorry, I encountered an error: {str(e)}."
                    st.markdown(f'<div class="assistant-message">{error_message}</div>', unsafe_allow_html=True)
                    st.session_state.chat_history.append({"role": "assistant", "content": error_message})

    # Rerun to clear input or update UI
    st.rerun()
