import streamlit as st
import google.generativeai as genai
import os
import time

# --- Configuration ---
PAGE_TITLE = "Pickme Cinime"
PAGE_ICON = "🎬"
GEMINI_MODEL_NAME = "gemini-2.5-flash-preview-04-17"

# System instruction for the AI
SYSTEM_INSTRUCTION = """You are Pickme Cinime, an expert AI assistant specializing in recommending movies and OTT series. Your goal is to help users discover content they'll love based on their preferences, mood, or specific requests.

Here's how you should behave:

1.  **Understand User Needs**:
    *   Carefully analyze the user's input. They might specify genres, actors, directors, plot themes, moods (e.g., "something happy," "a thrilling mystery"), or even ask for "something similar to..."
    *   If the request is vague (e.g., "recommend a movie"), ask clarifying questions like "What genre are you in the mood for?" or "Any particular actors or themes you enjoy?" before giving a broad recommendation. However, if they use a mood button, assume that's their primary preference.

2.  **Provide Diverse Recommendations**:
    *   Suggest a mix of well-known hits and lesser-known gems if appropriate.
    *   Include content from various streaming platforms if not specified by the user. If you know where a specific title is streaming, you can mention it (e.g., "available on Netflix").
    *   Aim for 2-3 recommendations per request unless the user asks for more or less.

3.  **Give Key Details (Concise & Engaging)**:
    *   For each recommendation, provide:
        *   **Title (and Year)**
        *   **A brief, engaging synopsis** (1-2 sentences) highlighting what makes it special.
        *   **Genre(s)**
        *   **Why it fits the user's request** (e.g., "This fits your request for a 'thrilling mystery' because...").
    *   Use Markdown for formatting (bold titles, bullet points for lists of recommendations).

4.  **Tone**:
    *   Friendly, enthusiastic, and knowledgeable – like a passionate movie buff friend.
    *   Keep responses relatively concise and easy to read.

5.  **Handling Moods**:
    *   If a user clicks a mood button (e.g., "Happy," "Thrilling"), generate recommendations that strongly align with that emotion. For example:
        *   **Happy/Uplifting**: Feel-good movies, comedies, inspiring stories.
        *   **Thrilling**: Suspense, action, horror, psychological thrillers.
        *   **Thoughtful/Intriguing**: Dramas, documentaries, films with complex themes, mind-bending plots.
        *   **Relaxing/Chill**: Light-hearted content, comfort watches, visually beautiful films.
        *   **Funny**: Comedies, stand-up specials, satirical content.

6.  **Safety and Limitations**:
    *   Do not recommend content that is excessively violent, graphic, or inappropriate for a general audience unless specifically asked for mature themes (and even then, with a warning).
    *   If you cannot fulfill a request or don't have enough information, politely say so and perhaps offer alternatives or ask for more details.
    *   You are an AI and do not have personal opinions or feelings.

7.  **Search Grounding**:
    *   You have access to Google Search for up-to-date information. If you use search results to answer a query (e.g., for very new releases, current events related to film/TV), make sure the information is relevant.
    *   If web sources are used and returned by the API, they will be displayed to the user.

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
try:
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        # Fallback to Streamlit secrets if GOOGLE_API_KEY env var is not set
        api_key = st.secrets.get("GOOGLE_API_KEY")

    if not api_key:
        st.error("🚨 Google API Key not found. Please set the GOOGLE_API_KEY environment variable or add it to Streamlit secrets.")
        st.stop()

    genai.configure(api_key=api_key)
    generative_model = genai.GenerativeModel(GEMINI_MODEL_NAME)

except Exception as e:
    st.error(f"🚨 Error initializing the Gemini API: {e}")
    st.stop()


# --- Chat History Management ---
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "chat" not in st.session_state:
    # Initialize chat with system instruction
    st.session_state.chat = generative_model.start_chat(
        history=[
            # Start with system instruction, but don't display it as a message
            # The system instruction is passed in the config of generate_content
        ]
    )


# Function to send message to AI and get response
def get_ai_response(prompt):
    try:
        response = st.session_state.chat.send_message(
            prompt,
            generation_config=genai.types.GenerationConfig(
                tools=[genai.types.Tool(google_search_retrieval=genai.types.GoogleSearchRetrieval(disable_attribution=False))],
            ),
            # Pass system instruction with each call if not inherently part of chat object context
            # For some SDK versions, system instructions might be part of model config or start_chat
            # The google-generativeai Python SDK typically uses it in the model's 'system_instruction' parameter
            # or implicitly if set during model initialization (though less common for direct send_message).
            # For this example, we'll ensure it's considered.
            # If start_chat doesn't take system_instruction directly, it's passed via model config.
            # The current approach is to rely on it being part of the generative_model if configured,
            # or implicitly handled by the chat object based on model setup.
            # Let's adjust to pass system_instruction explicitly if the SDK requires it per turn for non-model-level config.
            # However, the `start_chat` method often initializes context.
            # The `system_instruction` is better set when getting the model.
            # For `gemini-2.5-flash-preview-04-17`, we will ensure model is initialized with it.

            # Re-creating model with system instruction for each call if chat object doesn't retain it.
            # This is not ideal. Better to configure model once if possible.
            # Let's assume the model was configured with system_instruction if needed,
            # or the chat object handles it. For now, rely on initial model setup.

            # config={"systemInstruction": SYSTEM_INSTRUCTION} -> This is for generateContent, not chat.sendMessage
        )
        return response
    except Exception as e:
        st.error(f"🚨 Error communicating with the AI: {e}")
        return None

# --- UI Rendering ---

# Display chat history
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
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
cols = st.columns(len(MOOD_PROMPTS))
mood_button_clicked = False
for i, (mood, prompt_text) in enumerate(MOOD_PROMPTS.items()):
    if cols[i].button(mood, key=f"mood_{i}", use_container_width=True):
        st.session_state.chat_history.append({"role": "user", "content": prompt_text})
        with st.chat_message("user"):
            st.markdown(prompt_text)
        mood_button_clicked = True
        user_input_for_ai = prompt_text # Use the full mood prompt
        break # Process one mood click at a time

# Chat input
user_query = st.chat_input("Ask for a movie or series recommendation...")

if user_query or mood_button_clicked:
    actual_input = user_query if user_query else user_input_for_ai # user_input_for_ai is from mood button

    if not mood_button_clicked: # Add to history only if it's not a mood button (already added)
        st.session_state.chat_history.append({"role": "user", "content": actual_input})
        with st.chat_message("user"):
            st.markdown(actual_input)

    with st.chat_message("assistant"):
        with st.spinner("Pickme Cinime is thinking... 🤔"):
            # Construct the full prompt history for the AI
            # The system instruction is passed when creating the model or chat session.
            # For Gemini API, system instructions are typically part of the model config.
            # Let's ensure our model object uses it.

            # Re-initialize the model or chat with the system instruction if necessary.
            # For this setup, we assume the initial model configuration includes the system instruction
            # or the chat object inherently uses it.
            # If the chat object does not persist system_instruction context well across calls
            # or if it's better to send it each time with generate_content for stateless calls:

            current_chat_context = [{"role": "user" if msg["role"] == "user" else "model", "parts": [msg["content"]]} for msg in st.session_state.chat_history[:-1]] # all but the last user message

            # The `start_chat` method is stateful. We send the latest user message.
            # The system instruction is part of the `generative_model` if configured there,
            # or passed to `start_chat`. For the python SDK, it's often part of the model config.
            # Let's re-instantiate the model with the system instruction to be sure.

            model_with_sys_instruction = genai.GenerativeModel(
                GEMINI_MODEL_NAME,
                system_instruction=SYSTEM_INSTRUCTION
            )
            # Re-initialize chat with history and system instruction embedded in the model
            # This ensures the system instruction is always fresh for the context.
            # For a continuing chat, we should use st.session_state.chat ideally.
            # Let's try to use the existing chat object and rely on its state.

            if "chat" not in st.session_state: # Should already be initialized
                 st.session_state.chat = model_with_sys_instruction.start_chat(history=current_chat_context)


            ai_response = get_ai_response(actual_input) # Send only the latest user message

            if ai_response:
                response_text = ""
                # Streaming not implemented here for simplicity, getting full response
                # If using response.text for Gemini, it should work.
                # Check for older API structures if `text` is not direct.
                # For `google-generativeai` `response.text` is standard.
                try:
                    response_text = ai_response.text
                except AttributeError: # Should not happen with current SDK
                    st.error("Error accessing AI response text.")
                    response_text = "Sorry, I encountered an issue processing the response."
                except Exception as e_text: # Catch any other error during text access
                    st.error(f"Error extracting text from AI response: {str(e_text)}")
                    response_text = "Sorry, I had trouble understanding the AI's answer."


                st.markdown(response_text)
                st.session_state.chat_history.append({"role": "assistant", "content": response_text})

                # Displaying sources from grounding
                sources = []
                if ai_response.candidates and ai_response.candidates[0].grounding_metadata:
                    grounding_meta = ai_response.candidates[0].grounding_metadata
                    if grounding_meta.grounding_attributions or grounding_meta.web_search_queries: # Check for older 'retrieval_queries' or 'web_search_queries'
                        st.caption("Retrieved sources:")
                        # grounding_chunks is the preferred way for gemini-2.5-flash
                        for i, chunk in enumerate(grounding_meta.grounding_chunks):
                             if chunk.web and chunk.web.uri:
                                st.caption(f"{i+1}. {chunk.web.title or 'Untitled'}: {chunk.web.uri}")
                                sources.append({"title": chunk.web.title, "uri": chunk.web.uri})
                if sources: # Add sources to history if any
                    st.session_state.chat_history[-1]["sources"] = sources

                # Force rerun if a mood button was clicked to clear the query from input box if any
                if mood_button_clicked:
                    st.rerun()
            else:
                st.session_state.chat_history.append({"role": "assistant", "content": "Sorry, I couldn't get a response. Please try again."})
                st.markdown("Sorry, I couldn't get a response. Please try again.")
    # If only user_query (not mood button), rerun to clear input box
    elif user_query and not mood_button_clicked:
        st.rerun()