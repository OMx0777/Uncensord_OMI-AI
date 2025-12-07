from interpreter import interpreter
import google_tool
import os
import sys

# --- CONFIG ---
interpreter.llm.api_base = "http://localhost:11434"
interpreter.llm.model = "ollama/OMI"
interpreter.llm.api_key = "fake-key"
interpreter.offline = True
interpreter.auto_run = True 

# --- MEMORY ---
try:
    with open("memory.md", "r") as f: mem = f.read()
except: mem = ""

interpreter.system_message = f"""
You are OMI. User: {os.getlogin()}. OS: Arch Linux.
Memory: {mem}

INSTRUCTIONS:
You are a summarizer and helper. 
If the user provides search results, summarize them clearly.
If the user asks for code, write it.
"""

print(f"  [OMI-AI Online] Mode: Middleware")
print("  (Type 'search <topic>' to browse the web, or just chat)\n")

# --- THE SMART LOOP ---
while True:
    try:
        user_input = input("(omi) > ")
        
        # 1. EXIT COMMAND
        if user_input.lower() in ['exit', 'quit']:
            break

        # 2. INTERCEPT SEARCH COMMANDS
        elif user_input.lower().startswith("search "):
            query = user_input[7:] 
            # Run the tool directly via Python (No AI involvement)
            search_data = google_tool.get_results(query)
            
            # Feed results to AI
            prompt = f"I searched for '{query}'. Here are the results:\n{search_data}\n\nPlease summarize these findings."
            interpreter.chat(prompt)
            
        # 3. NORMAL CHAT.
        else:
            interpreter.chat(user_input)
            
    except KeyboardInterrupt:
        print("\nUse 'exit' to quit.")
        continue
    except Exception as e:
        print(f"Error: {e}")
