"""
OMI AI Desktop App
------------------
"""

import streamlit as st
import ollama
import time

# --- CONFIGURATION & THEME ---
st.set_page_config(
    page_title="OMI AI",
    page_icon="🤖",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- CUSTOM CSS FOR RED/GREEN CHAT ---
# This forces the user input to be Green and AI response to be Red/Orange
st.markdown("""
<style>
    /* Dark Mode Background (Streamlit default is dark, but we enforce it) */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    
    /* USER MESSAGE (Green) */
    [data-testid="stChatMessage"]:nth-child(odd) {
        background-color: #1b3b24 !important; /* Dark Green background */
        border-left: 5px solid #00ff00;
    }
    
    /* AI RESPONSE (Red/Orange tint) */
    [data-testid="stChatMessage"]:nth-child(even) {
        background-color: #3b1b1b !important; /* Dark Red background */
        border-right: 5px solid #ff4b4b;
        color: #ffcccc !important; /* Light red text */
    }

    /* Input box styling */
    .stChatInput textarea {
        color: #00ff00 !important; /* Green typing text */
    }
</style>
""", unsafe_allow_html=True)

# --- APP TITLE ---
st.title("OMI - Arch Linux Assistant")
st.caption("Uncensored Local AI • Powered by Ollama")

# --- SESSION STATE (Memory) ---
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# --- SIDEBAR TOOLS ---
with st.sidebar:
    st.header("Tools")
    
    # SAVE CONVERSATION
    if st.button("💾 Save Chat to .txt"):
        chat_text = ""
        for msg in st.session_state.messages:
            role = "User" if msg["role"] == "user" else "OMI"
            chat_text += f"{role}: {msg['content']}\n\n"
        
        st.download_button(
            label="Download Now",
            data=chat_text,
            file_name=f"omi_chat_{int(time.time())}.txt",
            mime="text/plain"
        )
    
    # CLEAR CHAT
    if st.button("🗑️ Clear History"):
        st.session_state["messages"] = []
        st.rerun()

# --- DISPLAY CHAT HISTORY ---
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- CHAT INPUT & GENERATION ---
if prompt := st.chat_input("Type a message... (Cmd+V to paste)"):
    # 1. Show User Message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Generate AI Response
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_response = ""
        
        # Stream from Ollama
        try:
            stream = ollama.chat(
                model='OMI',  # Ensure you ran 'ollama create OMI' before!
                messages=st.session_state.messages,
                stream=True,
            )
            
            for chunk in stream:
                content = chunk['message']['content']
                full_response += content
                message_placeholder.markdown(full_response + "▌")
                
            message_placeholder.markdown(full_response)
        except Exception as e:
            st.error(f"Error: {e}. Is Ollama running?")

    # 3. Save AI Message to History
    st.session_state.messages.append({"role": "assistant", "content": full_response})