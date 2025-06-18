import streamlit as st
import google.generativeai as genai
import os
import time

# --- Configuration ---
PAGE_TITLE = "Pickme Cinime"
PAGE_ICON = "🎬"
# Using the model name as provided by the user
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17" 

# System instruction for the AI
SYSTEM_INSTRUCTION = """You are Pickme Cinime, an expert AI assistant specializing in recommending movies and OTT series. Your goal is to help users discover content they'll love based on their preferences, mood, or specific requests.

Here's how you should behave:

1.  **Understand User Needs**:
    * Carefully analyze the user's input. They might specify genres, actors, directors, plot themes, moods (e.g., "something happy," "a thrilling mystery"), or even ask for "something similar to..."
    * If the request is vague (e.g., "recommend a movie"), ask clarifying questions like "What genre are you in the mood for?" or "Any particular actors or themes you enjoy?" before giving a broad recommendation. However, if they use a mood button, assume that's their primary preference.

2.  **Provide Diverse Recommendations**:
    * Suggest a mix of well-known hits and lesser-known gems if appropriate.
    * Include content from various streaming platforms if not specified by the user. If you know where a specific title is streaming, you can mention it (e.g., "available on Netflix").
    * Aim for 2-3 recommendations per request unless the user asks for more or less.

3.  **Give Key Details (Concise & Engaging)**:
    * For each recommendation, provide:
        * **Title (and Year)**
        * **A brief, engaging synopsis** (1-2 sentences) highlighting what makes it special.
        * **Genre(s)**
        * **Why it fits the user's request** (e.g., "This fits your request for a 'thrilling mystery' because...").
    * Use Markdown for formatting (bold titles, bullet points for lists of recommendations).

4.  **Tone**:
    * Friendly, enthusiastic, and knowledgeable – like a passionate movie buff friend.
    * Keep responses relatively concise and easy to read.

5.  **Handling Moods**:
    * If a user clicks a mood button (e.g., "Happy," "Thrilling"), generate recommendations that strongly align with that emotion. For example:
        * **Happy/Uplifting**: Feel-good movies, comedies, inspiring stories.
        * **Thrilling**: Suspense, action, horror, psychological thrillers.
        * **Thoughtful/Intriguing**: Dramas, documentaries, films with complex themes, mind-bending plots.
        * **Relaxing/Chill**: Light-hearted content, comfort watches, visually beautiful films.
        * **Funny**: Comedies, stand-up specials, satirical content.

6.  **Safety and Limitations**:
    * Do not recommend content that is excessively violent, graphic, or inappropriate for a general audience unless specifically asked for mature themes (and even then, with a warning).
    * If you cannot fulfill a request or don't have enough information, politely say so and perhaps offer alternatives or ask for more details.
    * You are an AI and do not have personal opinions or feelings.

7.  **Search Grounding**:
    * You have access to Google Search for up-to-date information. If you use search results to answer a query (e.g., for very new releases, current events related to film/TV), make sure the information is relevant.
    * If web sources are used and returned by the API, they will be displayed to the user.

Let's make movie and series discovery fun and easy!
"""

# Mood-based prompts
MOOD_PROMPTS = {
    "😄 Happy": "I'm in the mood for something happy and uplifting! Can you recommend some movies or series?",
    "😨 Thrilling": "I want something thrilling and suspenseful. Give me some movie or series recommendations.",
    "🤔 Thoughtful": "I'd like a thoughtful or intriguing movie/series. What do you suggest?",
    "😌 Relaxing": "Recommend some relaxing or chill movies/series for a quiet evening.",
    "😂 Funny": "I need a good laugh! What are some funny movies or series?",
}

# --- Streamlit Page Setup ---
st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
st.title(f"{PAGE_ICON} {PAGE_TITLE}")

# --- API Key and Model Initialization ---
# Ensure GOOGLE_API_KEY is set as an environment variable or Streamlit secret
api_key = os.environ.get("GOOGLE_API_KEY") or st.secrets.get("GOOGLE_API_KEY")

base_generative_model = None
if not api_key:
    st.error("🚨 Google API Key not found. Please set the GOOGLE_API_KEY environment variable or add it to Streamlit secrets.")
    st.stop() # Stop the app if no API key is found
else:
    try:
        genai.configure(api_key=api_key)
        base_generative_model = genai.GenerativeModel(
            GEMINI_MODEL_NAME,
            system_instruction=SYSTEM_INSTRUCTION
        )
        # Verify model availability
        # This is an optional, but good sanity check, can be removed after initial setup
        # for model_info in genai.list_models():
        #     if model_info.name == f"models/{GEMINI_MODEL_NAME}":
        #         st.sidebar.success(f"Model '{GEMINI_MODEL_NAME}' found and ready.")
        #         break
        # else:
        #     st.error(f"🚨 Model '{GEMINI_MODEL_NAME}' not found or accessible. Please check the model name and API key permissions.")
        #     st.stop()

    except Exception as e:
        st.error(f"🚨 Error initializing the Gemini API or configuring: {e}")
        st.info("Please check your API key and ensure it has permissions for the specified model.")
        st.stop()

# --- Chat History Management ---
# Initialize chat_history as a list of dictionaries, storing role, content, and sources
if "chat_history" not in st.session_state:
    st.session_state.chat_history = [] 
# Initialize chat_session with the base model, ensuring history is empty on first run
if "chat_session" not in st.session_state:
    if base_generative_model: # Only start chat if model initialized successfully
        st.session_state.chat_session = base_generative_model.start_chat(history=[])
    else:
        st.error("AI model not initialized. Please resolve API key/model issues.")
        st.stop()


# Function to send message to AI and get response
def get_ai_response(prompt_text):
    if not st.session_state.chat_session:
        st.error("Chat session not initialized. Cannot send message.")
        return None
    try:
        # Use GoogleSearchRetrieval tool for grounding
        response = st.session_state.chat_session.send_message(
            prompt_text,
            generation_config=genai.types.GenerationConfig(
                tools=[genai.types.Tool(google_search_retrieval=genai.types.GoogleSearchRetrieval())]
            )
        )
        return response
    except Exception as e:
        # More detailed error logging for debugging
        st.error(f"🚨 Error communicating with the AI (get_ai_response): {e}")
        st.exception(e) # Display full traceback in the Streamlit app
        return None

# --- UI Rendering ---

# Display chat history from session state
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        # Display sources if available
        if "sources" in message and message["sources"]:
            st.caption("Retrieved sources:")
            for i, source in enumerate(message["sources"]):
                st.caption(f"{i+1}. {source.get('title', 'N/A')}: {source.get('uri', '#')}")

# Welcome message if chat is empty
if not st.session_state.chat_history:
    st.info(
        "Welcome to Pickme Cinime! Ask me for movie or OTT series recommendations, "
        "or use the mood buttons below to get started."
    )

# Mood buttons
st.subheader("Quick Picks by Mood:")
# Create columns dynamically based on the number of mood prompts
cols = st.columns(len(MOOD_PROMPTS))
mood_button_clicked_prompt = None
for i, (mood_display, mood_prompt_text) in enumerate(MOOD_PROMPTS.items()):
    if cols[i].button(mood_display, key=f"mood_{i}", use_container_width=True):
        mood_button_clicked_prompt = mood_prompt_text
        break # Exit loop once a button is clicked to avoid processing multiple clicks

# Chat input from user
user_typed_query = st.chat_input("Ask for a movie or series recommendation...")

final_prompt_to_process = None
if mood_button_clicked_prompt:
    final_prompt_to_process = mood_button_clicked_prompt
elif user_typed_query:
    final_prompt_to_process = user_typed_query

# Process the prompt if either a mood button was clicked or text was entered
if final_prompt_to_process:
    # Add user's message to chat history and display it immediately
    st.session_state.chat_history.append({"role": "user", "content": final_prompt_to_process})
    with st.chat_message("user"):
        st.markdown(final_prompt_to_process)

    # Get AI response and display it
    with st.chat_message("assistant"):
        with st.spinner("Pickme Cinime is thinking... 🤔"):
            ai_response_object = get_ai_response(final_prompt_to_process)

            if ai_response_object:
                response_text = ""
                try:
                    # Attempt to extract text from the AI response
                    response_text = ai_response_object.text
                except Exception as e_text:
                    # Handle cases where ai_response_object.text might not be directly available
                    # (e.g., if the model returned only tool calls or other complex outputs)
                    st.error(f"Error extracting text from AI response: {str(e_text)}")
                    response_text = "Sorry, I had trouble understanding the AI's answer. It might have returned a non-text response."
                    # You might want to print the full ai_response_object here for debugging
                    # st.write(ai_response_object)

                st.markdown(response_text)
                
                # Prepare assistant message to be added to chat history
                assistant_message = {"role": "assistant", "content": response_text, "sources": []}

                try:
                    # Attempt to extract and display grounding sources
                    # Check if candidates and grounding_metadata exist before accessing
                    if ai_response_object.candidates and \
                       ai_response_object.candidates[0] and \
                       ai_response_object.candidates[0].grounding_metadata:
                        
                        grounding_meta = ai_response_object.candidates[0].grounding_metadata
                        if grounding_meta.grounding_chunks:
                            st.caption("Retrieved sources:")
                            for i, chunk in enumerate(grounding_meta.grounding_chunks):
                                # Ensure 'web' and 'uri' attributes exist
                                if chunk.web and chunk.web.uri:
                                    source_info = {"title": chunk.web.title or 'Untitled', "uri": chunk.web.uri}
                                    assistant_message["sources"].append(source_info)
                                    st.caption(f"{i+1}. [{source_info['title']}]({source_info['uri']})")
                except Exception as e_source:
                    st.warning(f"Could not retrieve sources from AI response: {str(e_source)}")
                
                # Add the complete assistant message (with text and sources) to chat history
                st.session_state.chat_history.append(assistant_message)
            else:
                # If ai_response_object is None (due to an error in get_ai_response)
                error_message = "Sorry, I couldn't get a response from the AI. Please check the error messages above."
                st.markdown(error_message)
                st.session_state.chat_history.append({"role": "assistant", "content": error_message, "sources": []})
    
    # Rerun the app to update the chat display with the new messages
    st.rerun()
